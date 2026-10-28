// touchdesigner-effects (MIT), Voxel Space: the height map. Each pixel's nearness above its row's far baseline
// (rows.glsl, a line fitted down the rows: below), over the tallest row's span (span.glsl), so the terrain
// stands 0 to 1 tall whatever the input. Orbit shows the picture as an island, so its heights rise from the sea over
// its outer 8% (a smoothstep) instead of ending in a cliff: a shore that rose steeply showed a little face at the first
// step inside it, which the steps cut into a sawtooth along the shore.
// Inputs: 0 nearness and validity, 1 rows.glsl, 2 span.glsl. Out: r the height, 0-1, g whether it had a reading.
uniform vec4 uR;   // x 1 for an island's shore (Orbit)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 d = texture(sTD2DInputs[0], uv).rg;
    // The baseline at this row: a straight line fitted to the rows' baselines over 3% of the height either side
    // (weighted least squares), read where it crosses this row. An average over them pulled the bottom rows'
    // baseline down the floor's ramp, where only rows above were there to average, and the floor along the bottom
    // edge stood up as a strip; a line follows the ramp to the edge. Over 1% the baselines jumped from row to row
    // where a desk or a screen filled them, and the terrain came out in horizontal terraces.
    float s0 = 0.0, s1 = 0.0, s2 = 0.0, b0 = 0.0, b1 = 0.0;
    for (int k = -6; k <= 6; k++) {
        float y = uv.y + 0.005 * float(k);
        if (y < 0.0 || y > 1.0) continue;
        vec4 r = texture(sTD2DInputs[1], vec2(0.5, y));
        float g = exp(-0.5 * float(k * k) / 9.0) * r.b, x = float(k);
        s0 += g; s1 += g * x; s2 += g * x * x;
        b0 += g * r.r; b1 += g * r.r * x;
    }
    float det = s0 * s2 - s1 * s1;
    float base = s0 <= 0.0 ? 0.0 : det > 1e-4 ? (b0 * s2 - b1 * s1) / det : b0 / s0;
    float span = max(texelFetch(sTD2DInputs[2], ivec2(0), 0).r, 0.2);
    float h = d.g < 0.5 ? 0.0 : clamp((d.r - base) / span, 0.0, 1.0);
    if (uR.x > 0.5) {
        vec2 size = vec2(textureSize(sTD2DInputs[0], 0));
        vec2 edge = min(uv, 1.0 - uv) * vec2(size.x / size.y, 1.0);
        h *= smoothstep(0.0, 0.08, min(edge.x, edge.y));
    }
    fragColor = vec4(h, d.g < 0.5 ? 0.0 : 1.0, 0.0, 1.0);
}
