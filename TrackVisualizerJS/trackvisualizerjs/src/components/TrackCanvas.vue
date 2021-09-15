<template>
    <div class="d-flex">
        <div class="">
            <div>
                <h4>{{ name }}</h4>
            </div>
            <canvas
                ref="canvas"
                @mousedown="canvasMouseDown"
                @mousemove="canvasMouseMove"
                @mouseup="documentMouseup"
                width="500"
                height="500"
            ></canvas>
            <div style="width: 500px">
                click to edit single points (freeze ground truth before starting to edit)<br />
                <div style="display: inline-block; background: #ff0000; width: 10px; height: 10px; border-radius: 5px" />
                <div class="ms-1" style="display: inline-block; background: #0000ff; width: 10px; height: 10px; border-radius: 5px" />
                left/right
                <div class="ms-2" style="display: inline-block; background: #000000; width: 10px; height: 10px; border-radius: 5px" />
                unrecognized color
                <div class="ms-2" style="display: inline-block; background: #dddddd; width: 10px; height: 10px; border-radius: 5px" />
                non existent
                <div class="ms-2" style="display: inline-block; background: #00ff00; width: 10px; height: 10px; border-radius: 5px" />
                midline
            </div>
        </div>
        <div class="ms-3" style="flex: 1">
            <div class="form-group">
                <label>track width</label>
                <div class="d-flex">
                    <input type="range" class="form-range w-0 flex-1" min="1" max="100" v-model.number="trackWidth" />
                    <output class="ms-2">{{ trackWidth }}</output>
                </div>
            </div>
            <div class="form-group">
                <label>derived width</label>
                <div class="d-flex">
                    <input type="range" class="form-range w-0 flex-1" min="1" max="100" :value="derivedWidth / 2" disabled />
                    <output class="ms-2">{{ Math.round(derivedWidth / 2) }}</output>
                </div>
            </div>
            <div class="form-group">
                <label>spacing</label>
                <div class="d-flex">
                    <input type="range" class="form-range w-0 flex-1" min="1" max="100" v-model.number="spacing" />
                    <output class="ms-2">{{ spacing }}</output>
                </div>
            </div>
            <div class="form-group">
                <label>derived spacing</label>
                <div class="d-flex">
                    <input type="range" class="form-range w-0 flex-1 handle-red" min="1" max="100" :value="derivedSpacingRed" disabled />
                    <output class="ms-2">{{ Math.round(derivedSpacingRed) }}</output>
                </div>
                <div class="d-flex">
                    <input type="range" class="form-range w-0 flex-1 handle-blue" min="1" max="100" :value="derivedSpacingBlue" disabled />
                    <output class="ms-2">{{ Math.round(derivedSpacingBlue) }}</output>
                </div>
            </div>
            <div class="form-group">
                <label>freeze ground truth</label>
                <input type="checkbox" class="form-check" v-model="freezeGroundTruth" />
            </div>

            <button @click="reset" class="btn btn-danger my-2 me-4">Reset</button>
            <button @click="download" class="btn btn-secondary my-2 me-4">Download</button>
            <button @click="addMissingPressed" class="btn btn-info my-2 me-4">Add missing</button>
            <button @click="calculatePython" class="btn btn-success my-2" :disabled="pythonLoading">
                Calculate Python Midline <span v-if="pythonLoading">(loading...)</span>
            </button>
            <hr />
            <a id="downloadAnchorElem" style="display: none"></a>
            <div class="form-group">
                <DemoChooser @fileSelected="openDemo" />
            </div>
            <div class="form-group">
                <label>import YAML</label>
                <input @change="YAMLFilesChange" type="file" class="form-control" />
            </div>
            <div class="form-group">
                <label>open JSON</label>
                <input @change="JSONFilesChange" type="file" class="form-control" />
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

interface YAMLFile {
    cones_left: string[];
    cones_orange: string[];
    cones_orange_big: string[];
    cones_right: string[];
    middle_points: string[];
    starting_pose_front_wing: number[];
    tk_device: string[];
}

/**
 * NOTES:
 * do the AI stuff with perceptilabs.com/papers
 */
import { Options, Vue } from "vue-class-component";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
//@ts-ignore
import * as YAML from "yamljs";
declare let loadPyodide: (opt: { indexURL: string }) => Promise<{
    runPython: (code: string) => any;
    runPythonAsync: (code: string) => any;
    loadPackagesFromImports: (code: string) => any;
    globals: {
        get: (key: "result") => {
            toJs: () => any;
        };
        set: (key: "args", value: any) => void;
    };
}>;
type Await<T> = T extends PromiseLike<infer U> ? U : T;

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
    private name = "";

    get context() {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        return this.canvas.getContext("2d")!;
    }
    get canvas() {
        return this.$refs.canvas as HTMLCanvasElement;
    }

    private pyodide = null as Await<ReturnType<typeof loadPyodide>> | null;
    async mounted() {
        /*this.output = `
            groundTruth = [[78.2,87.39],[78.20455169677734,83.3948974609375],[83.20455169677734,78.3948974609375],[89.20455169677734,73.3948974609375],[93.20455169677734,71.3948974609375],[97.20455169677734,68.3948974609375],[101.20455169677734,67.3948974609375],[109.20455169677734,62.3948974609375],[116.20455169677734,59.3948974609375],[123.20455169677734,57.3948974609375],[131.20455169677734,56.3948974609375],[136.20455169677734,53.3948974609375],[144.20455169677734,52.3948974609375],[154.20455169677734,50.3948974609375],[166.20455169677734,48.3948974609375],[174.20455169677734,46.3948974609375],[182.20455169677734,45.3948974609375],[194.20455169677734,45.3948974609375],[202.20455169677734,43.3948974609375],[214.20455169677734,42.3948974609375],[222.20455169677734,42.3948974609375],[229.20455169677734,42.3948974609375],[238.20455169677734,42.3948974609375],[248.20455169677734,42.3948974609375],[255.20455169677734,42.3948974609375],[259.20455169677734,42.3948974609375],[267.20455169677734,42.3948974609375],[275.20455169677734,42.3948974609375],[283.20455169677734,42.3948974609375],[288.20455169677734,42.3948974609375],[295.20455169677734,43.3948974609375],[299.20455169677734,45.3948974609375],[309.20455169677734,46.3948974609375],[316.20455169677734,47.3948974609375],[321.20455169677734,49.3948974609375],[328.20455169677734,49.3948974609375],[336.20455169677734,52.3948974609375],[340.20455169677734,53.3948974609375],[347.20455169677734,56.3948974609375],[351.20455169677734,57.3948974609375],[353.20455169677734,57.3948974609375],[355.20455169677734,61.3948974609375],[357.20455169677734,61.3948974609375],[359.20455169677734,63.3948974609375],[361.20455169677734,66.3948974609375],[362.20455169677734,67.3948974609375],[364.20455169677734,70.3948974609375],[366.20455169677734,74.3948974609375],[367.20455169677734,77.3948974609375],[368.20455169677734,82.3948974609375],[368.20455169677734,85.3948974609375],[371.20455169677734,88.3948974609375],[371.20455169677734,90.3948974609375],[371.20455169677734,93.3948974609375],[371.20455169677734,98.3948974609375],[371.20455169677734,99.3948974609375],[371.20455169677734,104.3948974609375],[370.20455169677734,108.3948974609375],[369.20455169677734,111.3948974609375],[369.20455169677734,116.3948974609375],[368.20455169677734,120.3948974609375],[366.20455169677734,125.3948974609375],[365.20455169677734,127.3948974609375],[364.20455169677734,128.3948974609375],[362.20455169677734,133.3948974609375],[359.20455169677734,138.3948974609375],[358.20455169677734,140.3948974609375],[355.20455169677734,142.3948974609375],[352.20455169677734,146.3948974609375],[350.20455169677734,147.3948974609375],[348.20455169677734,148.3948974609375],[346.20455169677734,149.3948974609375],[343.20455169677734,152.3948974609375],[339.20455169677734,154.3948974609375],[335.20455169677734,155.3948974609375],[333.20455169677734,157.3948974609375],[331.20455169677734,158.3948974609375],[327.20455169677734,159.3948974609375],[323.20455169677734,161.3948974609375],[318.20455169677734,164.3948974609375],[315.20455169677734,168.3948974609375],[313.20455169677734,168.3948974609375],[311.20455169677734,169.3948974609375],[307.20455169677734,171.3948974609375],[306.20455169677734,171.3948974609375],[304.20455169677734,174.3948974609375],[302.20455169677734,176.3948974609375],[299.20455169677734,177.3948974609375],[298.20455169677734,178.3948974609375],[296.20455169677734,179.3948974609375],[295.20455169677734,180.3948974609375],[293.20455169677734,182.3948974609375],[291.20455169677734,184.3948974609375],[290.20455169677734,185.3948974609375],[289.20455169677734,186.3948974609375],[289.20455169677734,188.3948974609375],[288.20455169677734,189.3948974609375],[287.20455169677734,193.3948974609375],[287.20455169677734,195.3948974609375],[286.20455169677734,197.3948974609375],[286.20455169677734,198.3948974609375],[286.20455169677734,200.3948974609375],[286.20455169677734,204.3948974609375],[286.20455169677734,206.3948974609375],[286.20455169677734,208.3948974609375],[286.20455169677734,212.3948974609375],[287.20455169677734,214.3948974609375],[287.20455169677734,216.3948974609375],[289.20455169677734,218.3948974609375],[289.20455169677734,219.3948974609375],[290.20455169677734,222.3948974609375],[291.20455169677734,224.3948974609375],[292.20455169677734,227.3948974609375],[294.20455169677734,228.3948974609375],[295.20455169677734,230.3948974609375],[297.20455169677734,231.3948974609375],[298.20455169677734,232.3948974609375],[299.20455169677734,234.3948974609375],[300.20455169677734,236.3948974609375],[301.20455169677734,237.3948974609375],[302.20455169677734,238.3948974609375],[304.20455169677734,239.3948974609375],[306.20455169677734,240.3948974609375],[307.20455169677734,241.3948974609375],[308.20455169677734,243.3948974609375],[310.20455169677734,243.3948974609375],[311.20455169677734,244.3948974609375],[313.20455169677734,245.3948974609375],[315.20455169677734,246.3948974609375],[317.20455169677734,247.3948974609375],[318.20455169677734,247.3948974609375],[321.20455169677734,249.3948974609375],[323.20455169677734,250.3948974609375],[325.20455169677734,250.3948974609375],[328.20455169677734,251.3948974609375],[330.20455169677734,252.3948974609375],[334.20455169677734,252.3948974609375],[337.20455169677734,254.3948974609375],[338.20455169677734,254.3948974609375],[340.20455169677734,254.3948974609375],[342.20455169677734,257.3948974609375],[345.20455169677734,257.3948974609375],[348.20455169677734,258.3948974609375],[350.20455169677734,260.3948974609375],[354.20455169677734,260.3948974609375],[358.20455169677734,263.3948974609375],[360.20455169677734,265.3948974609375],[362.20455169677734,266.3948974609375],[367.20455169677734,267.3948974609375],[370.20455169677734,272.3948974609375],[372.20455169677734,272.3948974609375],[375.20455169677734,274.3948974609375],[377.20455169677734,276.3948974609375],[378.20455169677734,278.3948974609375],[380.20455169677734,278.3948974609375],[382.20455169677734,280.3948974609375],[385.20455169677734,282.3948974609375],[386.20455169677734,284.3948974609375],[387.20455169677734,287.3948974609375],[388.20455169677734,288.3948974609375],[389.20455169677734,290.3948974609375],[390.20455169677734,292.3948974609375],[390.20455169677734,293.3948974609375],[393.20455169677734,296.3948974609375],[393.20455169677734,297.3948974609375],[394.20455169677734,298.3948974609375],[395.20455169677734,300.3948974609375],[395.20455169677734,303.3948974609375],[396.20455169677734,305.3948974609375],[396.20455169677734,307.3948974609375],[396.20455169677734,311.3948974609375],[397.20455169677734,311.3948974609375],[397.20455169677734,316.3948974609375],[397.20455169677734,317.3948974609375],[397.20455169677734,322.3948974609375],[397.20455169677734,326.3948974609375],[397.20455169677734,329.3948974609375],[397.20455169677734,334.3948974609375],[397.20455169677734,337.3948974609375],[397.20455169677734,339.3948974609375],[397.20455169677734,343.3948974609375],[397.20455169677734,346.3948974609375],[397.20455169677734,347.3948974609375],[397.20455169677734,348.3948974609375],[396.20455169677734,354.3948974609375],[395.20455169677734,356.3948974609375],[395.20455169677734,357.3948974609375],[395.20455169677734,358.3948974609375],[393.20455169677734,360.3948974609375],[392.20455169677734,362.3948974609375],[391.20455169677734,364.3948974609375],[389.20455169677734,368.3948974609375],[388.20455169677734,369.3948974609375],[387.20455169677734,373.3948974609375],[386.20455169677734,375.3948974609375],[384.20455169677734,377.3948974609375],[382.20455169677734,378.3948974609375],[381.20455169677734,381.3948974609375],[378.20455169677734,383.3948974609375],[378.20455169677734,385.3948974609375],[376.20455169677734,386.3948974609375],[374.20455169677734,388.3948974609375],[372.20455169677734,390.3948974609375],[368.20455169677734,391.3948974609375],[365.20455169677734,392.3948974609375],[360.20455169677734,395.3948974609375],[358.20455169677734,396.3948974609375],[356.20455169677734,398.3948974609375],[352.20455169677734,398.3948974609375],[349.20455169677734,399.3948974609375],[344.20455169677734,402.3948974609375],[341.20455169677734,403.3948974609375],[338.20455169677734,404.3948974609375],[334.20455169677734,406.3948974609375],[329.20455169677734,407.3948974609375],[326.20455169677734,408.3948974609375],[321.20455169677734,408.3948974609375],[319.20455169677734,409.3948974609375],[315.20455169677734,411.3948974609375],[312.20455169677734,412.3948974609375],[306.20455169677734,413.3948974609375],[304.20455169677734,413.3948974609375],[302.20455169677734,414.3948974609375],[298.20455169677734,415.3948974609375],[293.20455169677734,417.3948974609375],[287.20455169677734,417.3948974609375],[284.20455169677734,418.3948974609375],[279.20455169677734,418.3948974609375],[275.20455169677734,418.3948974609375],[270.20455169677734,419.3948974609375],[268.20455169677734,419.3948974609375],[263.20455169677734,420.3948974609375],[255.20455169677734,420.3948974609375],[252.20455169677734,420.3948974609375],[245.20455169677734,420.3948974609375],[239.20455169677734,420.3948974609375],[232.20455169677734,420.3948974609375],[225.20455169677734,420.3948974609375],[217.20455169677734,420.3948974609375],[214.20455169677734,420.3948974609375],[208.20455169677734,420.3948974609375],[202.20455169677734,420.3948974609375],[196.20455169677734,420.3948974609375],[191.20455169677734,420.3948974609375],[188.20455169677734,420.3948974609375],[185.20455169677734,420.3948974609375],[181.20455169677734,420.3948974609375],[173.20455169677734,420.3948974609375],[169.20455169677734,418.3948974609375],[162.20455169677734,418.3948974609375],[156.20455169677734,417.3948974609375],[151.20455169677734,416.3948974609375],[143.20455169677734,413.3948974609375],[139.20455169677734,410.3948974609375],[129.20455169677734,408.3948974609375],[125.20455169677734,407.3948974609375],[118.20455169677734,404.3948974609375],[112.20455169677734,401.3948974609375],[106.20455169677734,398.3948974609375],[99.20455169677734,398.3948974609375],[98.20455169677734,396.3948974609375],[92.20455169677734,393.3948974609375],[89.20455169677734,391.3948974609375],[83.20455169677734,386.3948974609375],[79.20455169677734,384.3948974609375],[77.20455169677734,380.3948974609375],[71.20455169677734,377.3948974609375],[68.20455169677734,371.3948974609375],[65.20455169677734,368.3948974609375],[63.204551696777344,365.3948974609375],[60.204551696777344,358.3948974609375],[59.204551696777344,352.3948974609375],[57.204551696777344,347.3948974609375],[56.204551696777344,343.3948974609375],[55.204551696777344,338.3948974609375],[55.204551696777344,333.3948974609375],[54.204551696777344,328.3948974609375],[54.204551696777344,324.3948974609375],[54.204551696777344,319.3948974609375],[54.204551696777344,315.3948974609375],[54.204551696777344,310.3948974609375],[54.204551696777344,307.3948974609375],[54.204551696777344,302.3948974609375],[54.204551696777344,297.3948974609375],[55.204551696777344,290.3948974609375],[56.204551696777344,286.3948974609375],[58.204551696777344,282.3948974609375],[59.204551696777344,279.3948974609375],[59.204551696777344,275.3948974609375],[59.204551696777344,273.3948974609375],[59.204551696777344,268.3948974609375],[60.204551696777344,264.3948974609375],[62.204551696777344,259.3948974609375],[62.204551696777344,257.3948974609375],[64.20455169677734,252.3948974609375],[64.20455169677734,248.3948974609375],[65.20455169677734,243.3948974609375],[67.20455169677734,238.3948974609375],[69.20455169677734,232.3948974609375],[70.20455169677734,228.3948974609375],[71.20455169677734,226.3948974609375],[71.20455169677734,224.3948974609375],[71.20455169677734,219.3948974609375],[71.20455169677734,218.3948974609375],[72.20455169677734,213.3948974609375],[73.20455169677734,211.3948974609375],[73.20455169677734,207.3948974609375],[73.20455169677734,204.3948974609375],[74.20455169677734,200.3948974609375],[74.20455169677734,198.3948974609375],[75.20455169677734,193.3948974609375],[75.20455169677734,191.3948974609375],[77.20455169677734,187.3948974609375],[78.20455169677734,180.3948974609375],[78.20455169677734,177.3948974609375],[79.20455169677734,174.3948974609375],[79.20455169677734,169.3948974609375],[81.20455169677734,165.3948974609375],[81.20455169677734,163.3948974609375],[82.20455169677734,158.3948974609375],[82.20455169677734,156.3948974609375],[83.20455169677734,153.3948974609375],[84.20455169677734,151.3948974609375],[84.20455169677734,148.3948974609375],[84.20455169677734,145.3948974609375],[84.20455169677734,141.3948974609375],[84.20455169677734,139.3948974609375],[85.20455169677734,135.3948974609375],[85.20455169677734,131.3948974609375],[85.20455169677734,128.3948974609375],[85.20455169677734,125.3948974609375],[85.20455169677734,122.3948974609375],[85.20455169677734,118.3948974609375],[84.20455169677734,116.3948974609375],[84.20455169677734,113.3948974609375],[81.20455169677734,108.3948974609375],[81.20455169677734,106.3948974609375],[79.20455169677734,101.3948974609375],[79.20455169677734,100.3948974609375],[79.20455169677734,98.3948974609375],[78.20455169677734,96.3948974609375],[75.20455169677734,92.3948974609375],[73.20455169677734,90.3948974609375],[73.20455169677734,89.3948974609375],[72.20455169677734,88.3948974609375],[72.20455169677734,87.3948974609375],[72.20455169677734,87.3948974609375]]
            cone_blue = [[94.66,41.2],[127.86,29.6],[161.77,21.76],[194.2,18.39],[222.2,15.39],[248.2,15.39],[275.2,15.39],[311.89,19.53],[345.68,27.11],[378.3,44.3],[398.2,90.39],[394.4,126.94],[373.8,162.59],[333.75,185.59],[321.3,195.49],[310.35,209.47],[317.82,218.86],[325.28,221.25],[340.2,227.39],[372.5,240.92],[410.35,272.32],[423.2,311.39],[358.1,425.55],[327.28,435.54],[287.2,444.39],[255.2,447.39],[225.2,447.39],[196.2,447.39],[162.2,445.39],[123,431.99],[100.13,425.54],[27.2,310.39],[33.59,270.86],[39.14,242.37],[44.2,219.39],[48.73,188.1],[57.06,153.32],[59.01,128.85],[54.2,106.39]]
            cone_yellow = [[107.75,93.59],[134.55,83.19],[170.64,75.03],[194.2,72.39],[222.2,69.39],[248.2,69.39],[275.2,69.39],[306.52,73.26],[326.72,77.68],[330.6,130.19],[320.66,133.2],[283.11,157.3],[262.06,185.32],[340.2,281.39],[361.91,293.87],[362.06,296.47],[369.2,311.39],[370.2,343.39],[365.06,356.32],[353.11,371.3],[330.31,379.24],[303.13,387.25],[287.2,390.39],[255.2,393.39],[225.2,393.39],[196.2,393.39],[162.2,391.39],[155.4,388.79],[124.28,377.25],[100.49,365.65],[84.3,349.3],[81.68,333.1],[81.2,310.39],[84.82,287.93],[89.27,262.42],[98.2,219.39],[101.68,198.69],[105.35,177.47],[111.4,141.94],[108.2,106.39]]
            faulty_cones = []
        `;*/
        if (!(window as any).pyodide)
            (window as any).pyodide = await loadPyodide({
                indexURL: "https://cdn.jsdelivr.net/pyodide/v0.18.0/full/",
            });
        if (!this.pyodide) this.pyodide = (window as any).pyodide as Await<ReturnType<typeof loadPyodide>>;

        const code = await (await fetch("./python/main.py")).text();

        console.warn("BEFORE IMPORT");
        await this.pyodide.loadPackagesFromImports(code);
        console.warn("AFTER IMPORT");
        this.pythonLoading = false;
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
    drawArrow(from: readonly [number, number], offset: readonly [number, number], color: string) {
        let to = plus(from, offset);
        var headlen = 10; // length of head in pixels
        var dx = to[0] - from[0];
        var dy = to[1] - from[1];
        var angle = Math.atan2(dy, dx);
        this.context.beginPath();
        this.context.moveTo(from[0], from[1]);
        this.context.lineTo(to[0], to[1]);
        this.context.lineTo(to[0] - headlen * Math.cos(angle - Math.PI / 6), to[1] - headlen * Math.sin(angle - Math.PI / 6));
        this.context.moveTo(to[0], to[1]);
        this.context.lineTo(to[0] - headlen * Math.cos(angle + Math.PI / 6), to[1] - headlen * Math.sin(angle + Math.PI / 6));
        this.context.strokeStyle = color;
        this.context.stroke();
    }
    reset() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.distance = 0;
        this.nextDotTargetDistance = this.spacing;
        this.trackData.pylons = [];
        this.trackData.groundTruth = [];
        this.detection = {};

        this.name = "";
    }

    private groundTruthToBeAdded = [] as [number, number][];
    private freezeGroundTruth = false;

    canvasMouseDown(event: MouseEvent) {
        this.drawing = true;
        this.lastPos = this.getPos(event);
        this.groundTruthToBeAdded.push(this.lastPos.map((n) => Math.round(n * 100) / 100) as [number, number]);
        this.startPos = this.lastPos;

        if (this.name != "" && !this.name.includes("edited")) this.name += " (edited)";
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
                .split("\n")
                .map((r) => r.trim())
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

            if (!map.cone_blue) map.cone_blue = [];
            if (!map.cone_yellow) map.cone_yellow = [];
            if (!map.faulty_cones) map.faulty_cones = [];

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
    addMissingPressed() {
        let filtered = this.trackData.pylons.filter((d) => !d.hidden && !d.undetect);

        let cone_blue = filtered.filter((d) => d.color == "#0000FF").map((o) => [o.x, o.y] as [number, number]);
        let cone_yellow = filtered.filter((d) => d.color == "#FF0000").map((o) => [o.x, o.y] as [number, number]);
        let faulty_cones = this.trackData.pylons.filter((d) => d.undetect).map((o) => [o.x, o.y] as [number, number]);

        let deriveSpacing = (points: [number, number][]): number =>
            points
                .map((p, i, arr) => (arr[i + 1] ? d(p, arr[i + 1]) : 0))
                .slice(0, -1)
                .sort() //distances between consective points
                .median(); //take the median as estimated for the generating distance
        //derive spacing from map.cone_yellow, map.cone_blue
        this.derivedSpacingBlue = deriveSpacing(cone_blue);

        this.derivedSpacingRed = deriveSpacing(cone_yellow);

        this.derivedWidth = [
            ...cone_blue.map((point) => d(point, this.findClosestPoint(cone_yellow, point))),
            ...cone_yellow.map((point) => d(point, this.findClosestPoint(cone_blue, point))),
        ]
            .sort()
            .median();
        //derive width from map.cone_blue-map.cone_yellow

        this.addMissing(cone_yellow, cone_blue, this.derivedWidth, this.derivedSpacingRed, this.derivedSpacingBlue, "#0000AA", -1);
        this.addMissing(cone_blue, cone_yellow, this.derivedWidth, this.derivedSpacingBlue, this.derivedSpacingRed, "#AA0000", 1);
    }
    private derivedWidth = 0;
    private derivedSpacingRed = 0;
    private derivedSpacingBlue = 0;

    findClosestPoint(points: readonly [number, number][], point: readonly [number, number]): [number, number] {
        return points.reduce((a, b) => (d([a[0], a[1]], point) < d([b[0], b[1]], point) ? a : b));
    }
    addMissing(
        group1: [number, number][],
        group2: [number, number][],
        width: number,
        spacing1: number,
        spacing2: number,
        color: string,
        fac: number
    ) {
        for (let i = 1; i < group1.length - 1; i++) {
            if (d(group1[i], group1[i + 1]) > spacing1 * 2) continue;
            if (d(group1[i], group1[i - 1]) > spacing1 * 2) continue;

            let n = rot(norm(plus(min(group1[i], group1[i + 1]), min(group1[i - 1], group1[i]))));
            let add = plus(group1[i], mul(n, width * fac));

            this.drawArrow(group1[i], mul(n, width * fac), "pink");
            //this.drawArrow(group1[i], plus(min(group1[i], group1[i + 1]), min(group1[i - 1], group1[i])), "green");

            let closest = this.findClosestPoint(group2, add);
            if (d(add, closest) > spacing2 * 0.5) this.drawCircleRaw(add[0], add[1], 5, color);
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
    private pythonLoading = true;
    async calculatePython() {
        if (this.pythonLoading || this.pyodide == null) return;
        this.pythonLoading = true;

        try {
            let filtered = this.trackData.pylons.filter((d) => !d.hidden && !d.undetect);
            /* const data = await (
            await fetch(
                "http://localhost:3000?" +
                    new URLSearchParams({
                        b: JSON.stringify(filtered.filter((d) => d.color == "#0000FF").map((o) => [o.x, o.y])),
                        y: JSON.stringify(filtered.filter((d) => d.color == "#FF0000").map((o) => [o.x, o.y])),
                        f: JSON.stringify(this.trackData.pylons.filter((d) => d.undetect).map((o) => [o.x, o.y])),
                    })
            )
        ).text();*/
            this.pyodide.globals.set("args", {
                cone_blue: JSON.stringify(filtered.filter((d) => d.color == "#0000FF").map((o) => [o.x, o.y])),
                cone_yellow: JSON.stringify(filtered.filter((d) => d.color == "#FF0000").map((o) => [o.x, o.y])),
                faulty_cones: JSON.stringify(this.trackData.pylons.filter((d) => d.undetect).map((o) => [o.x, o.y])),
            });
            await this.pyodide.runPythonAsync("print(args)");

            await this.pyodide.runPythonAsync(`
            import sys
            from js import fetch
            async def fetch_and_decode(url):
                jsbuf = await (await fetch(url)).arrayBuffer()
                pybuf = bytearray(jsbuf.to_py())
                return pybuf

            with open('christofides.py', 'wb') as f:
                f.write(await fetch_and_decode("./python/christofides.py"))
            sys.path.insert(0, '.')
        `);
            console.warn("AFTER CODE1");
            const code = await (await fetch("./python/main.py")).text();
            console.log(await this.pyodide.runPythonAsync("__name__='__main__'\n" + code));
            console.warn("AFTER CODE2");
            const [blueDetected, yellowDetected, midLine] = this.pyodide.globals.get("result").toJs();
            this.output += `
            cone_blue_detected = ${JSON.stringify(blueDetected)}
            cone_yellow_detected = ${JSON.stringify(yellowDetected)}
            midLine = ${JSON.stringify(midLine)}`;
        } catch (e) {
            console.warn(e);
        } finally {
            this.pythonLoading = false;
        }
    }

    async openDemo(file: { path: string; name: string }) {
        this.reset();
        this.name = file.name;
        const text = await (await fetch(file.path)).text();
        let result = YAML.parse(text) as YAMLFile;
        this.loadYAMLFile(result);
    }
    async YAMLFilesChange(event: Event) {
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        var files = (event.target as HTMLInputElement).files!;
        console.log(files);
        let result = YAML.parse(await files[0].text()) as YAMLFile;
        this.loadYAMLFile(result);
    }
    loadYAMLFile(result: YAMLFile) {
        const { cones_left, cones_orange, cones_orange_big, cones_right } = result;

        console.log([cones_left, cones_orange, cones_orange_big, cones_right]);

        const parsedSets = [cones_left, cones_orange, cones_orange_big, cones_right].map((list) =>
            list.map((p) => p.split("\n").map((x) => parseFloat(x.trim().slice(1))))
        ); //parse numbers

        const list = parsedSets.flat();
        //normalize
        const [minX, maxX] = [list.map((p) => p[0]).min(), list.map((p) => p[0]).max()];
        const [minY, maxY] = [list.map((p) => p[1]).min(), list.map((p) => p[1]).max()];
        //const scale = Math.min(1 / (maxX - minX), 1 / (maxY - minY));
        const scale = Math.min(1 / (maxX - minX), 1 / (maxY - minY));
        const offset = [-minX, -minY] as const;

        const trackSets = parsedSets
            .map((list) => {
                return list.map((p) => mul(plus(p as [number, number], offset), scale));
            }) //scale to 500x500 with padding
            .map((list) =>
                list.map((p) => plus(mul(p as [number, number], 450).map((x) => Math.round(x * 100) / 100) as [number, number], [25, 25]))
            );

        trackSets.forEach((list, i) =>
            list.forEach((p) => {
                this.drawCircleRaw(p[0], p[1], 5, ["blue", "yellow", "orange", "red", "green"][i]);
            })
        );
        this.trackData.pylons = [
            ...trackSets[0].map(([x, y]) => ({ x, y, color: "#0000FF" })),
            ...trackSets[3].map(([x, y]) => ({ x, y, color: "#FF0000" })),
        ];
    }

    async JSONFilesChange(event: Event) {
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

        this.strokePolygon(this.detection.blueDetected || [], "#7777FF", 3, true, true);
        this.strokePolygon(this.detection.yellowDetected || [], "#FF7777", 3, true, true);
        this.strokePolygon(this.detection.midLine || [], "#00FF00", 5, true, true);

        this.strokePolygon(this.trackData.groundTruth, "#000000", 3, true, false);
    }
    strokePolygon(pointsArray: [number, number][], strokeColor: string, radius: number, stroke?: boolean, circles?: boolean) {
        if (pointsArray.length <= 0) return;
        this.context.beginPath();

        if (strokeColor) this.context.strokeStyle = strokeColor;
        if (stroke)
            for (let i = 0; i < pointsArray.length - 1; i++) {
                this.drawArrow(pointsArray[i], min(pointsArray[i + 1], pointsArray[i]), strokeColor);
                //this.context.lineTo(pointsArray[i][0] * scale + offset, pointsArray[i][1] * scale + offset);
            }
        this.context.stroke();
        if (circles)
            for (let i = 0; i < pointsArray.length; i++) {
                this.drawCircle(pointsArray[i][0], pointsArray[i][1], radius, strokeColor);
            }
    }
}

function d(p: readonly [number, number], p2: readonly [number, number]) {
    return Math.sqrt(Math.pow(p[0] - p2[0], 2) + Math.pow(p[1] - p2[1], 2));
}
function plus(p: readonly [number, number], p2: readonly [number, number]) {
    return [p[0] + p2[0], p[1] + p2[1]] as const;
}
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
function rot(p: readonly [number, number]) {
    return [p[1], -p[0]] as const;
}

declare global {
    interface Array<T> {
        median(): T;
        mean(): T;
        max(): T;
        min(): T;
    }
}

Array.prototype.median = function <T>(this: T[]): T {
    if (this.length == 0) throw new Error("Array.median invoced with empty array");
    if (this.length % 2 === 0) {
        let a = this[this.length / 2 - 1];
        let b = this[this.length / 2 - 1];
        if (typeof a != "number" || typeof b != "number") throw new Error("median values non numeric in array with even size");
        // Average Of Two Middle Numbers
        return ((a + b) / 2) as unknown as T;
    }
    return this[(this.length - 1) / 2];
};
Array.prototype.mean = function (this: number[]): number {
    var num = 0;
    for (var i = 0, l = this.length; i < l; i++) num += this[i];
    return num / this.length;
};
Array.prototype.max = function () {
    return Math.max.apply(null, this);
};

Array.prototype.min = function () {
    return Math.min.apply(null, this);
};
</script>

<style l>
canvas {
    box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
    cursor: crosshair;
}
input[type="range"][disabled].handle-red::-webkit-slider-thumb {
    background: #ad6868 !important;
}
input[type="range"][disabled].handle-blue::-webkit-slider-thumb {
    background: #6161b6 !important;
}
</style>
