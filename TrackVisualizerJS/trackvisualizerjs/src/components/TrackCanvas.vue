<template>
    <div class="d-flex">
        <div>
            <canvas
                ref="canvas"
                @mousedown="canvasMouseDown"
                @mousemove="canvasMouseMove"
                @mouseup="documentMouseup"
                width="500"
                height="500"
            ></canvas>
        </div>
        <div class="ms-3" style="flex: 1">
            <div class="form-group">
                <label>track width</label>
                <input type="range" class="form-range" min="1" max="100" v-model.number="trackWidth" />
            </div>
            <div class="form-group">
                <label>spacing</label>
                <input type="range" class="form-range" min="1" max="100" v-model.number="spacing" />
            </div>
            <div class="form-group">
                <label>freeze ground truth</label>
                <input type="checkbox" class="form-check" v-model="freezeGroundTruth" />
            </div>

            <button @click="reset" class="btn btn-secondary my-2 me-4">Reset</button>
            <button @click="download" class="btn btn-primary my-2">Download</button>
            <hr />
            <a id="downloadAnchorElem" style="display: none"></a>
            <div class="form-group">
                <label>import</label>
                <input @change="selectFilesChange" type="file" class="form-control" />
            </div>
            <hr />
            <div class="alert alert-danger" v-if="outputError">{{ outputError }}</div>
            <div class="form-group">
                <label>output</label>
                <textarea class="form-control" rows="7" v-model="output" wrap="off"></textarea>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
interface Pylon {
    x: number;
    y: number;
    color: string;
    hidden?: boolean;
    undetect?: boolean;
}
interface Track {
    pylons: Pylon[];
    groundTruth: [number, number][];
}
interface Detection {
    blueDetected?: [number, number][];
    yellowDetected?: [number, number][];
    midLine?: [number, number][];
}

/**
 * NOTES:
 * do the AI stuff with perceptilabs.com/papers
 */
import { Options, Vue } from "vue-class-component";
@Options({})
export default class TrackCanvas extends Vue {
    private spacing = 30;
    private trackWidth = 10;

    private drawing = false;
    private lastPos = [0, 0] as [number, number];
    private startPos = [0, 0] as [number, number];

    private distance = 0;
    private nextDotTargetDistance = this.spacing;
    private trackData = { pylons: [], groundTruth: [] } as Track;
    private detection = {} as Detection;

    private outputError = "";

    get context() {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        return this.canvas.getContext("2d")!;
    }
    get canvas() {
        return this.$refs.canvas as HTMLCanvasElement;
    }

    d(p: [number, number], p2: [number, number]) {
        return Math.sqrt(Math.pow(p[0] - p2[0], 2) + Math.pow(p[1] - p2[1], 2));
    }
    getPos(event: MouseEvent) {
        var { x: offsetX, y: offsetY } = (event.target as HTMLCanvasElement).getBoundingClientRect();
        var x = event.clientX - offsetX;
        var y = event.clientY - offsetY;
        return [x, y] as [number, number];
    }
    drawCircle(x: number, y: number, radius: number, fill: string) {
        this.trackData.pylons.push({
            x: Math.round(x * 100) / 100,
            y: Math.round(y * 100) / 100,
            color: fill,
        });
        this.drawCircleRaw(x, y, radius, fill);
    }
    drawCircleRaw(x: number, y: number, radius: number, fill: string) {
        this.context.beginPath();
        this.context.arc(x, y, radius, 0, 2 * Math.PI, false);
        if (fill) {
            this.context.fillStyle = fill;
            this.context.fill();
        }
    }

    reset() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.distance = 0;
        this.nextDotTargetDistance = this.spacing;
        this.trackData.pylons = [];
        this.trackData.groundTruth = [];
        this.detection = {};
    }

    private groundTruthToBeAdded = [] as [number, number][];
    private freezeGroundTruth = false;

    canvasMouseDown(event: MouseEvent) {
        this.drawing = true;
        this.lastPos = this.getPos(event);
        this.groundTruthToBeAdded.push(this.lastPos.map((n) => Math.round(n * 100) / 100) as [number, number]);
        this.startPos = this.lastPos;
    }

    canvasMouseMove(event: MouseEvent) {
        if (!this.drawing) {
            return;
        }

        var p = this.getPos(event);
        this.groundTruthToBeAdded.push(p);

        this.context.beginPath();
        let distDelta = this.d(this.lastPos, p);
        this.distance += distDelta;
        this.context.moveTo(this.lastPos[0], this.lastPos[1]);
        this.context.lineTo(p[0], p[1]);
        this.context.stroke();

        if (this.distance >= this.nextDotTargetDistance) {
            this.nextDotTargetDistance += this.spacing;
            let d = this.trackWidth / distDelta;
            this.drawCircle(p[0] - (this.lastPos[1] - p[1]) * d, p[1] + (this.lastPos[0] - p[0]) * d, 5, "#0000FF");
            this.drawCircle(p[0] + (this.lastPos[1] - p[1]) * d, p[1] - (this.lastPos[0] - p[0]) * d, 5, "#FF0000");
        }
        this.lastPos = p;
    }
    documentMouseup(event: MouseEvent) {
        this.drawing = false;
        var endPoint = this.getPos(event);
        this.groundTruthToBeAdded.push(endPoint);

        if (this.d(this.startPos, endPoint) < 5 && this.trackData.pylons.length > 0) {
            //clicked
            let closest = this.trackData.pylons.reduce((a, b) => (this.d([a.x, a.y], endPoint) < this.d([b.x, b.y], endPoint) ? a : b));

            if (closest.undetect) {
                closest.undetect = false;
                closest.hidden = true;
                this.drawCircleRaw(closest.x, closest.y, 5, "#DDDDDD");
            } else if (closest.hidden) {
                closest.undetect = false;
                closest.hidden = false;
                closest.color = "#0000FF";
                this.drawCircleRaw(closest.x, closest.y, 5, closest.color);
            } else if (closest.color == "#0000FF") {
                closest.color = "#FF0000";
                this.drawCircleRaw(closest.x, closest.y, 5, closest.color);
            } else {
                closest.undetect = true;
                this.drawCircleRaw(closest.x, closest.y, 5, "#000");
            }
        } else {
            //not clicked add collected ground truth
            if (!this.freezeGroundTruth) this.trackData.groundTruth.push(...this.groundTruthToBeAdded);
            this.groundTruthToBeAdded = [];
        }
    }

    get output() {
        let filtered = this.trackData.pylons.filter((d) => !d.hidden && !d.undetect);

        return `
            groundTruth = ${JSON.stringify(this.trackData.groundTruth)}
            cone_blue = ${JSON.stringify(filtered.filter((d) => d.color == "#0000FF").map((o) => [o.x, o.y]))}
            cone_yellow = ${JSON.stringify(filtered.filter((d) => d.color == "#FF0000").map((o) => [o.x, o.y]))}
            faulty_cones = ${JSON.stringify(this.trackData.pylons.filter((d) => d.undetect).map((o) => [o.x, o.y]))}

            ${this.detection.blueDetected ? `cone_blue_detected = ${JSON.stringify(this.detection.blueDetected)}` : ""}
            ${this.detection.yellowDetected ? `cone_yellow_detected = ${JSON.stringify(this.detection.yellowDetected)}` : ""}
            ${this.detection.midLine ? `midLine = ${JSON.stringify(this.detection.midLine)}` : ""}
        `;
    }
    set output(value: string) {
        try {
            let entries = value
                .trim()
                .split("\n")
                .filter((l) => l)
                .map((r) => r.split("="));
            let map = Object.fromEntries(entries.map(([key, value]) => [key.trim(), JSON.parse(value)])) as {
                groundTruth: [number, number][];
                cone_blue: [number, number][];
                cone_yellow: [number, number][];
                faulty_cones: [number, number][];
                cone_blue_detected?: [number, number][];
                cone_yellow_detected?: [number, number][];
                midLine?: [number, number][];
            };
            this.trackData.pylons = [
                ...map.cone_blue.map(([x, y]) => ({ x, y, color: "#0000FF" })),
                ...map.cone_yellow.map(([x, y]) => ({ x, y, color: "#FF0000" })),
                ...map.faulty_cones.map(([x, y]) => ({ x, y, color: "#000000", undetect: true })),
            ];
            this.trackData.groundTruth = map.groundTruth;

            this.detection = {
                blueDetected: map.cone_blue_detected,
                yellowDetected: map.cone_yellow_detected,
                midLine: map.midLine,
            };
            this.outputError = "";
            this.redraw();
        } catch (e) {
            this.outputError = "" + e;
        }
    }

    download() {
        var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.trackData));
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        var dlAnchorElem = document.getElementById("downloadAnchorElem")!;
        dlAnchorElem.setAttribute("href", dataStr);
        dlAnchorElem.setAttribute("download", "trackCones.json");
        dlAnchorElem.click();
    }

    async selectFilesChange(event: Event) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        var files = (event.target as HTMLInputElement).files!;
        console.log(files);
        let result = JSON.parse(await files[0].text()) as Track;
        this.reset();
        this.trackData = result;
        this.redraw();
    }
    redraw() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.trackData.pylons.forEach(({ x, y, color, hidden, undetect }) =>
            this.drawCircleRaw(x, y, 5, hidden ? "#DDDDDD" : undetect ? "#000" : color)
        );

        this.strokePolygon(this.detection.blueDetected || [], "#7777FF", 1, 0, 3, true, true);
        this.strokePolygon(this.detection.yellowDetected || [], "#FF7777", 1, 0, 3, true, true);
        this.strokePolygon(this.detection.midLine || [], "#00FF00", 1, 0, 5, true, true);

        this.strokePolygon(this.trackData.groundTruth, "#000000", 1, 0, 3, true, false);
    }
    strokePolygon(
        pointsArray: [number, number][],
        strokeColor: string,
        scale: number,
        offset: number,
        radius: number,
        stroke?: boolean,
        circles?: boolean
    ) {
        if (pointsArray.length <= 0) return;
        this.context.beginPath();
        if (stroke)
            for (let i = 0; i < pointsArray.length; i++) {
                this.context.lineTo(pointsArray[i][0] * scale + offset, pointsArray[i][1] * scale + offset);
            }
        if (strokeColor != null && strokeColor != undefined) this.context.strokeStyle = strokeColor;
        this.context.stroke();
        if (circles)
            for (let i = 0; i < pointsArray.length; i++) {
                this.drawCircle(pointsArray[i][0] * scale + offset, pointsArray[i][1] * scale + offset, radius, strokeColor);
            }
    }
}
</script>

<style>
canvas {
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
    cursor: crosshair;
}
</style>
