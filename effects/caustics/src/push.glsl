// touchdesigner-effects (MIT), Caustics: how the picture's movement pushes the water. Where the picture changed since
// its last frame (lib optical_flow's luma at a quarter size), the water is pushed up or down by the change, so what
// moves through the picture leaves a wake. Only on a new input frame (a slow clip repeats frames), and never at a cut,
// which would slam the whole pool at once. A Blur TOP then spreads it into broad swells: pushed finely, the water
// ripples in short, steep waves that focus light hard, and they flashed (2 flashes a second on the dancer where the
// clip has 1; board #4671).
// Inputs: 0 the luma now (lum4), 1 the luma of the input's last frame (lum4p), 2 the input's clock (lib clock.glsl:
// r a new input frame, g a cut).
// Out: r the push (the change in luma, 0 when nothing new came).
out vec4 fragColor;
void main() {
    vec4 clock = texelFetch(sTD2DInputs[2], ivec2(0), 0);
    float now = texture(sTD2DInputs[0], vUV.st).r;
    float before = texture(sTD2DInputs[1], vUV.st).r;
    float fresh = clock.r > 0.5 && clock.g < 0.5 ? 1.0 : 0.0;
    fragColor = vec4(fresh * (now - before), 0.0, 0.0, 1.0);
}
