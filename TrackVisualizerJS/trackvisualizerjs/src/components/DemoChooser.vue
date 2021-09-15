<template>
    <transition name="modal">
        <div class="modal-mask" v-if="showModal">
            <div class="modal-wrapper" @click.self="showModal = false">
                <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Choose Demo Track</h5>
                            <button type="button" class="btn-close p-3" @click="showModal = false"></button>
                        </div>
                        <div class="modal-body row" style="max-height: 80vh; overflow: auto">
                            <div class="col-12 col-md-6 col-lg-4 col-xl-3" v-for="track in tracks" :key="track" @click="select(track)">
                                <div class="card mb-4">
                                    <img class="card-img-top" :src="track.img" @error="track.img = 'https://demofree.sirv.com/nope-not-here.jpg'" />
                                    <div class="card-body">
                                        <h6 class="card-text">{{ track.name }}</h6>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </transition>
    <button @click="showModal = true" class="btn btn-primary my-2 me-4">Open Demo Track...</button>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

@Options({})
export default class DemoChooser extends Vue {
    private showModal = false;
    private tracks = [
        "acceleration",
        "FSG",
        "skidpad",
        "track_1",
        ...Array(100)
            .fill(0)
            .map((_, i) => `random_track_${("00" + i).slice(-3)}`),
    ].map((track) => ({ name: track, img: `./YAML/${track}.png`, path: `./YAML/${track}.yaml` }));

    select(track: { path: string; name: string }) {
        this.showModal = false;
        this.$emit("fileSelected", track);
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
