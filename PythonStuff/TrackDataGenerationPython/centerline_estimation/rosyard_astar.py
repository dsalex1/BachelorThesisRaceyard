""" modified from: https://medium.com/@nicholas.w.swift/easy-a-star-pathfinding-7e6689c7f7b2 """

from helpers import calc_distance, calc_angle_vectors
from rosyard_cost_function import cost




def calc_rosyard_astar(pot_centerpoints):
    print("start astar ...")
    astar(pot_centerpoints, [0,0], [0,0])
    print("... finished astar")


def find_close_points(curr_node, pot_centerpoints, min_dist, max_dist):
    """
        returns list of neighbouring nodes

    """
    neighbours = list()
    for idx, p in enumerate(pot_centerpoints):
        """ calc distance """
        d = calc_distance(curr_node[0:2], p)

        if min_dist < d and d < max_dist:
            neighbours.append(p)

    return neighbours



def calc_cost(curr_point, target_point):
    """
        calculate cost for reaching the target point from current point

        a point is [x,y,ox,oy] with x,y position and ox, oy orientation
    """

    p = target_point

    """ check distance """
    d = calc_distance(curr_point, p)

    """ check angle """
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

    """ calcualte cost """
    return cost(d, angle1, angle2)


class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None, orientation=None):
        self.parent = parent
        self.position = position
        self.orientation = orientation

        self.g = 0
        self.h = 0
        self.f = 0

        # self.idx = idx  # index in potential_centerpoints list

    def __eq__(self, other):
        return self.position == other.position


def astar(midpoints, start, end):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node = Node(None, start, [1,0])
    start_node.g = start_node.h = start_node.f = 0

    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:

        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        """ TODO: define this """
        # Found the goal
        # if current_node == end_node:
        #     path = []
        #     current = current_node
        #     while current is not None:
        #         path.append(current.position)
        #        current = current.parent
        #    return path[::-1] # Return reversed path

        # find potentital successors

        children = list()
        """ TODO: don't hardcode search parameters """
        close_points = find_close_points(current_node.position, midpoints, 1., 15.)

        # Create nodes from children
        for cp in close_points:
            node_position = (cp[0], cp[1])
            node_orient = (cp[2], cp[3])

            # Create new node
            new_node = Node(current_node, node_position, node_orient)

            # Append
            children.append(new_node)


        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            # child.g = current_node.g + 1
            # child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            travel_cost = calc_cost([current_node.position[0], current_node.position[1], current_node.orientation[0], current_node.orientation[1]],
                                    [child.position[0], child.position[1], child.orientation[0], child.orientation[1]])
            """ dont hardcode this parameter """
            if travel_cost > 15:
                continue

            travel_dist = calc_distance(current_node.position, child.position)

            child.g = travel_cost
            """ dont hardcode this parameter """
            child.h = 1000 - (current_node.g + travel_dist)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)
