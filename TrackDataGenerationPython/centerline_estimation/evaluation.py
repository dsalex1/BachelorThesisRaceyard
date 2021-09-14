from rosyard_centerline import calc_potential_centerpoints, calc_rosyard_centerline, get_potential_centerpoints, reset
from rosyard_graph_centerline import find_path
from path_metric import path_error, distance_ratio
from helpers import get_last_midpoint_as_pot_midpoint, path_is_valid
import random
import numpy as np

from main import load_track, pc_augm

import glob
import os

yaml_paths = glob.glob(os.path.join(os.getcwd(), "generated_tracks/random_track_???.yaml"))
yaml_paths.sort()
# yaml_paths = ["generated_tracks/random_track_005.yaml"]
runs_per_track = 1

def main():

    for trackNr, yaml_path in enumerate(yaml_paths):
        global runs_per_track
        random.seed(0)

        blues, yellows, centerline = load_track(yaml_path)

        greed_error = np.zeros((runs_per_track))
        greed_dist_ratios = np.zeros((runs_per_track))
        greed_valid = np.chararray((runs_per_track))
        greed_valid[:] = "x"

        graph_error = np.zeros((runs_per_track))
        graph_dist_ratios = np.zeros((runs_per_track))
        graph_valid = np.chararray((runs_per_track))
        graph_valid[:] = "x"

        for i in range(runs_per_track):
        # for i in range(0):
            """ new augmentation """
            pc = pc_augm(blues, yellows)

            """ greedy """
            ryrd_pt = calc_potential_centerpoints(pc, centerline[0], [1.0, 0.])
            ryrd_cl, ryrd_pt = calc_rosyard_centerline(True, get_last_midpoint_as_pot_midpoint(centerline))

            greed_error[i] = path_error(centerline, ryrd_cl)
            greed_dist_ratios[i] = distance_ratio(ryrd_cl, centerline)
            if path_is_valid(ryrd_cl, blues, yellows):
                greed_valid[i] = "o"

            """ graph """
            ryrd_pt = get_potential_centerpoints()
            ryrd_cl = find_path(ryrd_pt, get_last_midpoint_as_pot_midpoint(centerline))

            graph_error[i] = path_error(centerline, ryrd_cl)
            graph_dist_ratios[i] = distance_ratio(ryrd_cl, centerline)
            if path_is_valid(ryrd_cl, blues, yellows):
                graph_valid[i] = "o"


        s = "Track {:03d} | ".format(trackNr)
        s += "er: "
        for i in range(runs_per_track):
            # s += "  {:05.2f}".format(min(greed_error[i], 99.99))
            # s += " ({:04.2f})".format(min(greed_dist_ratios[i], 9.99))
            s += " " + str(greed_valid[i])
        s += " | avg: {:05.2f} |".format(min(np.average(greed_error), 99.99))
        s += "| "
        s += "er: "
        for i in range(runs_per_track):
            # s += "  {:05.2f}".format(min(graph_error[i], 99.99))
            # s += " ({:04.2f})".format(min(graph_dist_ratios[i], 9.99))
            s += " " + str(graph_valid[i])
        s += " | avg: {:05.2f} |".format(min(np.average(graph_error), 99.99))

        print(s)

if __name__== "__main__":
    print("started Evaluation ...")
    main()
    print("... finished Evaluation")
