// touchdesigner-effects (MIT), Pixel Art: each art pixel's palette color, the one nearest its superpixel's color
// (with P(c | s) at the final temperature, the paper's "the color that maximizes P(c | s)"), and the next nearest for
// Dither. For video (ours): once the palette follows the picture, a pixel keeps last frame's color until another is
// Hold Lab units nearer, so a superpixel sitting between two colors doesn't flip back and forth with the noise. Until the
// palette has all its colors, each art pixel shows its superpixel's own color, and then fades to the palette's as the
// palette fades in (palette.glsl), so the palette's splits never show.
// Inputs: 0 the superpixels' colors (colors.glsl), 1 the palette (palette.glsl), 2 last frame's colors (this
// shader's buffer 0).
// Out, per art pixel: buffer 0 the color it shows (Lab, palette.glsl's row 1) and which (1 + the color's number; 0 for
// none yet); buffer 1 the next nearest color as shown and how far between the two the superpixel sits, 0 at its own
// color to 0.5 halfway.
uniform vec4 uH;   // x Hold (Lab), y the grid's allocated size G
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];

void main() {
    ivec2 me = ivec2(gl_FragCoord.xy);
    vec4 x = texelFetch(sTD2DInputs[0], me, 0);
    vec4 state = PALETTE_STATE(1);
    if (x.a <= 0.0 || state.y < 0.5) {
        fragColor[0] = vec4(0.0);
        fragColor[1] = vec4(0.0);
        return;
    }
    float d1 = 1e30, d2 = 1e30;
    int k1 = -1, k2 = -1;
    for (int k = 0; k < COLORS; k++) {
        vec4 c = texelFetch(sTD2DInputs[1], ivec2(k, 3), 0);
        if (c.a <= 0.0) continue;
        float d = distance(x.rgb, c.rgb);
        if (d < d1) {
            d2 = d1;
            k2 = k1;
            d1 = d;
            k1 = k;
        } else if (d < d2) {
            d2 = d;
            k2 = k;
        }
    }
    if (k1 < 0) {
        fragColor[0] = vec4(0.0);
        fragColor[1] = vec4(0.0);
        return;
    }
    if (state.y > 1.5 && GRID_OK(2, uH.y)) {
        int kept = int(texelFetch(sTD2DInputs[2], me, 0).a + 0.5) - 1;
        if (kept >= 0 && kept != k1) {
            vec4 c = texelFetch(sTD2DInputs[1], ivec2(kept, 3), 0);
            float d = distance(x.rgb, c.rgb);
            if (c.a > 0.0 && d < d1 + uH.x) {
                d2 = d1;
                k2 = k1;
                d1 = d;
                k1 = kept;
            }
        }
    }
    if (k2 < 0) {
        k2 = k1;
        d2 = d1;
    }
    float shown = state.y > 1.5 ? texelFetch(sTD2DInputs[1], ivec2(1, 2), 0).x : 0.0;
    fragColor[0] = vec4(mix(x.rgb, texelFetch(sTD2DInputs[1], ivec2(k1, 1), 0).rgb, shown), float(k1 + 1));
    fragColor[1] = vec4(mix(x.rgb, texelFetch(sTD2DInputs[1], ivec2(k2, 1), 0).rgb, shown), d1 / max(d1 + d2, 1e-6));
}
