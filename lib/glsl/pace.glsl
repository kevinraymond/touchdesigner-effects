// touchdesigner-effects (MIT), shared by Fluid and VHS + CRT (lib/glsl, flow_speed()): the input's
// pace, one pixel. When the last new input frame came and how long the input takes between frames,
// smoothed: a 16 fps clip in a 60 fps project brings a frame every third or fourth frame, and the
// optical flow measures the movement over that whole gap, so speed.glsl divides by it to get a speed.
// Inputs: 0 the clock (lib clock.glsl: r new frame, g cut), 1 this pass's previous output
// (Feedback TOP). Out: r when the last new frame came (seconds), g the gap between frames
// (seconds), b new frame now (0/1), a cut now (0/1).
uniform vec4 uP;   // x: seconds now (it also makes this pass cook every frame), y: longest gap that counts
out vec4 fragColor;
void main() {
    vec4 clock = texelFetch(sTD2DInputs[0], ivec2(0), 0);
    vec4 prev = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    float last = prev.r, gap = prev.g;
    if (clock.r > 0.5) {
        float g = clamp(uP.x - last, 1.0 / 240.0, uP.y);
        gap = gap > 0.0 ? mix(gap, g, 0.3) : g;
        last = uP.x;
    }
    fragColor = vec4(last, gap, clock.r, clock.g);
}
