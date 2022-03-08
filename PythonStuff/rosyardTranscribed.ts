function generatePNGFromPointData(
    pointData: {
        positions: { x: number; y: number };
        covariances: { covariance: number[] };
        colors: number;
    }[],
    carPosition: [number, number],
    imageSize: number
) {
    const IMAGE_SIZE = imageSize;
    let imageData = new Array<number>(IMAGE_SIZE * IMAGE_SIZE);

    for (let x = 0; x < IMAGE_SIZE; x++) for (let y = 0; y < IMAGE_SIZE; y++) imageData[(y * IMAGE_SIZE + x) * 4 + 3] = 255; // set alpha to 255 for all pixels

    for (let { positions, covariances, colors } of pointData) {
        let x = IMAGE_SIZE - Math.round((positions.x + carPosition[0]) * (IMAGE_SIZE - 1)) - 1;
        let y = IMAGE_SIZE - Math.round((positions.y + carPosition[1]) * (IMAGE_SIZE - 1)) - 1;
        //sum of covariances := x, atan to map [0,inf] to [0,1] and sqrt to even ditribution
        let confidence = Math.round((1 - ((Math.atan(covariances.covariance.reduce((a, c) => a + c)) / Math.PI) * 2) ** 0.5) * 255);

        if (colors != 98) imageData[(y * IMAGE_SIZE + x) * 4] = confidence; //color red when cone color is not blue
        if (colors != 121) imageData[(y * IMAGE_SIZE + x) * 4 + 2] = confidence; //color blue when cone color is not yellow
        //color purple when its both 
    }
    return imageData;
}

function simulateDriving() {
    const car = { x: 0, y: 0, theta: 0 } // get car

    const TRAINING_SAMPLE_RADIUS = 8;
    const TSR = TRAINING_SAMPLE_RADIUS;

    const CAR_POSITION: [number, number] = [0.5, 0.25]  // offset position of car (from lower left corner) center horizontal, lower quarter vetical

    //start point of NN input data
    let startPoint = [car.x - 2 * CAR_POSITION[0] * TSR, car.y - 2 * CAR_POSITION[1] * TSR];
    let size = [TSR * 2, TSR * 2];

    let slamMap: {
        positions: { x: number; y: number };
        covariances: { covariance: number[] };
        colors: number;
    }[]

    //filter for all points that are in range
    const slamMapForSteering = slamMap.filter(({ positions }) => {
        const [xT, yT] = rotby([positions.x, positions.y], [car.x, car.y], -car.theta);
        return xT >= startPoint[0] && xT <= startPoint[0] + size[0] && yT >= startPoint[1] && yT <= startPoint[1] + size[1];
    });
    //map them to the image coordiate system ranging from -1 to 1
    const pointData = slamMapForSteering.map((p) => {
        const [xT, yT] = mul(rot(min([p.positions.x, p.positions.y], [car.x, car.y]), -car.theta), [1 / size[0], 1 / size[1]]);
        return { ...p, positions: { x: xT, y: yT } };
    });

    const IMAGE_SIZE = 32;

    const currentPNG = generatePNGFromPointData(pointData, CAR_POSITION, IMAGE_SIZE);

    const [speed, angle] = steerCarFromPNG(currentPNG, [IMAGE_SIZE, IMAGE_SIZE]);
    moveCar(speed, angle);
}

let steering = 0;
function steerCarFromPNG(pixels: number[], sizes: [number, number]): [number, number] {
    //let tensorData = tf.from;
    const tensorInput = tf
        .tensor(pixels, [1, sizes[0], sizes[1], 4])
        .slice([0, 0, 0, 0], [-1, -1, -1, 3])
        .mul(1 / 255);
    const prediction = tfjsModel.predict(tensorInput).data().map((s: number) => (Math.sign(s) * Math.abs(s) ** 3) / 10);
    //training data mapping (s=>Math.sign(s)*Math.abs(s)**(1/3)
    //output unmapping (s=>Math.sign(s)*Math.abs(s)**3
    const steering = prediction[1] * 40 * 30;

    return [(1 / (Math.abs(steering) + 8)) * 5, steering];
}

function moveCar(distance: number, angle: number) {
    const { x, y, theta } = { x: 0, y: 0, theta: 0 } // get car

    const newTheta = theta + distance * ((angle * Math.PI) / 180);
    const [newX, newY] = plus([x, y], rot(mul([1, 0], distance), (newTheta / Math.PI) * 180));

    let newState = { newX, newY, newTheta } // output car
}








//#######################################################################################################
function min(p: readonly [number, number], p2: readonly [number, number]) {
    return [p[0] - p2[0], p[1] - p2[1]] as const;
}
function mul(p: readonly [number, number], p2: number | [number, number]): readonly [number, number] {
    if (typeof p2 == "number") return [p[0] * p2, p[1] * p2] as const;
    return [p[0] * p2[0], p[1] * p2[1]] as const;
}
function norm(p: readonly [number, number]) {
    return mul(p, 1 / d(p, [0, 0]));
}
function rot([x, y]: readonly [number, number], angle?: number) {
    if (angle === undefined) return [y, -x] as const;
    return [
        Math.cos((angle / 180) * Math.PI) * x - Math.sin((angle / 180) * Math.PI) * y,
        Math.sin((angle / 180) * Math.PI) * x + Math.cos((angle / 180) * Math.PI) * y,
    ] as const;
}
function rotby(p: readonly [number, number], q: readonly [number, number], angle?: number) {
    return plus(rot(min(p, q), angle), q);
}
function plus(p: readonly [number, number], p2: readonly [number, number]) {
    return [p[0] + p2[0], p[1] + p2[1]] as const;
}