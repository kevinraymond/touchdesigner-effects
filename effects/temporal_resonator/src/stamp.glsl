// touchdesigner-effects (MIT), Temporal Resonator: this cook's stamp. The string's state goes into its ring a cook
// late (through a Feedback TOP, which breaks the loop), and so does this stamp into the stamps ring beside it, so a
// slot's stamp says which cook made the state in it and when; taps.glsl finds the moments one beat back by them.
// Inputs: 0 the input's clock (lib clock.glsl: r a new input frame, g a cut), 1 this pass's previous output (Feedback
// TOP: black, alpha 0, on its first frame).
// Out (2 x 1): pixel 0 r a serial counting cooks, g when this cook ran (seconds on the wrapped clock), b 1 when the
// string starts again here (the first cook, after a pause, or at a cut), a 1; pixel 1 r the seconds since the last
// cook (0 when it starts again).
uniform vec4 uS;   // x now (clock_seconds(); it also makes this pass cook every frame), y the longest pause the string
                   // rings through (s), z the clock's wrap (CLOCK)
out vec4 fragColor;
const float SERIALS = 1048576.0;   // serials wrap here, well inside a 32-bit float's whole numbers
void main() {
    vec4 clock = texelFetch(sTD2DInputs[0], ivec2(0), 0);
    vec4 prev = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    float dt = mod(uS.x - prev.g + uS.z, uS.z);
    float again = (prev.a < 0.5 || dt > uS.y || clock.g > 0.5) ? 1.0 : 0.0;
    if (int(gl_FragCoord.x) == 1) {
        fragColor = vec4(again > 0.5 ? 0.0 : dt, 0.0, 0.0, 1.0);
        return;
    }
    fragColor = vec4(mod(prev.r + 1.0, SERIALS), uS.x, again, 1.0);
}
