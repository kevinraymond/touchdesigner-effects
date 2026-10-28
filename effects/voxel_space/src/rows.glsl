// touchdesigner-effects (MIT), Voxel Space: each row of the depth map's far baseline and how far above it the row
// reaches. A depth map is brightest at the bottom, where the floor runs up to the camera, so as heights it would make
// one long ramp; a floor is about as near all along a row, though, so the terrain is measured from each row's own far
// baseline (its 12th percentile), and the floor and the far wall lie flat while whatever stands in front of them
// stands up.
// Inputs: 0 nearness (r) and validity (g), from depth_near.glsl. Out (one pixel a band of rows): r the row's
// baseline, g its 97th percentile minus its baseline (how far it reaches), b the share of it with a reading. Every
// other pixel of the row is plenty for a percentile, and walking the whole row took 0.35 ms.
out vec4 fragColor;

#define BINS 64

float percentile(int hist[BINS], float n, float q) {
    float want = q * n, sum = 0.0;
    for (int b = 0; b < BINS; b++) {
        float c = float(hist[b]);
        if (sum + c >= want && c > 0.0) return (float(b) + (want - sum) / c) / float(BINS);
        sum += c;
    }
    return 1.0;
}

void main() {
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    int y = int((gl_FragCoord.y / uTDOutputInfo.res.w) * float(size.y));
    int hist[BINS];
    for (int b = 0; b < BINS; b++) hist[b] = 0;
    float n = 0.0;
    for (int x = 0; x < size.x; x += 2) {
        vec2 d = texelFetch(sTD2DInputs[0], ivec2(x, y), 0).rg;
        if (d.g < 0.5) continue;
        hist[min(int(d.r * float(BINS)), BINS - 1)]++;
        n += 1.0;
    }
    if (n < 1.0) {
        fragColor = vec4(0.0);
        return;
    }
    float base = percentile(hist, n, 0.12);
    fragColor = vec4(base, max(percentile(hist, n, 0.97) - base, 0.0), 2.0 * n / float(size.x), 1.0);
}
