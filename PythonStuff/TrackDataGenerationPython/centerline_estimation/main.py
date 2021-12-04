from statics import BLUE_CONE, YELLOW_CONE
from augmentations import (cones2pointcloud,
                           unsee_corner_cones,
                           cone_pos_noise,
                           unsee_cone,
                           unlabel_cone,
                           mislabel_cone,
                           hallucinate_cones,
                           randomize_list)
# centerline estimators
from amz_centerline import calc_amz_centerline
from rosyard_centerline import calc_potential_centerpoints, calc_rosyard_centerline, get_potential_centerpoints, reset
from rosyard_astar import calc_rosyard_astar
from rosyard_graph_centerline import find_path
from path_metric import path_error, calc_path_length
from helpers import get_last_midpoint_as_pot_midpoint, path_is_valid

# racing line estimators
from rosyard_racingline import create_racingline_candidates, find_racingline

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import yaml
import numpy as np

""" matplotlib stuff """
fig = plt.figure(figsize=(12,12))
ax  = fig.add_axes([0.05,0.05,0.9,0.9])
ax.set_aspect(1.0)

""" globals """
blues = np.array([[0,0], [0,1], [0,2]])
yellow = np.array([[1,0], [1,1], [1,2]])
midpoints = np.array([])
pc = list()

""" yaml paths and keys """
yaml_path = "tracks/track_1.yaml"
# yaml_path = "generated_tracks/random_track_048.yaml"
track_loops = True
BLUE_CONES = "cones_left"
YELLOW_CONES = "cones_right"
CENTER_LINE = "middle_points"

""" augmentation variables """
aug_angle_not_seen = 0.2
aug_not_seen = 0.1  # chance of a cone not being seen
aug_no_color = 0.5  # chance of not labeling cone at all
aug_misclass_b2y, aug_misclass_y2b  = 0.1, 0.1  # chance of labeling blue as yellow, chance of labeling yellow as blue
# area extension in which we hallucinate cones, percentage of hallucinated cones, prob of these cones beeing blue and yellow
aug_area_ext, aug_perc_halluc, aug_prob_halluc_yellow, aug_prob_halluc_blue = 0.2, 0.15, 0.05, 0.05
aug_position_sigma = .5  # standard deviation for xy pos

def load_track(path):
    with open(path) as file:
        data = yaml.load(file, Loader=yaml.FullLoader)

    blue_cones = data[BLUE_CONES] if BLUE_CONES in data else None
    yellow_cones = data[YELLOW_CONES] if YELLOW_CONES in data else None
    center_points = data[CENTER_LINE] if CENTER_LINE in data else None

    """ Debug Messages """
    def debug_msg(val, str):
        if val is None:
            print("Load Warning: Key '" + str + "' returns None")
        elif len(val) == 0:
            print("Load Warning: Key '" + str + "' is empty")

    debug_msg(blue_cones, BLUE_CONES)
    debug_msg(yellow_cones, YELLOW_CONES)
    debug_msg(center_points, CENTER_LINE)

    return blue_cones, yellow_cones, center_points


def draw_track(fig, ax, gt_l_cones = None, gt_r_cones = None, gt_midpoints = None, pred_midpoints = None, pointcloud = None):
    """ prepare plot """
    plt.cla()

    """ draw gt cones """
    if gt_l_cones is not None:
        ax.scatter(gt_l_cones[:,0], gt_l_cones[:,1], c="b")
    if gt_r_cones is not None:
        ax.scatter(gt_r_cones[:,0], gt_r_cones[:,1], c="y")

    """ draw poinctcloud as perceivied cones """
    if pointcloud is not None:
        bs = list()
        ys = list()
        us = list()  # unlabeled
        for p in pointcloud:
            if p[3] == BLUE_CONE:
                bs.append(p[:2])
            elif p[3] == YELLOW_CONE:
                ys.append(p[:2])
            else:
                us.append(p[:2])
        bs = np.asarray(bs, np.float32)
        ys = np.asarray(ys, np.float32)
        us = np.asarray(us, np.float32)

        if(bs.size > 0):
            ax.scatter(bs[:,0], bs[:,1], c="b", marker="s")
        if(ys.size > 0):
            ax.scatter(ys[:,0], ys[:,1], c="y", marker="s")
        if(us.size > 0):
            ax.scatter(us[:,0], us[:,1], c=('0.5', '0.5', '0.5'), marker="s")

    """ draw gt center line """
    if  gt_midpoints is not None and gt_midpoints.size > 1:
        # ax.scatter(midpoints[:,0], midpoints[:,1], c="r", marker="x")
        plt.plot(gt_midpoints[:,0], gt_midpoints[:,1], linewidth=1, c="r")

    """ draw predicted center line """
    if  pred_midpoints is not None and pred_midpoints.size > 1:
        ax.scatter(pred_midpoints[:,0], pred_midpoints[:,1], c="g", marker=".")
        # plt.plot(pred_midpoints[:,0], pred_midpoints[:,1], linewidth=1, c="r")

        """ if possible, draw orientation """
        if pred_midpoints[0].size >= 4:
            for p in pred_midpoints:
                ln = 1.  # len of line in both directions
                start_x = p[0] - p[2] * ln
                start_y = p[1] - p[3] * ln
                end_x = p[0] + p[2] * ln
                end_y = p[1] + p[3] * ln
                if pred_midpoints[0].size >= 6 and p[5] is False:
                    ax.plot([start_x, end_x], [start_y, end_y], linewidth = 1, c=(0., 0., 0.))
                else:
                    ax.plot([start_x, end_x], [start_y, end_y], linewidth = 1, c="g")

    fig.canvas.draw()

    ax.set_aspect(1.0)


def pc_augm(blues, yellows):
    pc = cones2pointcloud(blues, yellows)

    """ augmentations / noise """
    # pc = unsee_corner_cones(pc, aug_angle_not_seen)
    pc = unsee_cone(pc, aug_not_seen)
    pc = unlabel_cone(pc, aug_no_color)
    pc = mislabel_cone(pc, aug_misclass_b2y, aug_misclass_y2b)
    pc = cone_pos_noise(pc, aug_position_sigma)
    pc = hallucinate_cones(pc, 0.2, 0.15, 0.05, 0.05)
    pc = randomize_list(pc)

    return pc


def press(event):
    """ Changes what is drawn """

    global pc

    if event.key == 'w':
        pc = pc_augm(blues, yellows)
        ryrd_pt = calc_potential_centerpoints(pc, [0., 0.], [1.0, 0.])

        draw_track(fig, ax, None, None, None, None, np.asarray(pc))  # est cones

    if event.key == 'r':
        reset()
        ryrd_pt = calc_potential_centerpoints(pc, [0., 0.], [1.0, 0.])

    if event.key == '1':
        print("Print GT centerline")
        # draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(centerline))
        draw_track(fig, ax, None, None, np.asarray(centerline), None, np.asarray(pc))

    if event.key == '2':
        print("Print AMZ centerline")

        amz_cl = calc_amz_centerline(pc)
        draw_track(fig, ax, None, None, np.asarray(amz_cl), None, np.asarray(pc))

        # print("Path Error: " + str(path_error(centerline, amz_cl)))
        print("Undensed Path Error: " + str(path_error(centerline, amz_cl, False)))

    if event.key == '3':
        print("Print Rosyard greedy centerline")

        """ rosyard centerline """
        ryrd_pt = calc_potential_centerpoints(pc, centerline[0], [1.0, 0.]) if centerline is not None else calc_potential_centerpoints(pc, [0, 0], [1.0, 0.])

        if track_loops:
            ryrd_cl, ryrd_pt = calc_rosyard_centerline(True, None)
        else:
            ryrd_cl, ryrd_pt = calc_rosyard_centerline(True, get_last_midpoint_as_pot_midpoint(centerline))

        # draw_track(fig, ax, None, None, np.asarray(ryrd_cl), None, np.asarray(pc))  # est cones
        # draw_track(fig, ax, None, None, np.asarray(ryrd_cl), np.asarray(ryrd_pt), np.asarray(pc))  # est cones and midpoints
        draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(ryrd_cl), None, None)  # gt cones

        # print("Is Path valid? " + str(path_is_valid(ryrd_cl, blues, yellows)))

        # print("Path Error: " + str(path_error(centerline, ryrd_cl)))
        # print("Undensed Path Error: " + str(path_error(centerline, ryrd_cl, False)))

        # print("Path length: " + str(calc_path_length(centerline)))

    if event.key == 'down':
        ryrd_pt = get_potential_centerpoints()
        ryrd_cl, ryrd_pt = calc_rosyard_centerline(False)
        # draw_track(fig, ax, None, None, np.asarray(ryrd_cl), np.asarray(ryrd_pt), np.asarray(pc))  # pot midpoints
        draw_track(fig, ax, None, None, np.asarray(ryrd_cl), None, np.asarray(pc))  # pot midpoints

    if event.key == '4':
        print("Print Rosyard graph centerline")
        ryrd_pt = get_potential_centerpoints()
        if track_loops:
            ryrd_cl = find_path(ryrd_pt, None)
        else:
            ryrd_cl = find_path(ryrd_pt, get_last_midpoint_as_pot_midpoint(centerline))

            print(get_last_midpoint_as_pot_midpoint(centerline))



        draw_track(fig, ax, None, None, np.asarray(ryrd_cl), None, np.asarray(pc))  # est cones
        # draw_track(fig, ax, None, None, np.asarray(ryrd_cl), np.asarray(ryrd_pt), np.asarray(pc))  # est cones and midpoints
        # draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(ryrd_cl), np.asarray(ryrd_pt), None)  # gt cones

        # print("Path Error: " + str(path_error(centerline, ryrd_cl)))
        print("Undensed Path Error: " + str(path_error(centerline, ryrd_cl, False)))



    if event.key == '5':
        print("Print Rosyard racing line")
        cand_pit = create_racingline_candidates(centerline, 7)
        rl = find_racingline(cand_pit)

        # bring the candidate list in the right shape for plotting
        plot_cand = np.asarray(cand_pit)
        plot_cand = plot_cand.reshape(-1,4)

        draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(rl), None, None)  # gt cones
        # draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(rl), np.asarray(plot_cand), None)  # est cones and midpoints


    if event.key == 'down' and False:
        print("Print Rosyard astar")

        pc = pc_augm(blues, yellows)


        """ rosyard centerline """
        ryrd_pt = calc_potential_centerpoints(pc, [0., 0.], [1.0, 0.])
        calc_rosyard_astar(ryrd_pt)




def main():
    global blues, yellows, centerline, pc
    blues, yellows, centerline = load_track(yaml_path)
    pc = pc_augm(blues, yellows)

    draw_track(fig, ax, np.asarray(blues), np.asarray(yellows), np.asarray(centerline))
    fig.canvas.mpl_connect('key_press_event', press)
    plt.show()



if __name__== "__main__":
    print("started")
    main()
    print("finished")
