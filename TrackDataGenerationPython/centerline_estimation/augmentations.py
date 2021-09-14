from statics import BLUE_CONE, YELLOW_CONE, UNLABELED
from helpers import calc_angle_points, calc_orientation

import math
import numpy as np
import random

def cones2pointcloud(blues, yellows):
    """
        gets a list of blue and yellow cones (with x,y coordinates) and
        puts them in one list with (x,y,z, color), where color is a string

        Note: blues and yellows are expected to have the same length, but the
        function still works, if not
    """

    pointcloud = list()

    num_cones = min(len(blues), len(yellows))
    for (b, y) in zip(blues[:num_cones], yellows[:num_cones]):
        """ add blue and yellow """
        pointcloud.append([b[0], b[1], 0.0, BLUE_CONE])
        pointcloud.append([y[0], y[1], 0.0, YELLOW_CONE])

    """ TODO: deal with overlength """
    if (len(blues) > num_cones):
        print("We got more blue cones then yellow cones")
        for b in blues[num_cones:]:
            pointcloud.append([b[0], b[1], 0.0, BLUE_CONE])
    if (len(yellows) > num_cones):
        print("We got more yellow cones then blue cones")
        for y in yellows[num_cones:]:
            pointcloud.append([y[0], y[1], 0.0, YELLOW_CONE])


    return pointcloud


def unsee_corner_cones(pointcloud, angle_thres):
    """
        unsees cones at the inside of turns with 1. prob if their
        angle to the predecessing cone is >= max_angles and prob 0.
        if their angle is <= min angle. Inbetween the probabilityis
        interpolated

        (Note: this function requires the color data and the position
        of each cone, so it should be called first)
    """

    blue_cone1 = None # last seen blue cone
    blue_cone2 = None # second to last seen blue cone

    yellow_cone1 = None  # last seen yellow cone
    yellow_cone2 = None  # second to last seen yellow cone

    new_pointcloud = list()

    for p in pointcloud:
        if p[3] == BLUE_CONE:

            survives = True

            if blue_cone1 is not None and blue_cone2 is not None:
                angle = calc_angle_points(blue_cone2[:2], blue_cone1[:2], p[:2])
                orient = calc_orientation(blue_cone2[:2], blue_cone1[:2], p[:2])
                """ we care for left turns """
                if orient == -1 and angle > angle_thres:
                    survives = False

            blue_cone2 = blue_cone1
            blue_cone1 = p
            if survives:
                new_pointcloud.append(p)

        elif p[3] == YELLOW_CONE:
            survives = True

            if yellow_cone1 is not None and yellow_cone2 is not None:
                angle = calc_angle_points(yellow_cone2[:2], yellow_cone1[:2], p[:2])
                orient = calc_orientation(yellow_cone2[:2], yellow_cone1[:2], p[:2])
                """ we care for right turns """
                if orient == 1 and angle > angle_thres:
                    survives = False

            yellow_cone2 = yellow_cone1
            yellow_cone1 = p
            if survives:
                new_pointcloud.append(p)

    return new_pointcloud



def unsee_cone(pointcloud, prob):
    """
        randomly deletes cones from pointcloud
    """

    for p in pointcloud:
        if random.random() <= prob:
            pointcloud.remove(p)

    return pointcloud


def unlabel_cone(pointcloud, prob):
    """
        randomly labels cones as unlabeled
    """

    for p in pointcloud:
        if random.random() <= prob:
            p[3] = UNLABELED

    return pointcloud

def mislabel_cone(pointcloud, prob_b2y, prob_y2b):
    """
        randomly misclassifies cone as wrong color
    """

    for p in pointcloud:
        if p[3] == BLUE_CONE and random.random() <= prob_b2y:
            p[3] = YELLOW_CONE
        elif p[3] == YELLOW_CONE and random.random() <= prob_y2b:
            p[3] = BLUE_CONE

    return pointcloud


def cone_pos_noise(pointcloud, sigma):
    """
        adds gaussian noise to position
    """

    for p in pointcloud:
        """ generate random angle and distance """
        alpha = 2 * math.pi * random.random()
        dist = np.random.normal(0, sigma, 1)[0]
        """ apply noise """
        p[0] += dist * math.cos(alpha)
        p[1] += dist * math.sin(alpha)

    return pointcloud


def hallucinate_cones(pointcloud, area_extension, percentage_halluc, prob_yellow, prob_blue):
    """
        hallucinates cones in random positions in an area inside the track
    """
    if len(pointcloud) < 2:
        return pointcloud

    x_min = pointcloud[0][0]
    x_max = pointcloud[0][0]
    y_min = pointcloud[0][1]
    y_max = pointcloud[0][1]

    """ get area of track """
    for p in pointcloud[1:]:
        x_min = min(x_min, p[0])
        x_max = max(x_max, p[0])
        y_min = min(y_min, p[1])
        y_max = max(y_max, p[1])

    """ extend area """
    width = x_max - x_min
    height = y_max - y_min

    x_min -= width * area_extension / 2.
    x_max -= width * area_extension / 2.
    y_min -= height * area_extension / 2.
    y_max -= height * area_extension / 2.

    """ hallucinate cones """
    num_hallucs = int(len(pointcloud) * percentage_halluc)

    for _ in range(num_hallucs):
        """ randomize position """
        x = random.uniform(x_min, x_max)
        y = random.uniform(y_min, y_max)

        """ randomize color """
        c = random.random()
        cone_color = UNLABELED
        if c < prob_blue:
            cone_color = BLUE_CONE
        elif c < prob_blue + prob_yellow:
            cone_color = YELLOW_CONE

        """ insert at random position """
        idx = random.randrange(0, len(pointcloud))
        pointcloud.insert(idx, [x, y, 0.0, cone_color])

    return pointcloud

def randomize_list(pointcloud):
    random.shuffle(pointcloud)
    return pointcloud
