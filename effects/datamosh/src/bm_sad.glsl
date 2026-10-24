// Datamosh-style (touchdesigner-effects, MIT): block matching, step 1 of 2. The cost of every
// (block, candidate offset) pair in parallel: each block owns a tile of uP.w x uP.w output pixels,
// and pixel (x, y) of its tile tries offset (x, y) - R around a center, for x, y < D = 2R + 1 (the
// rest of the tile is unused). The cost is the mean absolute luma difference over the block plus
// a 1 px apron. One fragment per pair, not per block, keeps the GPU busy (about 20 times faster
// on an M2 Pro). The tiles let the output size follow the input through the resolution menu,
// with no expression reading another operator's size (which made unused operators cook).
// Inputs: 0 luma now, 1 luma of the previous input frame, at this level; 2 (fine level only) the
// coarse result, one pixel per block, whose offset doubled is the center.
uniform vec4 uP;   // x: R, y: block size in pixels at this level, z: 1 = center on the coarse result, w: tile size
out vec4 fragColor;
void main() {
    ivec2 sz = ivec2(uTD2DInfos[0].res.zw);
    int R = int(uP.x), D = 2 * R + 1, bs = int(uP.y), tile = int(uP.w), n = bs + 2;
    ivec2 q = ivec2(gl_FragCoord.xy);
    ivec2 B = q / tile;
    ivec2 d = q - B * tile;
    if (d.x >= D || d.y >= D) { fragColor = vec4(1e9, 0.0, 0.0, 1.0); return; }
    d -= R;
    if (uP.z > 0.5) d += 2 * ivec2(texelFetch(sTD2DInputs[2], B, 0).rg);
    ivec2 o0 = B * bs - 1;
    float sad = 0.0;
    for (int j = 0; j < n; j++)
    for (int i = 0; i < n; i++) {
        ivec2 p = o0 + ivec2(i, j);
        sad += abs(texelFetch(sTD2DInputs[0], clamp(p, ivec2(0), sz - 1), 0).r
                 - texelFetch(sTD2DInputs[1], clamp(p + d, ivec2(0), sz - 1), 0).r);
    }
    fragColor = vec4(sad / float(n * n), vec2(d), 1.0);
}
