// Reaction-Diffusion (touchdesigner-effects, MIT): what moved in the last moments, at the grid's size, for Grow On
// Movement: how much the picture's brightness changed since last frame, held and fading over uM.y seconds, so the
// pattern keeps growing on what moved for a while after it stops, and a video slower than TouchDesigner's frame rate
// (which repeats each of its frames) keeps what its last new frame moved.
// Inputs: 0 the picture at the grid's size, 1 the same last frame, 2 this pass last frame (r).
// Out: r the change, 0-1.
uniform vec4 uM;   // x the frame step (s), y how long a change lasts (s)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    float d = abs(luma(texture(sTD2DInputs[0], uv).rgb) - luma(texture(sTD2DInputs[1], uv).rgb));
    float last = texture(sTD2DInputs[2], uv).r * exp(-uM.x / uM.y);
    fragColor = vec4(max(last, d), 0.0, 0.0, 1.0);
}
