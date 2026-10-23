// DEV ONLY (datamosh round 1). Block matching, step 1 of 2, written for tdlib: the cost of every
// (block, candidate offset) pair in parallel. Output pixel (x, y) is block (x / D, y / D) tried at
// offset (x % D, y % D) - R around a center, D = 2R + 1: the mean absolute luma difference over
// the block plus a 1 px apron. Inputs 0/1: current/previous luma at this level; 2 (fine level
// only): the coarse result, whose offset doubled is the center.
uniform vec4 uP;   // x: R, y: block px at this level, z: 1 = center on the coarse result
out vec4 fragColor;
void main() {
    ivec2 sz = ivec2(uTD2DInfos[0].res.zw);
    int R = int(uP.x), D = 2 * R + 1, bs = int(uP.y), n = bs + 2;
    ivec2 q = ivec2(gl_FragCoord.xy);
    ivec2 B = q / D;
    ivec2 d = q - B * D - R;
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
