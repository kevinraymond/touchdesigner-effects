// touchdesigner-effects (MIT), Pixel Art: how strongly each superpixel belongs to each palette entry, the first half
// of the "associate" step of mass-constrained deterministic annealing (K. Rose, "Deterministic annealing for
// clustering, compression, classification, regression, and related optimization problems", Proc. IEEE 86(11), 1998),
// as Gerstner et al. use it:
//     P(c | s) = P(c) exp(-|m_s - c|^2 / T) / Z_s,
// with T the palette's temperature. This pass finds each superpixel's largest exponent and Z_s (relative to it), so
// totals.glsl can take any one entry's P(c | s) without summing over every entry again. Before the palette starts, every
// superpixel belongs wholly to entry 0, which gives the picture's mean and spread to start from.
// Inputs: 0 the superpixels' colors (colors.glsl), 1 last frame's palette (palette.glsl).
// Out: x the largest exponent, y Z_s, a 1 (0 past the grid's used part).
out vec4 fragColor;

void main() {
    vec4 x = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    if (x.a <= 0.0) {
        fragColor = vec4(0.0);
        return;
    }
    vec4 state = PALETTE_STATE(1);
    if (state.y < 0.5) {
        fragColor = vec4(0.0, 1.0, 0.0, 1.0);
        return;
    }
    float t = max(state.x, 1e-3);
    float top = -1e30;
    for (int e = 0; e < ENTRIES; e++) {
        vec4 c = texelFetch(sTD2DInputs[1], ivec2(e, 0), 0);
        if (c.a <= 0.0) continue;
        vec3 d = x.rgb - c.rgb;
        top = max(top, log(c.a) - dot(d, d) / t);
    }
    float z = 0.0;
    for (int e = 0; e < ENTRIES; e++) {
        vec4 c = texelFetch(sTD2DInputs[1], ivec2(e, 0), 0);
        if (c.a <= 0.0) continue;
        vec3 d = x.rgb - c.rgb;
        z += exp(log(c.a) - dot(d, d) / t - top);
    }
    fragColor = vec4(top, z, 0.0, 1.0);
}
