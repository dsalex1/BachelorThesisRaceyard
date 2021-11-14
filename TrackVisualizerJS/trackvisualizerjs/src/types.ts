
export interface Position {
    x: number;
    y: number;
    z: number;
}

export interface Orientation {
    x: number;
    y: number;
    z: number;
    w: number;
}
export interface Header {
    seq: number;
    stamp: {
        secs: number;
        nsecs: number;
    };
    frame_id: string;
}

export interface SlamMap {
    header: Header;
    height: number;
    width: number;
    fields: {
        name: string;
        offset: number;
        datatype: number;
        count: number;
    }[];
    is_bigendian: boolean;
    point_step: number;
    row_step: number;
    data: number[];
    is_dense: boolean;
}

export interface SlamCar {
    header: Header;
    car_state: {
        x: number;
        y: number;
        theta: number;
    };
}

export interface SlamDebugMap {
    positions: Position[];
    covariances: {
        covariance: number[];
    }[];
    colors: number[];
    groundTruth?: {
        x: number;
        y: number;
    }[];
}

export interface SlamDebugParticles {
    header: Header;
    poses: {
        position: Position;
        orientation: Orientation;
    }[];
}

export interface BagData {
    "/slam/map": SlamMap;
    "/slam/car": SlamCar;
    "/slam/debug/map": SlamDebugMap;
    "/slam/debug/particles": SlamDebugParticles;
}