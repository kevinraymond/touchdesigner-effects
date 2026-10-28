// touchdesigner-effects (MIT), Pixel Art: the superpixels' colors through Gerstner et al.'s bilateral filter over the
// grid (after C. Tomasi and R. Manduchi, ICCV 1998), so a smooth gradient in the picture doesn't break into speckles.
// Then, for video (ours): each superpixel's color eased over Ease seconds where it changed a little (the picture's
// noise, which would flip art pixels back and forth between two colors), and taken at once where it changed a lot
// (a cut, an edge going by), so nothing trails.
// Inputs: 0 the superpixels' centers and mean colors (gather.glsl: two pixels each, the color second), 1 last frame's
// colors (this shader's).
// Out: Lab, importance (0 past the grid's used part).
uniform vec4 uGrid;   // y the grid's allocated size G, w the bilateral filter's color sigma (Lab)
uniform vec4 uEase;   // x seconds since the last frame, y Ease (s), z, w: a change under z Lab is eased, over w taken
out vec4 fragColor;

void main() {
    ivec2 me = ivec2(gl_FragCoord.xy);
    vec4 m = texelFetch(sTD2DInputs[0], ivec2(2 * me.x + 1, me.y), 0);
    if (m.a <= 0.0) {
        fragColor = vec4(0.0);
        return;
    }
    int g = int(uGrid.y);
    vec3 sum = vec3(0.0);
    float weight = 0.0;
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            ivec2 q = me + ivec2(dx, dy);
            if (q.x < 0 || q.y < 0 || q.x >= g || q.y >= g) continue;
            vec4 nb = texelFetch(sTD2DInputs[0], ivec2(2 * q.x + 1, q.y), 0);
            if (nb.a <= 0.0) continue;
            vec3 d = nb.rgb - m.rgb;
            float w = exp(-0.5 * float(dx * dx + dy * dy) - dot(d, d) / (2.0 * uGrid.w * uGrid.w));
            sum += nb.rgb * w;
            weight += w;
        }
    }
    vec3 color = sum / weight;
    if (GRID_OK(1, uGrid.y)) {
        vec4 last = texelFetch(sTD2DInputs[1], me, 0);
        if (last.a > 0.0) {
            float k = 1.0 - exp(-uEase.x / max(uEase.y, 1e-3));
            k = mix(k, 1.0, clamp((distance(color, last.rgb) - uEase.z) / (uEase.w - uEase.z), 0.0, 1.0));
            color = mix(last.rgb, color, k);
        }
    }
    fragColor = vec4(color, m.a);
}
