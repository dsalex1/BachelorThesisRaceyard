from helpers import calc_distance, densify_path


def densify(path):

    return


def point_error_dirty(p, path):
    """
        Calculates the shortest distance from point p to the given path

        Method: Takes point p and the path, looks for the closest point q in
        the path and returns the distance

        Note: to be mor clean, we would have to calculate for q the vector to
            its predecessor and its successor and then calculate the shortest
            distance from p to either of these two vectors. But since we
            expect the path to be densified anyway (so that each point has
            more or less the same importance), we omit that for simplicity
    """
    distances = [calc_distance(p, q) for q in path]
    return min(distances)


def path_error(pred_path, gt_path, densify = True):
    """
        returns the average shortest to gt_path for each point p in pred_path
    """
    if densify:
        pred_path = densify_path(pred_path, 0.5)
        gt_path = densify_path(gt_path, 0.5)

    point_errors = [point_error_dirty(p, gt_path) for p in pred_path]
    return sum(point_errors) / len(point_errors)


def calc_path_length(path):
    dist1 = 0.
    for idx, p in enumerate(path[1:]):
        dist1 += calc_distance(p, path[idx])
        # print(p, path[idx-1], calc_distance(p, path[idx]))
    return dist1


def distance_ratio(pred_path, gt_path):
    dist1 = calc_path_length(pred_path)
    dist2 = calc_path_length(gt_path)

    return dist1 / dist2
