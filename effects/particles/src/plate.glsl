// Particles (touchdesigner-effects, MIT). The empty room, for Find on Background: the picture as it
// was when Capture Background was last pressed, held until it is pressed again.
// Inputs: 0 the picture, small (small.glsl); 1 this TOP's last frame (a Feedback TOP).
// Out: rgb the empty room, a which capture it is (0: none yet).
uniform vec4 uPlate;   // x how many times Capture Background has been pressed
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec4 old = texelFetch(sTD2DInputs[1], p, 0);
    if (uPlate.x > 0.5 && abs(old.a - uPlate.x) > 0.5) {
        fragColor = vec4(texelFetch(sTD2DInputs[0], p, 0).rgb, uPlate.x);
        return;
    }
    fragColor = old;
}
