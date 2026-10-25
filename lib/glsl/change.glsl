// touchdesigner-effects (MIT), shared by Datamosh and Fluid (lib/glsl, lib_glsl()): how much the
// input changed since the last frame this pass saw, per pixel at 1/8 size; an Analyze TOP averages
// it. A clip slower than the project (16 fps in 60) repeats each frame several times: a change of 0
// means "no new frame", and the effect then holds its last motion instead of measuring none (Datamosh
// holds its picture, Fluid keeps pushing with the last frame's motion).
// Inputs: 0 luma at 1/8 now, 1 this pass's previous output (Feedback TOP; g is the luma it saw).
// Out: r |change|, g the luma now (seen next frame), a follows the clock so this pass cooks every
// frame even when the input doesn't (a still picture, a camera between frames).
uniform float uTime;
out vec4 fragColor;
void main() {
    float now = texture(sTD2DInputs[0], vUV.st).r;
    float seen = texture(sTD2DInputs[1], vUV.st).g;
    fragColor = vec4(abs(now - seen), now, 0.0, fract(uTime));
}
