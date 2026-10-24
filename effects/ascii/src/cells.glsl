// ASCII (touchdesigner-effects, MIT): one texel per glyph cell. Input 0 is the picture, input 1 the
// edge pass (edges.glsl, half resolution). Every edge texel in the cell votes for its direction,
// weighted by its edge weight.
// Out, 32-bit float: rgb the cell's mean color; a packs its edge as one integer (exact in a 32-bit
// float): winning bin * 65536 + the winner's share of the cell's area * 255 * 256 + the winner's
// share of all the cell's votes * 255.
uniform vec4 uCell;   // cell width, height, grid origin x, y (pixels of input 0; the origin centers the grid)
out vec4 fragColor;

void main() {
    vec2 cs = uCell.xy;
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 lo = uCell.zw + floor(gl_FragCoord.xy) * cs;   // the cell's lower-left corner

    vec3 sum = vec3(0.0);
    for (int j = 0; j < 4; j++)
        for (int i = 0; i < 4; i++) {
            vec2 p = clamp(lo + (vec2(i, j) + 0.5) * 0.25 * cs, vec2(0.5), res - 0.5);
            sum += texture(sTD2DInputs[0], p / res).rgb;
        }

    vec2 eres = uTD2DInfos[1].res.zw;
    vec2 k = eres / res;
    ivec2 e0 = ivec2(max(floor(lo * k), vec2(0.0)));
    ivec2 e1 = ivec2(min(ceil((lo + cs) * k), eres));
    vec4 votes = vec4(0.0);
    for (int y = e0.y; y < e1.y; y++)
        for (int x = e0.x; x < e1.x; x++) {
            vec2 e = texelFetch(sTD2DInputs[1], ivec2(x, y), 0).rg;
            votes[clamp(int(e.r * 4.0), 0, 3)] += e.g;
        }
    int best = 0;
    for (int b = 1; b < 4; b++)
        if (votes[b] > votes[best]) best = b;
    float n = float(max((e1.x - e0.x) * (e1.y - e0.y), 1));
    float total = votes.x + votes.y + votes.z + votes.w;
    int share = int(clamp(votes[best] / n, 0.0, 1.0) * 255.0 + 0.5);
    int coherence = int(clamp(votes[best] / max(total, 1e-6), 0.0, 1.0) * 255.0 + 0.5);
    fragColor = TDOutputSwizzle(vec4(sum / 16.0, float(best * 65536 + share * 256 + coherence)));
}
