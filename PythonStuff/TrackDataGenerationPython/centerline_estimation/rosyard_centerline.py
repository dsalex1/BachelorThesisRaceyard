from helpers import calc_distance, calc_midpoint, calc_angle_vectors
from rosyard_cost_function import cost
from rosyard_astar import astar

import math
import numpy as np
import numpy.linalg as linalg

""" globals """
pot_centerpoints = list()

""" parameters """
max_dist = 8.
min_dist = 1.
max_search_distance = 8.


def get_potential_centerpoints():
    return pot_centerpoints

def reset():
    centerline = list()
    connected = None
    first_loop = True
    curr_point = None

def calc_potential_centerpoints(pointcloud, start_point, start_dir):
    """
        gets list of cones/landmarks as input and calculates all midpoint
        between two landmarks within a distance range """

    global max_dist, min_dist, pot_centerpoints

    pot_centerpoints = list()
    pot_centerpoints.append([start_point[0], start_point[1], start_dir[0], start_dir[1]])

    for idx, p0 in enumerate(pointcloud):
        """ check distance to any other cone """
        for p1 in pointcloud[idx:]:
            """ calc distance """
            d = calc_distance(p0, p1)

            if min_dist <= d and d <= max_dist:
                """ calc orientation (orthogonal to the vector between the points) """
                v = np.array([p1[1] - p0[1], p0[0] - p1[0]])
                v_hat = v / linalg.norm(v)

                """ calc midpoint """
                mp = calc_midpoint(p1, p0)

                """ potential centerpoint is point and orientation """
                pcp = [mp[0], mp[1], v_hat[0], v_hat[1]]

                pot_centerpoints.append(pcp)


    """ TODO bad that i do this here """
    global first_loop
    first_loop = True

    return pot_centerpoints



""" ... """
centerline = list()
connected = None
first_loop = True
curr_point = None

class CenterNode():
    def __init__(self, position, orientation, indx, connected, active1, active2):
        self.position = position
        self.orientation = orientation
        self.indx = indx
        # self.connected = connected
        self.predecessor_indx = -1
        self.active1 = active1  # potential points in direction of orientation
        self.active2 = active2  # potential points in direction of negative orientation


pot_center_nodes = list()


def calc_rosyard_centerline(all_in_one = True, manual_endpoint = None):
    """
        a greedy algorithm that takes the next best center_point according to the
        rosyward cost_function and supports back-tracking in cases, where no next point
        (best or otherwise) can be found

        Notes:
            we assume the first entry in pot_centerpoints is fixed for centerline

            a point in pot_centerpoints has [x,y,ox, oz] with x,y position and ox,oy orientation
    """

    global pot_centerpoints
    global max_search_distance




    global centerline, connected, curr_point, first_loop

    if first_loop:
        centerline = list()
        centerline.append(pot_centerpoints[0])

        """ Add last point """
        if manual_endpoint is None:
            pot_centerpoints.append(pot_centerpoints[0][:])
        else:
            pot_centerpoints.append(manual_endpoint)

        connected = np.zeros((len(pot_centerpoints)), dtype=bool) # which points have we already connected?
        connected[0] = True
        curr_point = pot_centerpoints[0]

        pot_center_nodes = list()
        for idx, p in enumerate(pot_centerpoints):
            pos = p[0:2]
            orient = p[2:4]

            node = CenterNode(pos, orient, idx, None, True, True)
            pot_center_nodes.append(node)




    """ add extra info to pot_centerpoints """
    if len(pot_centerpoints[0]) < 6:
        for idx, p in enumerate(pot_centerpoints):
            p.append(-1)    # Predecessor
            p.append(True)   # Node is active
            p.append(idx)    # own index

    # print("start rosyard centerline calc ...")

    def find_best_point():

        winner = None
        winner_idx = -1

        max_cost = 25    # > max_cost hardcoded omg
        best_cost = max_cost

        """ debug """
        pot_successors = 0
        pot_costs_string = "------------\n"

        """ best point is point within distance with minimal travel cost """
        for idx, p in enumerate(pot_centerpoints):
            """ check that point is not already taken
                (Note: we can connect to first point only if we are not currently on the first point) """
            if connected[idx]: # or (idx == 0 and first_loop):
                continue

            """ check that point was not already disregarded cause we did not find good sucessors from here """
            if p[5] == False:
                continue

            """ check distance distance """
            d = calc_distance(curr_point, p)
            if d > max_search_distance:
                continue

            """ check angle
                Note: we want to punish hard turns, so we calculate 2 angles
                    1) the angle between the current point orientation and the vector (v) to the target point
                       (the smaller this is, the less we have to turn to reach that point)
                    2) the angle between (v) and the target point orientation
                       (the smaller this is, the less we probably have to turn after reaching that point)
            """

            """ calculate first angle (Note: since this is the current point, it's orientation has been correctly set) """
            curr_orient = [curr_point[2], curr_point[3]]
            to_target = [p[0] - curr_point[0], p[1] - curr_point[1]]
            angle1 = calc_angle_vectors(curr_orient, to_target)

            """ calculate second angle (Note: the target point can be oriented in two ways (positive and negative, so we choose the smaller of the two angles)) """
            p_orient1 = [p[2], p[3]]
            p_orient2 = [p[2]*-1, p[3]*-1]

            pot_angle1 = calc_angle_vectors(to_target, p_orient1)
            pot_angle2 = calc_angle_vectors(to_target, p_orient2)
            angle2 = min(pot_angle1, pot_angle2)  # [0, 1/2 PI] with 0 completely aligned, 1/2 = 90 degrees

            """ Edge Case: start pos has correct orientation per definition """
            if idx == 0:
                angle2 = pot_angle1


            """ Calc cost """
            curr_cost = cost(d, angle1, angle2)

            if curr_cost < max_cost:
                max_cost = curr_cost
                winner = p
                winner_idx = idx
                best_angle = angle1 + angle2
                """ set orientation in case this point wins """
                if angle2 == pot_angle2:
                    p[2] *= -1
                    p[3] *= -1
                pot_successors += 1

                pot_costs_string += "pos: {:.1f},{:.1f} or: {:.1f},{:.1f} cost {:.1f} \n".format(float(p[0]),float(p[1]),float(p[2]),float(p[3]),curr_cost)

        """ set winner """
        if winner_idx > -1:
            connected[winner_idx] = True
            pot_centerpoints[winner_idx][4] = curr_point[6]
            # print("For " + str(curr_point[6]) + " the Winner is: " + str(winner_idx) + " (" + str(pot_successors) + " pot. successors)")
            curr_idx = winner_idx
        else:
            # print("Found no winner for " + str(curr_point[6]) + ". Switching back")
            curr_idx = curr_point[6]

        if not all_in_one:
            print(pot_costs_string)

        return winner


    """ Actual Algorithm """
    finished = False
    while len(pot_centerpoints) > 0 and not finished:
        first_loop = False
        winner = find_best_point()
        if winner is not None:
            centerline.append(winner)
            curr_point = winner

            """ termination condition """
            if winner[6] == len(pot_centerpoints) - 1:  # pot_centerpoints[0]:
                finished = True


        else:

            """ curr_point did not find a good node, so delete it from list """
            if curr_point[4] == -1:
                finished = True  # we were about to go back from the start point so give up
            else:
                # deactivate current point
                curr_point[5] = False
                # remove it from the center_line
                del centerline[-1]
                # go to predecessor
                idx = curr_point[4]
                curr_point = pot_centerpoints[idx]

        if not all_in_one:
            finished = True

    # if all_in_one:
        # print("... finished rosyard centerline calc")

    np_cl = np.array(centerline)

    # print(np.shape(np_cl))
    # print(centerline[0])

    return centerline, pot_centerpoints
