// Showreel (touchdesigner-effects, MIT). Grid view: the input and every effect side by side in
// COLS x ROWS cells (left to right from the top), each picture fit whole into its cell, its name
// on a plate in the top-left corner (Labels). The builder writes N_TILES, COLS, ROWS, tileRes()
// and tile() above this: a sampler can't be chosen by a variable, so tile(t, uv) reads input t
// through a chain of constant indices.
// Inputs: 0 the input picture; 1 to N_TILES - 1 each effect's output.
uniform vec4 uLook;   // x Labels (0 or 1)
out vec4 fragColor;

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    vec2 cell = res / vec2(float(COLS), float(ROWS));
    int col = min(int(px.x / cell.x), COLS - 1);
    int row = min(int((res.y - px.y) / cell.y), ROWS - 1);
    int t = row * COLS + col;
    vec3 c = vec3(0.0);
    if (t < N_TILES) {
        // The picture's rectangle in its cell: as large as fits, centered.
        vec2 pr = tileRes(t);
        float pa = pr.x / max(pr.y, 1.0), ca = cell.x / cell.y;
        vec2 size = pa > ca ? vec2(cell.x, cell.x / pa) : vec2(cell.y * pa, cell.y);
        vec2 o = vec2(float(col) * cell.x, res.y - float(row + 1) * cell.y) + 0.5 * (cell - size);
        vec2 uv = (px - o) / size;
        if (all(greaterThanEqual(uv, vec2(0.0))) && all(lessThan(uv, vec2(1.0)))) c = tile(t, uv).rgb;
        if (uLook.x > 0.5) {
            float s = max(1.0, floor(2.0 * res.y / 720.0 + 0.5));
            vec2 corner = o + vec2(8.0 * s / 2.0, size.y - plateHeight(s) - 8.0 * s / 2.0);
            c = withName(c, t, px, corner, s);
        }
    }
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
