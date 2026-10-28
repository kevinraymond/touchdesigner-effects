// touchdesigner-effects (MIT), Words: the distance from each cell to the subject's outline, by jump flooding (G. Rong
// and T.-S. Tan, "Jump Flooding in GPU with Applications to Voronoi Diagram and Distance Transform", I3D 2006): each
// pass looks at the cells a step away in eight directions and keeps the nearest outline cell any of them knows, the
// step halving from 128 cells to 1 over the passes (Passes 8: each pass reads the last one's output).
// Input: 0 the outline (seed.glsl), then the last pass. Out: rg the nearest outline cell found (-1: none yet), a 1.
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 n = textureSize(sTD2DInputs[0], 0);
    int step = 128 >> uTDPass;
    vec2 best = vec2(-1.0);
    float d = 1e9;
    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++) {
        ivec2 q = p + ivec2(i, j) * step;
        if (any(lessThan(q, ivec2(0))) || any(greaterThanEqual(q, n))) continue;
        vec2 s = texelFetch(sTD2DInputs[0], q, 0).rg;
        if (s.x < 0.0) continue;
        float e = distance(s, vec2(p));
        if (e < d) {
            d = e;
            best = s;
        }
    }
    fragColor = vec4(best, 0.0, 1.0);
}
