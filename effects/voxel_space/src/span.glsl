// touchdesigner-effects (MIT), Voxel Space: how far the tallest row reaches above its baseline, eased over a second
// and a half, so the terrain's peaks come out about as tall whether they come from a depth map (people a half of its
// range above the floor) or from the picture's brightness (the whole range).
// Inputs: 0 rows.glsl, 1 this pass's last frame. Out: r the span, eased.
uniform vec4 uS;   // x seconds since the last frame
out vec4 fragColor;

void main() {
    int rows = textureSize(sTD2DInputs[0], 0).y;
    float m = 0.0;
    for (int y = 0; y < rows; y++) {
        vec4 r = texelFetch(sTD2DInputs[0], ivec2(0, y), 0);
        if (r.b > 0.25) m = max(m, r.g);
    }
    vec4 was = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    float s = was.a < 0.5 ? m : mix(was.r, m, 1.0 - exp(-uS.x / 1.5));
    fragColor = vec4(s, 0.0, 0.0, 1.0);
}
