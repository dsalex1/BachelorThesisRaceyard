import tensorflow as tf
import math
import json
import numpy as np
from functools import reduce

neuralNetworkModel = tf.keras.models.load_model('saved_model')

#######################################################################################
################################### CENTERLINE ########################################

# params:
# pointData: {
#     positions: { x: number; y: number };
#     covariances: { covariance: number[] };
#     colors: number;
# }[],
# carPosition: [number, number],
# imageSize: number
def generatePNGFromPointData(pointData, carPosition, imageSize):
  IMAGE_SIZE = imageSize
  imageData = [0] * (IMAGE_SIZE * IMAGE_SIZE * 3)

  for point in pointData:
    x = IMAGE_SIZE - \
        int(round((point["positions"]["x"] + carPosition[0])
            * (IMAGE_SIZE - 1))) - 1
    y = IMAGE_SIZE - \
        int(round((point["positions"]["y"] + carPosition[1])
            * (IMAGE_SIZE - 1))) - 1
    #sum of covariances := x, atan to map [0,inf] to [0,1] and sqrt to even ditribution

    confidence = round(
        (1 - (math.atan(sum(point["covariances"]["covariance"])) / math.pi * 2) ** 0.5) * 255)

    if point["colors"] != 98:
      # color red when cone color is not blue
      imageData[(y * IMAGE_SIZE + x) * 3] = confidence

    if point["colors"] != 121:
      # color blue when cone color is not yellow
      imageData[(y * IMAGE_SIZE + x) * 3 + 2] = confidence
    #color purple when its both
  return imageData


def filterMapData(car, slamMap, CAR_POSITION, TSR):
  startPoint = (car["x"] - (2 * CAR_POSITION[0] * TSR),
                car["y"] - (2 * CAR_POSITION[1] * TSR))
  size = (TSR * 2, TSR * 2)

  def pointWithinRect(point, pos, size):
      return point[0] >= pos[0] and point[0] <= pos[0] + size[0] and point[1] >= pos[1] and point[1] <= pos[1] + size[1]

  #filter for all points that are in range
  slamMapForSteering = [point for point in slamMap if pointWithinRect(
      rotBy(fromXY(point["positions"]), fromXY(car), -car["theta"]), startPoint, size)]

  #map them to the image coordiate system ranging from -1 to 1 (offseted by an assumed CAR_POSITION of (0.5, 0.5))
  for point in slamMapForSteering:
    point["positions"] = toXY(
        rot(fromXY(point["positions"]) - fromXY(car), -car["theta"]) / size)

  return slamMapForSteering


def getCurvatures(pixels, sizes):
    data = np.reshape(pixels, (sizes[0], sizes[1], 3))/255.0,

    prediction = reloaded.predict(
        tf.convert_to_tensor(data, dtype=tf.float32))[0]
    # training data mapping (s=>Math.sign(s)*Math.abs(s)**(1/3)
    # output unmapping (s=>Math.sign(s)*Math.abs(s)**3
    return [(point ** 3)  for point in prediction]

# Main function, mapping from car and slam map to local cetnerline coordiates
# params:
# slamMap: {
#     positions: {x: number, y: number}
#     covariances: {covariance: number[]}
#     colors: number
# }[]
# car: {x: number, y: number, theta: number}
def simulateDriving(car, slamMap):
    TRAINING_SAMPLE_RADIUS = 8
    TSR = TRAINING_SAMPLE_RADIUS
    # offset position of car (from lower left corner) center horizontal, lower quarter vetical
    CAR_POSITION = (0.5, 0.25)

    # start point of NN input data
    pointData = filterMapData(car, slamMap, CAR_POSITION, TSR)

    IMAGE_SIZE = 32
    currentPNG = generatePNGFromPointData(pointData, CAR_POSITION, IMAGE_SIZE)

    curvatures = getCurvatures(currentPNG, (IMAGE_SIZE, IMAGE_SIZE))

    #map the curvatures to local xy coordinates
    return list(map(lambda p: curvatureToXy(p[0], p[1]), zip(curvatures, (2, 4, 6, 8, 10))))

#######################################################################################
################################### DRIVER ###########################################

def steerCarFromCurvatures(curvatures):
    steering = curvatures[1] * 40 * 30

    return ((1 / (abs(steering)+8))*5, steering)

def moveCar(distance, angle):
    x, y, theta = (0, 0, 0)  # get car
    newTheta = theta + distance * ((angle * math.pi) / 180)
    newX, newY = np.array((x, y)) + rot(np.array((1, 0))
                                        * distance, (newTheta / math.pi) * 180)
    return (newX, newY, newTheta)  # output

#######################################################################################
################################### HELPERS ###########################################

def rotBy(point, origin, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
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

def curvatureToXy(c,d):
   return (math.cos(d*c)/c - 1/c, math.sin(d*c)/c)

def xyToCurvature(x,y):
   return 2*x/(x**2+y**2)


def testImplementation():
    #this data structure is expected by the functions
    result = simulateDriving({"x": 31.0, "y": -5.3, "theta": -114.1}, [
    {'positions': {'x': 36.2, 'y': -8.6, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121},
    {'positions': {'x': 43.2, 'y': -4.8, 'z': 0}, 'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': 41.9, 'y': -8.9, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121},
    {'positions': {'x': -2.0, 'y': -3.9, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': -4.0, 'y': -4.5, 'z': 0}, 'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': 31.6, 'y': -3.9, 'z': 0},'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': 40.2, 'y': -4.5, 'z': 0},'covariances': {'covariance': [0.0, -0.0, -0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': 37.2, 'y': -4.6, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 98},
    {'positions': {'x': 30.6, 'y': -7.9, 'z': 0}, 'covariances': {'covariance': [0.0, 0.0, 0.0, 0.0]}, 'colors': 121}])

    #with the currently trained network this should yield the following output
    print("it should have the correct result: ", result == [(-0.11348429008726058, 1.9957006354579976),
                                                            (-0.4874363343233217, 3.960122633014861),
                                                            (-0.8863731290529628, 5.911796852114679), 
                                                            (-1.0438232567798913, 7.908469536019484), 
                                                            (-1.6542053185888648, 9.815181787668886)])


testImplementation()





