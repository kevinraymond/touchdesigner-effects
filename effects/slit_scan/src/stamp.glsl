// touchdesigner-effects (MIT), Slit-Scan: this cook's stamp, written into the stamps ring beside the picture and its
// flow, so frames.glsl can tell which slots hold which input frame and when it came.
// Inputs: 0 the input's pace (lib pace.glsl: r when the last new input frame came, g the gap between its frames,
// b a new frame now, a a cut now), 1 this pass's previous output (Feedback TOP).
// Out (2 x 1): pixel 0 r a serial counting cooks, g an id counting the input's new frames, b when this input frame
// came, a now (both seconds on the wrapped clock); pixel 1 r 1 when this input frame came at a cut, g the gap between
// the input's frames (seconds).
uniform vec4 uS;   // x: now (clock_seconds(); it also makes this pass cook every frame)
out vec4 fragColor;
const float SERIALS = 1048576.0;   // serials and ids wrap here, well inside a 32-bit float's whole numbers
void main() {
    vec4 pace = texelFetch(sTD2DInputs[0], ivec2(0), 0);
    vec4 prev = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    if (int(gl_FragCoord.x) == 1) {
        fragColor = vec4(pace.a, pace.g, 0.0, 1.0);
        return;
    }
    fragColor = vec4(mod(prev.r + 1.0, SERIALS), mod(prev.g + step(0.5, pace.b), SERIALS), pace.r, uS.x);
}
