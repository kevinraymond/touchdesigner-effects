// touchdesigner-effects (MIT), Voxel Space: the heights eased toward the picture's with a leak, each frame a share of
// the way (most of it in a quarter of a second), as the colors are (colors.glsl), so the hills move with the land
// and a video's noise doesn't shake them. Where a depth camera got no reading the heights hold where they were.
// Inputs: 0 the height map (smoothed; g whether it had a reading), 1 this pass's last frame. Out: r the height, eased.
uniform vec4 uE;   // x seconds since the last frame, y the time it eases over
out vec4 fragColor;

void main() {
    vec2 now = texture(sTD2DInputs[0], vUV.st).rg;
    float h = now.r / max(now.g, 1e-3);                 // the blur spread no reading into its neighbors: undo that
    vec4 was = texture(sTD2DInputs[1], vUV.st);
    float follow = now.g < 0.5 ? 0.0 : 1.0 - exp(-uE.x / uE.y);
    fragColor = vec4(was.a < 0.5 ? h : mix(was.r, h, follow), 0.0, 0.0, 1.0);
}
