<template>
    <nav class="navbar navbar-dark bg-secondary d-flex p-0">
        <div class="container px-3 py-2">
            <a href="#" class="navbar-brand align-bottom router-link-active">TrackVisualizer</a>
        </div>
    </nav>
    <div class="container d-flex align-items-stretch justify-content-center flex-column">
        <div class="card card-default mt-5">
            <div class="card-header">Canvas</div>
            <div class="card-body">
                <TrackCanvas />
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

@Options({})
export default class App extends Vue {}
</script>

<style></style>
