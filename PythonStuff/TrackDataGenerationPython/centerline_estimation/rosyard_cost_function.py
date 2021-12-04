

def cost(distance, angle1, angle2):
    """
        params (refer to rosyard_centerline):
            distance [0, maxDistance]
            angle1 [0, 1/2 PI]
            angle2 [0, 1/2 PI]

        idea: choose straight lines over turns, choose closer points over
              further ones
    """


    """ linear cost for distance """
    # distance_penalty = 0.1 # cost per meter
    dist_cost = 0.0000075 * distance**5 + 0.0005 * distance **3

    """ exponential cost for angles
        (small angle changes are acceptable, hard angle changes are not) """
    angle1_cost = (angle1+2.5)**0.9 * 5.
    angle2_cost = (angle2+2)**1.7 * 2.


    return dist_cost + angle1_cost + angle2_cost
