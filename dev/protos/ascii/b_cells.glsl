// DEV ONLY (ASCII round 1), variant B, pass 2: one output pixel per cell. Every edge pixel in the
// cell votes for one of four directions, weighted by its edge weight. Out: mean luminance, the
// winning direction (0 |, 1 \, 2 -, 3 /), the winner's share of the cell, all edges' share.
uniform vec2 uCell;
out vec4 fragColor;
void main() {
    ivec2 res = ivec2(uTD2DInfos[0].res.zw);
    ivec2 cell = ivec2(gl_FragCoord.xy);
    ivec2 cs = ivec2(uCell);
    vec4 votes = vec4(0.0);
    float lum = 0.0, edge = 0.0;
    for (int j = 0; j < cs.y; j++)
        for (int i = 0; i < cs.x; i++) {
            ivec2 p = ivec2(min(cell.x * cs.x + i, res.x - 1), max(res.y - 1 - (cell.y * cs.y + j), 0));
            vec4 e = texelFetch(sTD2DInputs[0], p, 0);
            lum += e.a;
            if (e.z > 0.0 && dot(e.xy, e.xy) > 1e-8) {
                float a = mod(atan(e.y, e.x), 3.14159265);        // edges have no sign
                int b = int(floor(a / 0.78539816 + 0.5)) % 4;     // 0, 45, 90, 135 degrees
                votes[b] += e.z;
                edge += e.z;
            }
        }
    int best = 0;
    for (int b = 1; b < 4; b++)
        if (votes[b] > votes[best]) best = b;
    float n = float(cs.x * cs.y);
    fragColor = vec4(lum / n, float(best), votes[best] / n, edge / n);
}
