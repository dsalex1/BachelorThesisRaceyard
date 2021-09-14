#!/usr/bin/env python
import math
import scipy.interpolate as si
from sklearn import svm
import numpy as np
from functools import reduce
import json, argparse
import random
from christofides import tsp
from statistics import median

def cones_to_xy(cones):
    """ Expands the cone objects list to x, y position of cones
        Args:
            cones (list): cones objects
        Returns:
            x (list): list of x parameter
            y (list): list of y parameter
    """
    x = []
    y = []
    for cone in cones:
        x.append(cone.position.x)
        y.append(cone.position.y)
    return x, y


def bind_xy(x, y):
    """ Binds the x,y values together to represent a geomertrical point
        Args:
            x (list): list of x parameter
            y (list): list of y parameter
        Returns:
            point (list): list of geometrical (x,y) points
    """
    point = []
    for i in range(len(x)):
        point.append([x[i], y[i]])
    return point


def distance(p1, p2):
    """ calculates the distance between two geometrical points
        Args:
            p1: point containing (x,y) coordinates of p1
            p2: point containing (x,y) coordinates of p2
        Returns:
            distance between p1 & p2
    """
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def getBSpline(ls):
    """ Interpolate the polynomial geometrical points list.
        Args:
            points (list): list of geometrical points(cones) location
        Returns:
            new_points (list): Interpolated/splined geometrical points list
    """
    n = len(ls) * 10
    degree = 2
    ls = np.asarray(ls)
    count = ls.shape[0]

    # Prevent degree from exceeding count-1, otherwise splev will crash
    degree = np.clip(degree, 1, count - 1)

    temp = []
    for l in range(count - degree + 1):
        temp.append(l)

    # Calculate knot vector
    kv = np.array([0] * degree + temp + [count - degree] * degree, dtype='int')

    # Calculate query range
    u = np.linspace(0, (count - degree), n)

    # Calculate result
    return np.array(si.splev(u, (kv, ls.T, degree))).T


def nearest(side2, n_side2, side1, x):
    """ Finds the nearest point in side2 from side1 point having index 'x'
        Args:
            side2 (list): list of geometrical points(cones) location
            n_side2: length of side2 list
            side1 (list): list of geometrical points(cones) location
            x: index value of point in side1
        Returns:
            mp: point containing (x,y) nearest to side1[x]
    """
    md = distance(side2[x % n_side2], side1[x])
    mp = side2[(x % n_side2)]

    for i in range(x + 1, n_side2):
        d = distance(side2[i % n_side2], side1[x])
        if d < md:
            md, mp = d, side2[i % n_side2]
    return mp


def expand_xy(points):
    """ Expands the x, y coordinates from the input list.
        Args:
            points (list): points containing list of x,y coordinates
        Returns:
            x (list): list of x coordinate
            y (list): list of y coordinate
    """
    x = []
    y = []
    for point in points:
        x.append(point[0])
        y.append(point[1])

    return x, y


def clasify_cones(X, y, TestSet):
    """ Classify the cones into two different list.
        Args:
            X (list): List of training sample to train svm model
            y (list): List of classes for training svm model
            TestSet (list): list of coordinates to classify
        Returns:
            C1 (list): classified list out of TestSet with class1
            C2 (list): classified list out of TestSet with class2
    """
    clf = svm.SVC(kernel='rbf', C=1E6, gamma='auto')
    poly = clf.fit(X, y)
    C1 = []
    C2 = []
    for point in TestSet:
        pred_y = clf.predict([point])
        if pred_y == [0]:
            C1.append(point)
        elif pred_y == [1]:
            C2.append(point)
    return C1, C2


# calculates centerline between two set of points
def get_centerline(side1, side2):
    """ Calculates the centerline between two lists of geometrical points(x,y).
        Args: 
            side1 (list): points containing list of x,y coordinates(cones)
            side2 (list): points containing list of x,y coordinates(cones)
        Returns:
            centerline (list): list of centerline points(x,y)
    """
    n_side1, n_side2 = len(side1), len(side2)
    p1 = []
    p2 = []
    if n_side1 < n_side2:
        p1 = side1
        nearest_p = []
        for j in range(n_side1):
            nearest_p.append(nearest(side2, n_side2, side1, j))
        p2 = nearest_p
    else:
        p2 = side2
        nearest_p = []
        for j in range(n_side2):
            nearest_p.append(nearest(side1, n_side1, side2, j))
        p1 = nearest_p

    return [(l[0] + r[0]) / 2 for l, r in zip(p1, p2)], [(l[1] + r[1]) / 2 for l, r in zip(p1, p2)]


def remove_dup(ls):
    """ Removes redundant(duplicate) data from a list.
        Args:
            ls (list): list of data
        Returns:
            new_list (list): List without redundant(duplicate) data
    """
    new_list = []
    for l in ls:
        if l not in new_list:
            new_list.append(l)
    return new_list


def get_sorted(ls):
    """ Sort the given coordinates list according to their spatial location
        and orient them clockwise(in some cases sorting make anti-clockwise orientation).
        Args:
            ls (list): list of coordinates
        Returns:
            new_list (list): List spatially ordered
    """

    # function to find the nearest point
    def nearestS(x, ls, O):
        min_d, min_p = 999999, None
        for p in ls:
            if p in O: continue
            d = distance(p, x)
            if d < min_d: min_d, min_p = d, p
        return min_p

    # function to order according to the nearest point
    def order(ls):
        ordered, p, c, n = [ls[0]], ls[0], 1, len(ls)
        while c < n:
            p = nearestS(p, ls, ordered)
            if p == None: break
            ordered.append(p);
            c += 1
        return ordered

    return order(ls)


# function to orient clockwise
def orient_clockwise(ls):
    """  orient the given list clockwise(in some cases sorting make anti-clockwise orientation).
        Args:
            ls (list): list of coordinates
        Returns:
            new_list (list): List spatially rotated
    """
    # ---> Note :
    if ls[1][0] < ls[0][0]:
        oriented = ls[1:]
        oriented.reverse()
        oriented = [ls[0]] + oriented
        return oriented
    return ls


def return_list(ls):
    """  Returns x, y coordinate in [x, y] format.
        Args:
            ls (list): list of only x, y coordinate
        Returns:
            ret (list): [x, y]
    """
    ret = []
    for l in ls:
        ret.append([l[0], l[1]])
    return ret

def sort_and_orientate(blue_cones,yellow_cones):
    #sort the points using an traveling salesperson approximation
    blue_cones = tsp(blue_cones)
    yellow_cones = tsp(yellow_cones)

    #the point in yellow_cones that ist closest to the 2nd (index 1) point in blue_cones likely coresponds to it
    yellowStart = yellow_cones.index(reduce(
        (lambda a, b: a if np.linalg.norm(np.subtract(a, blue_cones[1])) < np.linalg.norm(np.subtract(b, blue_cones[1])) else b),
        yellow_cones))

    # using this correspondence we can fix the orientation, going one index step further in yellow_cones this point should
    # correspond to the 3rd point in blue_cones, but if its closer to the 1st point, yellow_cones and blue_cones are likely
    # going in oposit directions, so we reverse yellow_corner and adjust the saved index yellowStart according to the reverse
    if (np.linalg.norm(np.subtract(yellow_cones[(yellowStart+1) % len(yellow_cones)], blue_cones[2])) >
        np.linalg.norm(np.subtract(yellow_cones[(yellowStart + 1) % len(yellow_cones)], blue_cones[0]))):
        yellow_cones = yellow_cones[::-1]
        yellowStart = len(yellow_cones)-yellowStart-1

    #now that the orientation is the same for both points, we can shift yellow_cones so that both lists start with nearby points
    yellow_cones = yellow_cones[yellowStart-1:] + yellow_cones[:yellowStart-1]

    return blue_cones,yellow_cones

def pre_process_cones(blue_cones, yellow_cones, noisy_cones):
    """ Pre-processing of cones having mis-identified color, redundant cones, unsorted order
        Args:
            blue_cones (list): list of x, y coordinates
            yellow_cones (list): list of x, y coordinates
            noisy_cones (list): list of x, y coordinates(coes having noisy color)
        Returns:
            blue_cones (list): list of x, y coordinates(after pre-processing)
            yellow_cones (list): list of x, y coordinates(after pre-processing)
    """
    # ---> Cone color classification
    X = blue_cones + yellow_cones

    test_set = blue_cones + yellow_cones + noisy_cones

    y_blue = []
    y_yellow = []
    for x in blue_cones:
        y_blue.append(0)
    for x in yellow_cones:
        y_yellow.append(1)

    y = y_blue + y_yellow

    #this classification does not currently work well
    #blue_cones, yellow_cones = clasify_cones(X, y, test_set)

    # ---> Remove duplicate cones from cones list
    blue_cones = remove_dup(blue_cones)
    yellow_cones = remove_dup(yellow_cones)

    # ---> Sorting the cones
    blue_cones,yellow_cones = sort_and_orientate(blue_cones,yellow_cones)


    def addMissing(group1, group2, width, spacing, fac):
        for i in range(1,len(group1)-1):
            if np.linalg.norm(np.subtract(group1[i], group1[i + 1])) > spacing * 2:
                continue
            if np.linalg.norm(np.subtract(group1[i], group1[i - 1])) > spacing * 2:
                continue

            n = np.add(np.subtract(group1[i], group1[i + 1]), np.subtract(group1[i - 1], group1[i])) #tangent vector to group1[i]
            n = np.divide([n[1],-n[0]],np.sqrt(np.sum(n**2))) # normalize and rotate by 90°, so we get the normal vector
            point = np.add(group1[i], np.multiply(n, width * fac)) # fac decides whether its the inner or outer normal vector

            #find the point in the other group thats closest, if its so close, we dont need the new point
            closest = reduce((lambda a,b: a if np.linalg.norm(np.subtract(a, point)) < np.linalg.norm(np.subtract(b, point)) else b), group2)

            if np.linalg.norm(np.subtract(point, closest)) > spacing * 0.5:
                group2.append(point.tolist())# otherwise append the new point

    def deriveSpacing(points):
        #distances between consecutive points
        #take the median as estimated for the generating distance
        return median([(np.linalg.norm(np.subtract(p, points[i + 1])) if points[i + 1] else 0) for i, p in enumerate(points[:-1])])

    def closest(points,p):
        return reduce((lambda a,b: a if np.linalg.norm(np.subtract(a, p)) < np.linalg.norm(np.subtract(b, p)) else b), points)

    def getSignedArea(points):
        signedArea = 0
        for i in range(len(points)):
            x1 = points[i][0]
            y1 = points[i][1]
            x2 = points[(i+1)%len(points)][0]
            y2 = points[(i+1)%len(points)][1]
            signedArea += (x1 * y2 - x2 * y1)
        return signedArea / 2

    derivedSpacingBlue = deriveSpacing(blue_cones)

    derivedSpacingYellow = deriveSpacing(yellow_cones)

    derivedWidth = median(
        [np.linalg.norm(np.subtract(p, closest(yellow_cones, p))) for p in blue_cones] +
        [np.linalg.norm(np.subtract(p, closest(blue_cones, p))) for p in yellow_cones])

    clockwise = getSignedArea(yellow_cones)>getSignedArea(blue_cones)

    addMissing(yellow_cones, blue_cones, derivedWidth, derivedSpacingYellow, 1 if clockwise else -1)

    addMissing(blue_cones, yellow_cones, derivedWidth, derivedSpacingBlue, -1 if clockwise else 1)

    blue_cones, yellow_cones = sort_and_orientate(blue_cones, yellow_cones)

    return blue_cones, yellow_cones


class CenterLineEstimation:
    def __init__(self):
        self.calc_once = True
        self.initial_lap = False

    def getMap(self):
        """
            Args:
            Returns:
                self.map: map object of this class
        """
        return self.map

    def mapCallback(self, slam_map):
        global args
        if self.calc_once:
            # print('Callback_Called')

            cone_blue = [[304.21,185.84],[351.19,243.15],[317.43,326.95],[242.02,339.94],[176.5,323.98],[141.02,240.94],[186.19,164.72],[257.54,146.9]]
            cone_yellow = [[269.83,230.04],[296.86,256.73],[288.62,278.93],[242.02,283.94],[201.54,273.9],[197.02,240.94],[205.85,217.16],[232.5,196.98]]
            faulty_cones = []

            parser = argparse.ArgumentParser()
            parser.add_argument('--cone_blue', '-b', help="the cone_blue data to use", type=str)
            parser.add_argument('--cone_yellow', '-y', help="the cone_yellow data to use", type=str)
            parser.add_argument('--faulty_cones', '-f', help="the faulty_cones data to use", type=str)
            if (args is None):
                args = parser.parse_args()

            if args.cone_blue is not None:
                cone_blue = json.loads(args.cone_blue)
            if args.cone_yellow is not None:
                cone_yellow = json.loads(args.cone_yellow)
            if args.faulty_cones is not None:
                faulty_cones = json.loads(args.faulty_cones)

            random.seed(42)

            random.shuffle(cone_blue)
            random.shuffle(cone_yellow)
            random.shuffle(faulty_cones)

            blue_x, blue_y = zip(*cone_blue)
            yellow_x, yellow_y = zip(*cone_yellow)
            faulty_x, faulty_y = zip(*faulty_cones) if len(faulty_cones)>0 else [[],[]]

            blue_cones = bind_xy(blue_x, blue_y)
            yellow_cones = bind_xy(yellow_x, yellow_y)
            f_cones = bind_xy(faulty_x, faulty_y)

            blue_cones = [[c[0]/500, c[1]/500] for c in blue_cones]
            yellow_cones =  [[c[0]/500, c[1]/500] for c in yellow_cones]
            f_cones =  [[c[0]/500, c[1]/500] for c in f_cones]

            # ---> Pre-processing cones data(cone color classification, removal of duplicate cones, spatial ordering)
            blue_cones, yellow_cones = pre_process_cones(blue_cones, yellow_cones, f_cones)

            blue_cones, yellow_cones = [[c[0] * 500, c[1] * 500] for c in blue_cones], [[c[0] * 500, c[1] * 500] for c
                                                                                        in yellow_cones]
            output = []
            output.append(blue_cones)
            output.append(yellow_cones)

            # ---> Join the ends of map(make circular) --pre-processing filters the duplicate cones
            if not self.initial_lap:
                blue_cones.append(blue_cones[0])
                yellow_cones.append(yellow_cones[0])

            # ---> Calculating the splined data for blue and
            #     yellow cones to get more accurate centerline
            blue_cones = getBSpline(blue_cones)
            yellow_cones = getBSpline(yellow_cones)



            '''
            blue_x, blue_y = expand_xy(blue_cones)
            yellow_x, yellow_y = expand_xy(yellow_cones)
            plt.plot(blue_x,blue_y, c='blue')
            plt.plot(yellow_x,yellow_y, c='yellow')
            '''

            # ---> calculating centerline
            midx, midy = get_centerline(blue_cones, yellow_cones)

            center_line = []
            # ---> Assigning calculated centerline points to map object
            for mx, my in zip(midx, midy):
                center_line.append([mx, my])

            # result:
            output.append(center_line)
            return output

if __name__ == "__main__":
    center_line_est = CenterLineEstimation()

    result = center_line_est.mapCallback(None)
    # try:
    #    while (True):
    #        maping = center_line_est.getMap()

    # except KeyboardInterrupt:
    #    print("shutdown")
