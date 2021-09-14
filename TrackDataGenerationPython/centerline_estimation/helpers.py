import math
from numpy import (array, dot, arccos, clip)
from numpy.linalg import norm
import numpy as np


def calc_distance(p0, p1):
    """ returns the distance between two points """
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    d = math.sqrt(dx**2 + dy**2)

    return d


def calc_midpoint(p0, p1):
    """ returns the midpoint between two points """
    return [(p1[0] + p0[0]) / 2., (p1[1] + p0[1]) / 2]


def calc_angle_points(p2, p1, p0):
    """ calculates the angle between the vectors (p1,p2) and (p0,p1) """
    u = [p2[0] - p1[0], p2[1] - p1[1]]
    v = [p1[0] - p0[0], p1[1] - p0[1]]

    return calc_angle_vectors(u, v)


def calc_angle_vectors(v, u):
    """ calculates angle between two vectors """
    c = dot(u,v)/norm(u)/norm(v)  # cosine of the angle
    return arccos(clip(c, -1, 1))  # angle [0, PI] with PI = forward


def calc_orientation(p2, p1, p0):
    """ find out, whether we are in a left or right turn:
         0 --> colinear
         1 --> clockwise (right)
        -1 --> coutnerclockwise (left)
    """
    val = (p1[1] - p2[1]) * (p0[0] - p1[0]) - (p1[0] - p2[0]) * (p0[1] - p1[1]);

    if val == 0:
        return 0
    return 1 if val > 0 else -1


def rotate_vector(v, r):
   """ rotates vector for angle r (in radians) """
   x = v[0] * math.cos(r) - v[1] * math.sin(r)
   y = v[0] * math.sin(r) + v[1] * math.cos(r)

   return [x,y]


def densify_path(path, precision):

    desified_path = list()
    desified_path.append(path[0])

    for idx, p in enumerate(path[1:]):

        idx += 1  # respect offset
        insert_points = list()

        """ calc distance between points """
        dx = p[0] - path[idx-1][0]
        dy = p[1] - path[idx-1][1]
        d = math.sqrt(dx**2 + dy**2)
        nm_add_points = int(d / precision)
        for j in range(nm_add_points):
            px = path[idx-1][0] + precision * j * dx / d
            py = path[idx-1][1] + precision * j * dy / d
            insert_points.append([px, py, 0.0])

        """ insert points at right position
            (Note: this is something the AMZ code does not do) """
        desified_path.extend(insert_points)

    """ append last point of original centerline since it gets ignored in for """
    desified_path.append(path[-1])

    return desified_path


def get_last_midpoint_as_pot_midpoint(midpoints):
    pos = midpoints[-1]
    orient = [1., 0]

    if len(midpoints) >= 2:
        x = midpoints[-1][0] - midpoints[-2][0]
        y = midpoints[-1][1] - midpoints[-2][1]

        v = [x, y]
        orient = v / norm(v)

    return [pos[0], pos[1], orient[0], orient[1]]


def path_is_valid(path, blue_cones, yellow_cones):
    """
        checks for each segment of the path, whether it intersects with
        the boundaries defined by the blue and yellow cones
    """

    """ TODO: check that start and end are valid """

    path = np.asarray(path)
    blue_cones = np.asarray(blue_cones)
    yellow_cones = np.asarray(yellow_cones)

    for idx, p in enumerate(path[1:]):
        v1 = [p[0:2], path[idx][0:2]]

        # check blue boundary
        for idx2, c in enumerate(blue_cones[1:]):
            # print("track:", idx, " blue:", idx2)
            v2 = [c, blue_cones[idx2]]
            if twoLinesIntersect(v1,v2):
                return False

        # check yellow boundary
        for idx2, c in enumerate(yellow_cones[1:]):
            # print("track:", idx, " yellow:", idx2)
            v2 = [c, yellow_cones[idx2]]
            if twoLinesIntersect(v1,v2):
                return False

    return True

def twoLinesIntersect(v1, v2):
    """
        v = [[x1,y1], [x2,y2]]

        from: https://stackoverflow.com/questions/3838329/how-can-i-check-if-two-segments-intersect
    """
    X1 = v1[0][0]
    X2 = v1[1][0]
    X3 = v2[0][0]
    X4 = v2[1][0]
    Y1 = v1[0][1]
    Y2 = v1[1][1]
    Y3 = v2[0][1]
    Y4 = v2[1][1]

    I1 = [min(X1,X2), max(X1,X2)]
    I2 = [min(X3,X4), max(X3,X4)]

    Ia = [max( min(X1,X2), min(X3,X4) ), min( max(X1,X2), max(X3,X4) )]

    if (max(X1,X2) < min(X3,X4)):
        return False  # There is no mutual abcisses

    A1 = (Y1-Y2)/(X1-X2)  # Pay attention to not dividing by zero
    A2 = (Y3-Y4)/(X3-X4)  # Pay attention to not dividing by zero
    b1 = Y1-A1*X1 # = Y2-A1*X2
    b2 = Y3-A2*X3 # = Y4-A2*X4

    if (A1 == A2):
        return False  # Parallel segments

    # Ya = A1 * Xa + b1
    # Ya = A2 * Xa + b2
    # A1 * Xa + b1 = A2 * Xa + b2
    Xa = (b2 - b1) / (A1 - A2)   # Once again, pay attention to not dividing by zero

    if ( (Xa < max( min(X1,X2), min(X3,X4) )) or (Xa > min( max(X1,X2), max(X3,X4) )) ):
        return False  # intersection is out of bound
    else:
        # print(v1, v2)
        return True
