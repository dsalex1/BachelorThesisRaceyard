from statics import BLUE_CONE, YELLOW_CONE
from helpers import densify_path
import numpy as np
import math


def calc_amz_centerline(pointcloud, densify = True):
    """
        gets a list of cones with xyz and color and outputs a centerline
        returns a list of centerpoints
    """

    """ check colors of landmarks and sort them in corresponding lists """
    cone_blue = list()
    cone_yellow = list()

    for p in pointcloud:
        if(p[3] == BLUE_CONE):
            cone_blue.append(p[0:2])
        if(p[3] == YELLOW_CONE):
            cone_yellow.append(p[0:2])

    """ nparrays for better handling """
    cone_blue = np.asarray(cone_blue)
    cone_yellow = np.asarray(cone_yellow)

    center_line = list()

    """ determine if more yellow or blue cones are available """
    more_yellow = len(cone_blue) < len(cone_yellow)

    if more_yellow:
        for blue in cone_blue:
            """ find closest yellow cone by calculating all distances to
                current cone """
            def hypot(point):
                a = blue[0] - point[0]
                b = blue[1] - point[1]
                return math.sqrt(a**2. + b**2.)

            distances = np.array(list(map(hypot, cone_yellow)))
            """ find point with minimal distance """
            idx = np.where(distances == np.amin(distances))
            yellow = cone_yellow[idx]

            """ calc centerline point """
            p = np.array([0., 0., 0.])
            p[0:2] = (blue + yellow) / 2.0
            center_line.append(p.tolist())

    else:
        for yellow in cone_yellow:
            """ find closest blue cone by calculating all distances to
                current cone """
            def hypot(point):
                a = yellow[0] - point[0]
                b = yellow[1] - point[1]
                return math.sqrt(a**2. + b**2.)

            distances = np.array(list(map(hypot, cone_blue)))
            """ find point with minimal distance """
            idx = np.where(distances == np.amin(distances))
            blue = cone_blue[idx]

            """ calc centerline point """
            p = np.array([0., 0., 0.])
            p[0:2] = (yellow + blue) / 2.0
            center_line.append(p.tolist())

    """ densify the center line """
    if densify:
        return densify_path(center_line, 0.5)

    return center_line
