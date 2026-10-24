// Glitch (touchdesigner-effects, MIT). The picture from just before the current burst: it follows
// the input between bursts and holds still during one, for the blocks a burst freezes.
// Inputs: 0 the picture; 1 this TOP's previous output (a Feedback TOP).
uniform vec4 uBurst;   // x 1 during a burst
out vec4 fragColor;

void main() {
    fragColor = uBurst.x > 0.5 ? texture(sTD2DInputs[1], vUV.st) : texture(sTD2DInputs[0], vUV.st);
}
