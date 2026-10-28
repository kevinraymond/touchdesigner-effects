// touchdesigner-effects (MIT), Pixel Art: Gerstner et al.'s Laplacian smoothing of the superpixels' centers. Each
// moves 40% of the way to the average of its 4 neighbors, which keeps the superpixels in rows and columns like the
// art's pixels (SLIC alone drifts toward a hexagonal grid and bends the picture's features); a missing neighbor at the
// edge counts as one cell further on. Each center stays within half a cell of its home, so its 2S x 2S window always
// reaches the pixels of its own cell and lies within the 3 x 3 cells around it.
// Inputs: 0 the superpixels' centers and colors (gather.glsl: two pixels each, the center first).
// Out: x, y the center in pixels, S, 1 (0 past the grid's used part).
uniform vec4 uGrid;   // y the grid's allocated size G, z how far toward the neighbors (0.4)
out vec4 fragColor;

bool used(ivec2 q) {
    int g = int(uGrid.y);
    return q.x >= 0 && q.y >= 0 && q.x < g && q.y < g && texelFetch(sTD2DInputs[0], ivec2(2 * q.x + 1, q.y), 0).a > 0.0;
}

void main() {
    ivec2 me = ivec2(gl_FragCoord.xy);
    if (!used(me)) {
        fragColor = vec4(0.0);
        return;
    }
    vec4 c = texelFetch(sTD2DInputs[0], ivec2(2 * me.x, me.y), 0);
    float s = c.w;
    const ivec2 SIDES[4] = ivec2[4](ivec2(1, 0), ivec2(-1, 0), ivec2(0, 1), ivec2(0, -1));
    vec2 around = vec2(0.0);
    for (int k = 0; k < 4; k++) {
        ivec2 q = me + SIDES[k];
        around += used(q) ? texelFetch(sTD2DInputs[0], ivec2(2 * q.x, q.y), 0).xy : c.xy + vec2(SIDES[k]) * s;
    }
    vec2 center = c.xy + uGrid.z * (around * 0.25 - c.xy);
    vec2 home = (vec2(me) + 0.5) * s;
    fragColor = vec4(clamp(center, home - 0.5 * s, home + 0.5 * s), s, 1.0);
}
