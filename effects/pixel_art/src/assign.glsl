// touchdesigner-effects (MIT), Pixel Art: each of the picture's pixels joins a superpixel, one step of Gerstner et
// al.'s modified SLIC (after Achanta et al., "SLIC Superpixels", 2010). There is one superpixel per art pixel, and a
// pixel joins whichever of those around it minimizes
//     d = |its color - the superpixel's palette color| + m sqrt(N / M) |its place - the superpixel's center|,
// N superpixels in M pixels, so sqrt(N / M) = 1 / S. As in SLIC, a superpixel reaches only the pixels within S of its
// center (its 2S x 2S window); centers stay within half a cell of home, so they are among the 3 x 3 cells around a
// pixel's own, and its own cell's always reaches it. The color distance is to the palette color the superpixel shows,
// not its mean color: the paper's change to SLIC, which shapes the superpixels by the colors the art can show. m = 45
// (the paper's) keeps them about one cell big. Before the first palette, the place alone decides: a plain grid.
// Inputs: 0 the picture in Lab (lab.glsl), 1 last frame's centers (centers.glsl), 2 last frame's palette color of
// each superpixel (index.glsl).
// Out: rg which neighbor it joined, (dx + 1) / 2 and (dy + 1) / 2.
uniform vec4 uGrid;   // x Pixel Size, y the grid's allocated size G, z m
out vec4 fragColor;

void main() {
    ivec2 res = textureSize(sTD2DInputs[0], 0);
    int s = cell_size(res, uGrid.x, uGrid.y);
    ivec2 n = grid_size(res, s);
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 cell = p / s;
    vec3 lab = texelFetch(sTD2DInputs[0], p, 0).rgb;
    bool centers = GRID_OK(1, uGrid.y);
    bool colors = GRID_OK(2, uGrid.y);
    float wgt = uGrid.z / float(s);
    vec2 here = vec2(p) + 0.5;
    float best = 1e30;
    ivec2 pick = ivec2(0);
    for (int dy = -1; dy <= 1; dy++) {
        for (int dx = -1; dx <= 1; dx++) {
            ivec2 q = cell + ivec2(dx, dy);
            if (any(lessThan(q, ivec2(0))) || any(greaterThanEqual(q, n))) continue;
            vec2 center = (vec2(q) + 0.5) * float(s);
            if (centers) {
                vec4 c = texelFetch(sTD2DInputs[1], q, 0);
                if (c.w > 0.0 && c.z == float(s)) center = c.xy;
            }
            if (any(greaterThan(abs(here - center), vec2(float(s))))) continue;
            float dc = 0.0;
            if (colors) {
                vec4 c = texelFetch(sTD2DInputs[2], q, 0);
                if (c.a > 0.0) dc = distance(lab, c.rgb);
            }
            float d = dc + wgt * distance(here, center);
            if (d < best) {
                best = d;
                pick = ivec2(dx, dy);
            }
        }
    }
    fragColor = vec4(vec2(pick + 1) * 0.5, 0.0, 1.0);
}
