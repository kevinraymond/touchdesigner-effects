// touchdesigner-effects (MIT), Scan Processor: the signal generators' phases, one pixel each (x = 0 for the sub bass's
// to 6 for the brilliance's), carried from frame to frame. A tone a little off a television's field rate draws stripes
// that creep up or down the screen, so each oscillator creeps at its own rate, the higher bands faster and alternately
// up and down, and faster still while its band is loud.
// Inputs: 0 the size (a 7 x 1 Constant TOP), 1 this pass's last frame (phase_fb).
// Out: r the phase in cycles, 0-1.
uniform vec4 uW0;   // the bands' levels, sub bass to mid
uniform vec4 uW1;   // upper mid, presence, brilliance, (strike)
uniform vec4 uD;    // seconds since the last frame, Speed
out vec4 fragColor;

const float DRIFT[7] = float[7](0.03, 0.07, -0.09, 0.11, -0.13, 0.15, -0.17);   // cycles a second at Speed 1

void main() {
    int k = int(gl_FragCoord.x);
    float level = k < 4 ? uW0[k] : uW1[k - 4];
    float p = texelFetch(sTD2DInputs[1], ivec2(k, 0), 0).r;
    fragColor = vec4(fract(p + DRIFT[k] * uD.y * (0.4 + level) * uD.x), 0.0, 0.0, 1.0);
}
