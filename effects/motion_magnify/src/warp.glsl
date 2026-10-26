// touchdesigner-effects (MIT), Motion Magnify: the picture moved further. Each part of the picture is taken from where
// its displacement says, so a part that has moved d from where it rests is drawn at d times (1 + Amount) from there.
// Swaying wider sweeps a red edge across more of the picture, and a red near WCAG's saturated-red line crosses it each
// time (the red flowers swaying: 2 red flashes a second with Flashing Off, the clip 1), so the red guard (lib
// red_guard.glsl) keeps every red shown short of that line, as Slit-Scan's does.
// Inputs: 0 the picture, 1 the displacement to move it by (guard.glsl: rg UV units, at a quarter size, read smoothly).
// Out: the picture, moved.
out vec4 fragColor;

void main() {
    vec2 a = texture(sTD2DInputs[1], vUV.st).rg;
    vec4 c = texture(sTD2DInputs[0], vUV.st - a);
    fragColor = vec4(pow(redGuard(pow(max(c.rgb, 0.0), vec3(2.2))), vec3(1.0 / 2.2)), c.a);
}
