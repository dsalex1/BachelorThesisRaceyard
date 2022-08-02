#!/usr/bin/env python
#import rospy
import math
#from sensor_msgs.msg import PointCloud2
#from sensor_msgs import point_cloud2
#from geometry_msgs.msg import Point
#from rosyard_common.msg import Map, CarStateRaw, LandmarkArray
import tensorflow as tf
import math
import json
import numpy as np
from functools import reduce
from timeit import default_timer as timer
from munch import DefaultMunch

#######################################################################################
################################### CENTERLINE ########################################


def generatePNGFromPointData(pointData, carPosition, imageSize):
    """
    params:
    pointData: {
        positions: { x: number; y: number };
        covariances: { covariance: number[] };
        colors: number;
    }[],
    carPosition: [number, number],
    imageSize: number
    """
    IMAGE_SIZE = imageSize
    imageData = [0] * (IMAGE_SIZE * IMAGE_SIZE * 3)

    for point in pointData:
        x = IMAGE_SIZE - \
            int(round((point["positions"]["x"] + carPosition[0])
                * (IMAGE_SIZE - 1))) - 1
        y = IMAGE_SIZE - \
            int(round((point["positions"]["y"] + carPosition[1])
                * (IMAGE_SIZE - 1))) - 1
        # sum of covariances := x, atan to map [0,inf] to [0,1] and sqrt to even ditribution

        confidence = round(
            (1 - (math.atan(sum(point["covariances"]["covariance"])) / math.pi * 2) ** 0.5) * 255)

        if point["colors"] != 98:
            # color red when cone color is not blue
            imageData[(y * IMAGE_SIZE + x) * 3] = confidence

        if point["colors"] != 121:
            # color blue when cone color is not yellow
            imageData[(y * IMAGE_SIZE + x) * 3 + 2] = confidence
        # color purple when its both
    return imageData


def filterMapData(car, slamMap, CAR_POSITION, TSR):
    startPoint = (car["x"] - (2 * CAR_POSITION[0] * TSR),
                  car["y"] - (2 * CAR_POSITION[1] * TSR))
    size = (TSR * 2, TSR * 2)

    def pointWithinRect(point, pos, size):
        return point[0] >= pos[0] and point[0] <= pos[0] + size[0] and point[1] >= pos[1] and point[1] <= pos[1] + size[1]

    # filter for all points that are in range
    slamMapForSteering = [point for point in slamMap if pointWithinRect(
        rotBy(fromXY(point["positions"]), fromXY(car), -car["theta"]), startPoint, size)]

    # map them to the image coordiate system ranging from -1 to 1 (offseted by an assumed CAR_POSITION of (0.5, 0.5))
    for point in slamMapForSteering:
        point["positions"] = toXY(
            rot(fromXY(point["positions"]) - fromXY(car), -car["theta"]) / size)

    return slamMapForSteering


def getCurvatures(pixels, sizes, model):
    data = np.reshape(pixels, (sizes[0], sizes[1], 3))/255.0,

    prediction = model.predict(
        tf.convert_to_tensor(data, dtype=tf.float32))[0]
    # training data mapping (s=>Math.sign(s)*Math.abs(s)**(1/3)
    # output unmapping (s=>Math.sign(s)*Math.abs(s)**3
    return [(point ** 3) for point in prediction]


def predictCurvaturesFromSlam(car, slamMap, neuralNetworkModel):
    """
    Main function, mapping from car and slam map to local cetnerline coordiates
    params:
    slamMap: {
        positions: {x: number, y: number}
        covariances: {covariance: number[]}
        colors: number
    }[]
    car: {x: number, y: number, theta: number}
    """
    TRAINING_SAMPLE_RADIUS = 8
    TSR = TRAINING_SAMPLE_RADIUS
    # offset position of car (from lower left corner) center horizontal, lower quarter vetical
    CAR_POSITION = (0.5, 0.25)

    # start point of NN input data
    pointData = filterMapData(car, slamMap, CAR_POSITION, TSR)

    IMAGE_SIZE = 32
    currentPNG = generatePNGFromPointData(pointData, CAR_POSITION, IMAGE_SIZE)

    curvatures = getCurvatures(
        currentPNG, (IMAGE_SIZE, IMAGE_SIZE), neuralNetworkModel)

    # map the curvatures to local xy coordinates
    return list(map(lambda p: curvatureToXy(p[0], p[1]), zip(curvatures, (2, 4, 6, 8, 10))))


#######################################################################################
################################### HELPERS ###########################################


def rotBy(point, origin, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in degrees.
    """
    ox, oy = origin
    px, py = point

    qx = ox + math.cos(math.radians(angle)) * (px - ox) - \
        math.sin(math.radians(angle)) * (py - oy)
    qy = oy + math.sin(math.radians(angle)) * (px - ox) + \
        math.cos(math.radians(angle)) * (py - oy)
    return np.array((qx, qy))


def rot(point, angle):
    return rotBy(point, (0, 0), angle)


def fromXY(point):
    return np.array((point["x"], point["y"]))


def toXY(point):
    return {'x': point[0], 'y': point[1]}


def curvatureToXy(c, d):
    return (math.cos(d*c)/c - 1/c, math.sin(d*c)/c)


def xyToCurvature(x, y):
    return 2*x/(x**2+y**2)

#######################################################################################
################################### TESTING #######################################


def testImplementation(neuralNetworkModel):
    # this data structure is expected by the functions
    result = predictCurvaturesFromSlam({"x": 31.0, "y": -5.3, "theta": -114.1}, [
        {'positions': {'x': 36.2, 'y': -8.6, 'z': 0},
            'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121},
        {'positions': {'x': 43.2, 'y': -4.8, 'z': 0},
            'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': 41.9, 'y': -8.9, 'z': 0},
            'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121},
        {'positions': {'x': -2.0, 'y': -3.9, 'z': 0},
            'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': -4.0, 'y': -4.5, 'z': 0},
            'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': 31.6, 'y': -3.9, 'z': 0},
            'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': 40.2, 'y': -4.5, 'z': 0},
            'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': 37.2, 'y': -4.6, 'z': 0},
            'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
        {'positions': {'x': 30.6, 'y': -7.9, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121}], neuralNetworkModel)

    # with the currently trained network this should yield the following output (or with a different neuwork, at least somewhat similar)
    print("it should have the correct result: ", result == [(-0.11348429008726058, 1.9957006354579976),
                                                            (-0.4874363343233217,
                                                             3.960122633014861),
                                                            (-0.8863731290529628,
                                                             5.911796852114679),
                                                            (-1.0438232567798913,
                                                             7.908469536019484),
                                                            (-1.6542053185888648, 9.815181787668886)])

#######################################################################################
################################### NODE CONFIG #######################################


def transformInputs(landmarks, carstate):
    # transform the topic messages from:
    # landmarks: rosyard_common/LandmarkArray
    # carstate: rosyard_common/CarStateRaw
    #
    # into these dictionary like formats:
    # slamMap: {
    #     positions: {x: number, y: number}
    #     covariances: {covariance: number[]}
    #     colors: number
    # }[]
    # car: {x: number, y: number, theta: number}

    # this code was used to transform the PointCloud2 type
    # cones = point_cloud2.read_points(
    #    inputMap, skip_nans=True, field_names=("x", "y", "z", "rgb"))

    # map = [{'positions': {'x': cone[0], 'y': cone[1], 'z': cone[2]},
    #        'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': cone[3]} for cone in cones]  # we have the wrong topic, so we cant easily use covariances

    map = landmarks
    car = carstate["car_state"]

    return (map, car)


def transformOutput(predictedFuturePoints):
    # transform the output:
    # predictedFuturePoints: List(Tuple(number, number))
    #
    # into rosyard_common/Map

    #map = Map()
    #map.header.frame_id = "map"
    #map.local_centerline = [Point(x, y) for x, y in predictedFuturePoints]

    return predictedFuturePoints


class CenterLineEstimation:
    def __init__(self):
        self.inputMap = None
        self.inputCar = None
        self.neuralNetworkModel = tf.keras.models.load_model('saved_model')

    def getCenterlineMap(self):

        transformedMap, transformedCar = transformInputs(
            self.inputMap, self.inputCar)

        predictedFuturePoints = predictCurvaturesFromSlam(
            transformedCar, transformedMap,  self.neuralNetworkModel)

        return transformOutput(predictedFuturePoints)

    def mapCallback(self, slam_map):
        self.inputMap = slam_map  # save for use in publishing

    def carCallback(self, slam_car):
        self.inputCar = slam_car  # save for use in publishing


if __name__ == "__main__":

    # init node
    #rospy.init_node('center_line_estimator', anonymous=True)

    # we need the slam map as well as the car
    # map_topic = rospy.get_param('/nodes/slam_map_topic_name')
    #map_topic = rospy.get_param('/nodes/slam_map_debug_topic_name')
    #car_topic = rospy.get_param('/nodes/slam_car_topic_name')

    # location to publish center_line
    #center_line_topic = rospy.get_param('/nodes/map_topic_name')
    #updateRate = rospy.get_param('/nodes/map_rate')

    cone_blue = []
    cone_yellow = []
    faulty_cones = []
    slamMap =[{"positions": {"x": cone[0], "y":cone[1]}, "covariances": {
        "covariance": (0,0.001,0,0.002)}, "colors": 98} for cone in cone_blue]+[{"positions": {"x": cone[0], "y":cone[1]}, "covariances": {
        "covariance": (0, 0.001, 0, 0.002)}, "colors": 121} for cone in cone_yellow]+[{"positions": {"x": cone[0], "y":cone[1]}, "covariances": {
        "covariance": (0, 0.001, 0, 0.002)}, "colors": 0} for cone in faulty_cones]

    # slamMap: {
    #     positions: {x: number, y: number}
    #     covariances: {covariance: number[]}
    #     colors: number
    # }[]
    car = {"x": 0, "y": 0, "theta": 0}

    center_line_est = CenterLineEstimation()
    center_line_est.mapCallback(slamMap)
    center_line_est.carCallback({"car_state": car})
    result = center_line_est.getCenterlineMap()

    trys = 1
    print(str(trys) + " cones")
    print(str(len(cone_blue+cone_yellow+faulty_cones)) + " tries")

    start = timer()
    testImplementation(tf.keras.models.load_model('saved_model'))
    #for i in range(trys):
        #result = center_line_est.getCenterlineMap()
    end = timer()
    # Time in seconds, e.g. 5.38091952400282
    print("{:10f}ms".format((end - start)/trys*1000))

    # Subscriber
    #rospy.Subscriber(map_topic, LandmarkArray, center_line_est.mapCallback)
    # rospy.Subscriber(map_topic, PointCloud2, center_line_est.mapCallback)
    #rospy.Subscriber(car_topic, CarStateRaw, center_line_est.carCallback)

    # Publisher
    #map_publisher = rospy.Publisher(center_line_topic, Map, queue_size=10)

    #rate = rospy.Rate(updateRate)

    #try:
    #    while not rospy.is_shutdown():
    #        # rospy.spin()
    #        map = center_line_est.getCenterlineMap()
    #        map_publisher.publish(map)
    #        rate.sleep()

    #except KeyboardInterrupt:
    #    rospy.loginfo("Shutting down node %s", 'Center Line Estimation')
