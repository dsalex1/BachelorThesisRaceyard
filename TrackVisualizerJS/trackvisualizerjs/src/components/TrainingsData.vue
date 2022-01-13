<template>
    <transition name="modal">
        <div class="modal-mask" v-if="showModal">
            <div class="modal-wrapper" @click.self="showModal = false">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Training Data PNGs</h5>
                            <button type="button" class="btn-close p-3" @click="showModal = false"></button>
                        </div>
                        <div v-if="this.trainingDataPNGs.length>0" class="modal-body row mt-0" style="max-height: 80vh; overflow: auto">
                            <div class="col-12 mb-3 d-grid">
                                <button v-if="!downloadLoading" class="btn btn-primary d-block" @click="download">Download Images + Labels</button>
                                <div v-else class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                            </div>
                            <div class="col-12 col-md-6 col-lg-4 col-xl-3 text-center pb-4" v-for="img,i in trainingDataPNGs" :key="img.img">
                                Frame {{i}}/{{trainingDataPNGs.length}}
                                <img class="w-100" :src="img.img">
                                {{img.labels.map(curv=>curv.distance+":"+Math.round(curv.curvature*10000)/10000).join("; ")}}
                            </div>
                        </div>
                        <div v-else class="modal-body">no trainings data loaded or generated yet</div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
    <button @click="showModal = true" class="btn btn-secondary my-2 me-4">Show Training data...</button>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";
import { Prop, Watch } from "vue-property-decorator";
import JSZip from 'jszip';
import { saveAs } from 'file-saver';

@Options({})
export default class TrainingsData extends Vue {
    public showModal = false;

    @Prop()
    public trainingDataPNGs:{img:string,labels:{distance: number;curvature: number;}[]}[]=[];

    @Watch("trainingDataPNGs")
    show(){
        this.showModal=true;
    }

    public downloadLoading=false;
    download(){
        this.downloadLoading=true;
        var zip = new JSZip();

        zip.file("labels.json", JSON.stringify(
            this.trainingDataPNGs.map(({labels})=>(labels.sort((a,b)=>a.distance>b.distance?1:-1).map(s=>s.curvature)))
            ,null,2));
        
        var img = zip.folder("images")!;
        for (let i=0;i<this.trainingDataPNGs.length;i++)
            img.file(`Frame${("0000"+i).slice(-5)}.png`, this.trainingDataPNGs[i].img.split("data:image/png;base64,")[1], {base64: true});

        zip.generateAsync({type:"blob"}).then(function(content) {
            saveAs(content, "TrainingDataRosyard.zip");
        });
        this.downloadLoading=false;
    }
} 
</script>

<style>
.modal-mask {
    position: fixed;
    z-index: 9998;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: table;
}

.modal-wrapper {
    display: table-cell;
    vertical-align: middle;
}

.modal-container {
    width: 300px;
    margin: 0px auto;
    padding: 20px 30px;
    background-color: #fff;
    border-radius: 2px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.33);
    font-family: Helvetica, Arial, sans-serif;
}

.modal-header h3 {
    margin-top: 0;
    color: #42b983;
}

.modal-body {
    margin: 20px 0;
}

.modal-default-button {
    display: block;
    margin-top: 1rem;
}

.modal-enter-active,
.modal-leave-active {
    transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
    opacity: 0;
}
</style>
