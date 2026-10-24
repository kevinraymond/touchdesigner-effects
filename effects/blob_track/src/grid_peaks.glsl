// Blob Track (touchdesigner-effects, MIT). GPU Grid detector, step 2 of 3: the cells that are
// peaks (above the threshold and higher than every cell within two), and how far around each
// (up to 3 cells) the cells stay above 60% of its score, which sizes its box.
// Inputs: 0 grid.glsl; 1 the picture (for its shape).
// Out: r the peak's score (0 where there is none), g and b its box's half width and height (cells).
uniform vec4 uPeak;   // x threshold, y min size, z max size (longer side, fraction of the picture's height)
out vec4 fragColor;

ivec2 G;
float score(ivec2 c) {
    if (any(lessThan(c, ivec2(0))) || any(greaterThanEqual(c, G))) return 0.0;
    return texelFetch(sTD2DInputs[0], c, 0).r;
}

int reach(ivec2 c, ivec2 dir, float floor_) {
    int n = 0;
    for (int k = 1; k <= 3; k++) {
        if (score(c + dir * k) < floor_) break;
        n = k;
    }
    return n;
}

void main() {
    G = textureSize(sTD2DInputs[0], 0);
    ivec2 c = ivec2(gl_FragCoord.xy);
    float s = score(c);
    fragColor = vec4(0.0);
    if (s < uPeak.x) return;
    for (int y = -2; y <= 2; y++) {
        for (int x = -2; x <= 2; x++) {
            if (x == 0 && y == 0) continue;
            float o = score(c + ivec2(x, y));
            if (o > s || (o == s && y * 5 + x < 0)) return;
        }
    }
    float hw = float(max(reach(c, ivec2(-1, 0), 0.6 * s), reach(c, ivec2(1, 0), 0.6 * s))) + 0.5;
    float hh = float(max(reach(c, ivec2(0, -1), 0.6 * s), reach(c, ivec2(0, 1), 0.6 * s))) + 0.5;
    float asp = uTD2DInfos[1].res.z / max(uTD2DInfos[1].res.w, 1.0);
    float side = max(2.0 * hw / float(G.x) * asp, 2.0 * hh / float(G.y));
    if (side < uPeak.y || side > uPeak.z) return;
    fragColor = vec4(s, hw, hh, 1.0);
}
