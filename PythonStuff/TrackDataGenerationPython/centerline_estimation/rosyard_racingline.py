from helpers import rotate_vector, calc_distance, calc_angle_vectors
from numpy.linalg import norm
import numpy as np
import math




def calc_midpoint_orientation(midpoints):
    """
        gets a list of midpoints without orientation and adds orientation
    """

    # add first point as last point if that is not already the case
    if midpoints[0] != midpoints[-1]:
        print("Added one centerpoint")
        midpoints.append(midpoints[0][:])

    # calculate orientations as the vector from the current point to the next
    oriented_list = list()
    for idx, mp in enumerate(midpoints[:-1]):
        to_target = np.asarray(mp[0:2]) - np.asarray(midpoints[idx+1][0:2])
        to_target = to_target / norm(to_target)
        oriented_list.append(np.array([mp[0], mp[1], to_target[0], to_target[1]]))

    return oriented_list



def create_racingline_candidates(midpoints, candiates_per_midpoint=5, span_dist = 2.4):
    """
        for each midpoint

        params:
            midpoints (list) : list of midpoints with [x,y,ox,oy] (ie. position and orientation)
            candidates_per_midpoint (int) : number of candidates
            hor_size (float) : the number of metres from left to right where the candidates get placed

        returns:
            candiadtes (list) : list with n = len(midpoints) entries where each entry contains
                                m = candidates_per_midpoint RLCandidates

    """
    # check if we need to add orientations
    if len(midpoints[0]) < 4:
        midpoints = calc_midpoint_orientation(midpoints)

    candidates = list()

    for mp in midpoints:
        # get vector to the left
        v = np.asarray(rotate_vector(mp[2:4], -math.pi / 2.))
        # get leftmost point (Note: we expect the orientation of the midpoint to be normalized)
        start = mp[0:2] + v * span_dist / 2.

        # get step_size
        step = span_dist / candiates_per_midpoint
        # palce candidates
        loc_candidates = list()
        for i in range(candiates_per_midpoint):
            pos = start - v * step * i
            orient = mp[2:4]
            # loc_candidates.append(RLCandidate(pos, orient))
            loc_candidates.append([pos[0], pos[1], orient[0], orient[1]])

        candidates.append(loc_candidates)

    return candidates


class RLCandidate:
    def __init__(self, pos, orient, idx, lidx):

        self.pos = pos
        self.orient = orient
        self.track_idx = idx  # the track index indicates to which original centerpoint this candidate belongs
        self.list_indx = lidx

        self.travel_cost = float("inf")


def find_succeeding_candidate(curr_cand, unvisited_cands):
    """
        find potential succeeding nodes for current node and returns:
            - their index in the unvisited_Nodes list
            - the travel_cost to reach them
    """

    idxs = list()
    costs = list()
    curr_track_idx = curr_cand.track_idx

    # we are somehow in final candidate
    if curr_track_idx == len(unvisited_cands):
        return idxs, costs

    # search in next track index
    # for c in unvisited_cands[curr_track_idx + 1]:
    for idx, c in enumerate(unvisited_cands):

        if not c.track_idx == curr_track_idx + 1:
            continue

        # check distance
        dist = calc_distance(curr_cand.pos, c.pos)

        # check angles
        to_target = curr_cand.pos - c.pos
        angle1 = calc_angle_vectors(curr_cand.orient, to_target)
        angle2 = calc_angle_vectors(to_target, c.orient)

        """ TODO: real cost function """
        this_cost = dist
        # this_cost = curr_cand.travel_cost + (angle1 + angle2)

        idxs.append(idx)
        costs.append(this_cost)

    return idxs, costs


def find_racingline(candidates):
    """
        (...)
    """


    """ 1) Create Nodes and unvisited_Nodes from centerpoints """
    Nodes = list()  # list of all Nodes; Only need this for the centerline position


    # iterate through centerpoints (i.e. track idxs)
    li = 0
    for idx, track in enumerate(candidates):
        # iterate through candidates
        for c in track:
            pos = np.array([c[0], c[1]])
            orient = np.array([c[2], c[3]])
            Nodes.append(RLCandidate(pos, orient, idx, li))
            li += 1

    # intialise starting points
    num_per_cp = len(candidates[0])
    for c in Nodes[:num_per_cp]:
        c.travel_cost = 0

    # create unvisited Node list (this is the list we look at and modify for the search Algorithms)
    unv_Nodes = Nodes[:]
    # create list of
    node_preceeds = [-1] * len(unv_Nodes)  # memorize for each node the node that connected to it (-1 means no one did)

    """ 2) Set start point as current """
    curr_Node = unv_Nodes[0]
    finished = False

    while not finished and len(unv_Nodes) > 0:

        """ 3) Find potential succeeding and update their travel_cost """
        prec_idxs, costs = find_succeeding_candidate(curr_Node, unv_Nodes)
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

        """ 6) check if we have unexpectedly finished """
        if min_travel_cost == float("inf"):
            finished = True

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
