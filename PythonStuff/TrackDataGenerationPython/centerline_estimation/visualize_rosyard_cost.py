from rosyard_cost_function import cost
from helpers import calc_distance, calc_angle_vectors
import matplotlib.pyplot as plt
import numpy as np
import math


fig = plt.figure()
ax = fig.gca()

def draw_costmap(start_orient = [0, 1], target_orient = [0, 1]):
    """
        params:
            start_orient: (...) (first is y, second is x)
    """

    print("start drawing map ...")

    """ prepare plot """
    plt.cla()

    # 25m x 25m in 0.1m steps
    size_x = 100
    size_y = 100
    step_size = 0.25

    max_cost = 25

    cost_map = np.zeros((size_x,size_y), np.float)
    start_point = [(cost_map.shape[0] / 2.) - 0.5,
                   (cost_map.shape[1] / 2.) - 0.5]  # center of map

    """ debug """
    to_target_map = np.zeros((size_x, size_y, 2), np.float)
    angles_map = np.zeros((size_x, size_y), np.float)

    """ calculate cost for each point """
    """ map would be nicer but i don't know how to access the indx that way """
    for x in range(0, cost_map.shape[0]):
        for y in range(0, cost_map.shape[1]):

            """ calc cost parameters """
            dist = calc_distance([x, y], start_point) * step_size

            to_target = [x - start_point[0], y - start_point[1]]
            angle1 = 0
            if abs(to_target[0]) > 0.01 or abs(to_target[1]) > 0.01:
                angle1 = calc_angle_vectors(start_orient, to_target)

            angles_map[x,y] = angle1
            to_target_map[x,y] = [x - start_point[0], y - start_point[1]]

            """ todo: set per interface or whatever """
            angle2 = 0
            if abs(to_target[0]) > 0.01 or abs(to_target[1]) > 0.01:
                angle2 = calc_angle_vectors(to_target, target_orient)

            """ calc cost """
            cost_map[x, y] = min(cost(dist, angle1, angle2), max_cost)



    """ reference point (so that heatmap doesnt get black if all have max cost)"""
    cost_map[int(start_point[0]), int(start_point[1])] = 0

    # print(start_orient)
    # print(target_orient)

    """ set axis the way pyplot wants it """
    plot_map = np.swapaxes(cost_map,0,1)
    plot_map = np.flip(plot_map, 0)

    """ draw cost map """
    plt.grid()
    plt.imshow(plot_map, cmap='hot', interpolation='nearest')
    """ calc directions """
    blue_dir = [start_point[0] + start_orient[0] * 8, -start_point[1] + start_orient[1] * 8]
    green_dir = [start_point[0] + target_orient[0] * 5, -start_point[1] + target_orient[1] * 5]

    ax.plot([start_point[0], blue_dir[0]], [start_point[1], -blue_dir[1]], linewidth = 1, c="b")
    ax.plot([start_point[0], green_dir[0]], [start_point[1], -green_dir[1]], linewidth = 1, c="g")

    fig.canvas.draw()
    print("... finished drawing map")


glob_start_rot = 0  # [0, 360)
glob_target_rot = 0  # [0, 360)



def press(event):

    global glob_start_rot
    global glob_target_rot
    step = 22.5

    if event.key == 'left':
        glob_start_rot = (glob_start_rot - step) % 360

    if event.key == 'right':
        glob_start_rot = (glob_start_rot + step) % 360

    if event.key == 'a':
        glob_target_rot = (glob_target_rot - step) % 360

    if event.key == 'd':
        glob_target_rot = (glob_target_rot + step) % 360


    # x' = x cos d - y sin d
    # y' = x sind d + y cos d
    start_orient =  [math.sin(glob_start_rot  * 3.14 / 180. ),
                   math.cos(glob_start_rot * 3.14 / 180. )]
    target_orient = [math.sin(glob_target_rot  * 3.14 / 180. ),
                     math.cos(glob_target_rot * 3.14 / 180. )]

    draw_costmap(start_orient=start_orient, target_orient=target_orient)




if __name__== "__main__":

    # global glob_car_orient
    # global glob_cone_orient

    draw_costmap([0, 1], [0, 1])
    fig.canvas.mpl_connect('key_press_event', press)
    plt.show()
