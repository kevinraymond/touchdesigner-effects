// Showreel (touchdesigner-effects, MIT). Grid view: the input and every effect side by side in
// COLS x ROWS cells (left to right from the top), packed together as one block of 16:9 cells, as
// wide as the picture allows and centered, so the cells touch and any spare room is one band
// around the block; each picture fit whole into its cell, its name on a plate in the top-left
// corner (Labels). The builder writes N_TILES, COLS, ROWS, tileRes()
// and tile() above this: a sampler can't be chosen by a variable, so tile(t, uv) reads input t
// through a chain of constant indices.
// Inputs: 0 the input picture; 1 to N_TILES - 1 each effect's output.
uniform vec4 uLook;   // x Labels (0 or 1)
out vec4 fragColor;

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    float w = min(res.x / float(COLS), res.y / float(ROWS) * 16.0 / 9.0);
    vec2 cell = vec2(w, w * 9.0 / 16.0);
    vec2 block = cell * vec2(float(COLS), float(ROWS));
    vec2 b0 = 0.5 * (res - block);     // the block's bottom-left corner
    vec2 q = px - b0;
    int col = int(floor(q.x / cell.x));
    int row = int(floor((block.y - q.y) / cell.y));
    int t = row * COLS + col;
    vec3 c = vec3(0.0);
    if (col >= 0 && col < COLS && row >= 0 && row < ROWS && t < N_TILES) {
        // The picture's rectangle in its cell: as large as fits, centered.
        vec2 pr = tileRes(t);
        float pa = pr.x / max(pr.y, 1.0), ca = cell.x / cell.y;
        vec2 size = pa > ca ? vec2(cell.x, cell.x / pa) : vec2(cell.y * pa, cell.y);
        vec2 o = b0 + vec2(float(col) * cell.x, block.y - float(row + 1) * cell.y) + 0.5 * (cell - size);
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
