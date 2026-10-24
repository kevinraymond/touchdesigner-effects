// Blob Track (touchdesigner-effects, MIT). Which boxes each part of the picture needs: the output
// cut into 64 x 36 tiles, each listing (as 64 bits, 16 per channel) the boxes whose outline,
// labels or links reach into it. draw.glsl then visits only those, so its cost follows what is
// near a pixel, not how many boxes there are.
// Inputs: 0 the box table (table.glsl); 1 the picture (the output's size).
// boxes.glsl comes before this.
out vec4 fragColor;

void main() {
    setup(uTD2DInfos[1].res.zw);
    vec2 tile = gRes / uTDOutputInfo.res.zw;
    vec2 tlo = floor(gl_FragCoord.xy) * tile, thi = tlo + tile;
    vec2 tc = 0.5 * (tlo + thi);
    float reach = 0.5 * length(tile) + gLw + 1.0;
    uint bits[4] = uint[4](0u, 0u, 0u, 0u);
    for (int i = 0; i < MAXB; i++) {
        if (i >= gN) break;
        vec2 c, hs; float e; int id; vec4 b, m, f;
        if (!boxAt(i, c, hs, e, id, b, m, f)) continue;
        vec2 lo, hi;
        footprint(c, hs, lo, hi);
        bool hit = all(lessThan(lo, thi)) && all(greaterThan(hi, tlo));
        for (int k = 0; k < 5; k++) {
            if (hit) break;
            float w;
            int j = linkOf(i, k, id, m, f, w);
            if (j < 0 || w <= 0.0) continue;
            vec2 a = c, d = T(j, 0).xy * gRes;
            vec2 pa = tc - a, ba = d - a;
            float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
            hit = length(pa - ba * h) <= reach;
        }
        if (hit) bits[i / 16] |= 1u << uint(i % 16);
    }
    fragColor = vec4(float(bits[0]), float(bits[1]), float(bits[2]), float(bits[3]));
}
