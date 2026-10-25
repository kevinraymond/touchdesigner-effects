// Datamosh (touchdesigner-effects, MIT): block matching, step 2 of 2. Per block, the
// candidate with the least cost; the zero offset gets a bonus, as encoders prefer "skip" blocks.
// Coarse level (uP.z = 0): rg is the integer offset at this level (content came from x + d), for
// the fine level to center on; one output pixel per block. Final level (uP.z = 1): a parabola
// through the costs either side of the best offset gives a sub-pixel estimate, quantized to
// quarter pixels at full size as H.264 does; rg is the block's vector in UV units with
// current(x) = previous(x - v), b its cost, and each block covers uQ.y x uQ.y output pixels.
// Inputs: 0 sets the output size; 1 the costs from bm_sad (each block a uQ.x x uQ.x tile);
// 2 the input, for its size (used at the final level).
uniform vec4 uP;   // x: R, y: zero bias, z: final (1/0), w: full-size pixels per level pixel
uniform vec4 uQ;   // x: tile size in the costs, y: output pixels per block
out vec4 fragColor;
void main() {
    int R = int(uP.x), D = 2 * R + 1;
    ivec2 B = ivec2(gl_FragCoord.xy) / max(int(uQ.y), 1);
    ivec2 o = B * int(uQ.x);
    ivec2 csz = ivec2(uTD2DInfos[1].res.zw);
    float best = 1e9; ivec2 bi = ivec2(R); vec2 bd = vec2(0.0);
    for (int y = 0; y < D; y++)
    for (int x = 0; x < D; x++) {
        ivec2 p = o + ivec2(x, y);
        if (p.x >= csz.x || p.y >= csz.y) continue;
        vec4 c = texelFetch(sTD2DInputs[1], p, 0);
        float s = c.r - (c.g == 0.0 && c.b == 0.0 ? uP.y : 0.0);
        if (s < best) { best = s; bi = ivec2(x, y); bd = c.gb; }
    }
    if (uP.z < 0.5) { fragColor = vec4(bd, best, 1.0); return; }
    vec2 sub = vec2(0.0);
    if (bd != vec2(0.0) && all(greaterThan(bi, ivec2(0))) && all(lessThan(bi, ivec2(D - 1)))
        && all(lessThan(o + bi + 1, csz))) {
        float c0 = texelFetch(sTD2DInputs[1], o + bi, 0).r;
        float l = texelFetch(sTD2DInputs[1], o + bi - ivec2(1, 0), 0).r;
        float r = texelFetch(sTD2DInputs[1], o + bi + ivec2(1, 0), 0).r;
        float b = texelFetch(sTD2DInputs[1], o + bi - ivec2(0, 1), 0).r;
        float t = texelFetch(sTD2DInputs[1], o + bi + ivec2(0, 1), 0).r;
        float dx = l - 2.0 * c0 + r, dy = b - 2.0 * c0 + t;
        sub.x = dx > 1e-6 ? clamp(0.5 * (l - r) / dx, -0.5, 0.5) : 0.0;
        sub.y = dy > 1e-6 ? clamp(0.5 * (b - t) / dy, -0.5, 0.5) : 0.0;
    }
    vec2 dfull = floor((bd + sub) * uP.w * 4.0 + 0.5) / 4.0;
    fragColor = vec4(-dfull / uTD2DInfos[2].res.zw, best, 1.0);
}
