from helpers import calc_distance, calc_angle_vectors
from rosyard_cost_function import cost

import numpy as np


class RosyNode:
    """ TODO: different classes for the two lists (i.e. Nodes and unvisited_Nodes)"""
    def __init__(self, pos, orient, indx, pindx):

        self.pos = pos
        self.orient = orient

        self.list_indx = indx  # index in the all nodes list (i.e. not the unvisited Nodes list)
        self.point_indx = pindx  # to identify the corresponding point in the midpoint_cloud
        self.visited = False
        self.travel_cost = float("inf")


def find_succeeding_nodes(curr_node, unvisited_Nodes, cost_thrsh, min_search_distance = 0.5, max_search_distance = 8.):
    """
        find potential succeeding nodes for current node and returns:
            - their index in the unvisited_Nodes list
            - the travel_cost to reach them
    """

    pred_Nodes_idxs = list()
    costs = list()

    for idx, n in enumerate(unvisited_Nodes):
        # check distance
        dist = calc_distance(curr_node.pos, n.pos)
        if min_search_distance > dist or dist > max_search_distance:
            continue

        # check angles
        to_target = curr_node.pos - n.pos
        angle1 = calc_angle_vectors(curr_node.orient, to_target)
        angle2 = calc_angle_vectors(to_target, n.orient)

        # calculate cost
        own_cost = cost(dist, angle1, angle2)
        this_cost = curr_node.travel_cost + own_cost

        if own_cost < cost_thrsh:
            pred_Nodes_idxs.append(idx)

            """ TODO: this is unconventional """
            costs.append(own_cost)
            """ this would be right but sometimes leads to worse results """
            # costs.append(this_cost)

    return pred_Nodes_idxs, costs


def find_path(midpoints, manual_endpoint = None):
    """
        Takes the potential centerpoints and technically* builds a graph where
        nodes are centerpoints and edges are the travel cost defined by
        the rosyard rosyard_cost_function

        * we only have the nodes and calculate the edges when needes


        Then throws the Dijkstra's algorithm on it

        Then builds the centerline and returns it
    """


    """ 1) Create Nodes and unvisited_Nodes from centerpoints """
    Nodes = list()  # list of all Nodes; Only need this for the centerline position

    # add first point
    start_pos = np.array([midpoints[0][0], midpoints[0][1]])
    start_orient = np.array([midpoints[0][2], midpoints[0][3]])
    Nodes.append(RosyNode(start_pos, start_orient, len(Nodes), 0))
    Nodes[0].travel_cost = 0.

    # add other points
    for idx, p in enumerate(midpoints[1:]):
        pos = np.array([p[0], p[1]])
        orient1 = np.array([p[2], p[3]])
        orient2 = np.array([-p[2], -p[3]])
        Nodes.append(RosyNode(pos, orient1, len(Nodes), idx + 1))
        Nodes.append(RosyNode(pos, orient2, len(Nodes), idx + 1))

    # add end point
    if manual_endpoint is None:
        Nodes.append(RosyNode(start_pos, start_orient, len(Nodes), 0))
    else:
        end_pos = np.array([manual_endpoint[0], manual_endpoint[1]])
        end_orient = np.array([manual_endpoint[2], manual_endpoint[3]])
        Nodes.append(RosyNode(end_pos, end_orient, len(Nodes), 0))


    # create unvisited Node list (this is the list we look at and modify for the search Algorithms)
    unv_Nodes = Nodes[:]
    # create list of
    node_preceeds = [-1] * len(unv_Nodes)  # memorize for each node the node that connected to it (-1 means no one did)

    """ 2) Set start point as current """
    curr_Node = unv_Nodes[0]
    finished = False

    while not finished and len(unv_Nodes) > 0:

        """ 3) Find potential succeeding and update their travel_cost """
        prec_idxs, costs = find_succeeding_nodes(curr_Node, unv_Nodes, 70)
        for idx, c in zip(prec_idxs, costs):
            if c < unv_Nodes[idx].travel_cost:
                unv_Nodes[idx].travel_cost = c
                # update node_preceeds
                node_preceeds[unv_Nodes[idx].list_indx] = curr_Node.list_indx

        """ 4) Set current node to visited """
        curr_Node.visited = True
        unv_Nodes.remove(curr_Node)

        """ 5) select next Node """
        min_travel_cost = float("inf")
        for n in unv_Nodes:
            if n.travel_cost <= min_travel_cost:
                min_travel_cost = n.travel_cost
                curr_Node = n

        """ 6) check if we are finished """
        if min_travel_cost == float("inf"):
            finished = True
            # print("Couldn't find path :(")
        if curr_Node.point_indx == 0:
            finished = True
            # print("Found path")


    # print(node_preceeds[-1])

    """ Have found a path. Reverse engineer it - literally by building the centerline
        from the endpoint to the start point """
    centerline = list()
    # add end_point manually
    centerline.append(Nodes[-1].pos)

    # look at preceeding node
    curr_prec_idx = node_preceeds[-1]
    while not curr_prec_idx == -1:
        # get position data from preceeding node
        pos = Nodes[curr_prec_idx].pos
        centerline.append(pos)
        # get next preceeding index
        curr_prec_idx = node_preceeds[curr_prec_idx]

    # reverse so we go from start to finish
    centerline.reverse()

    return centerline
