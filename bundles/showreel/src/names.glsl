// Showreel (touchdesigner-effects, MIT). A name on a dark plate, in the library's 5 x 7 font.
// The builder writes NAMES (every name's glyphs, one after another), NAME_AT and NAME_LEN (where
// name k starts and how long it is) above this: name k is effect k's, in the View menu's order.
#define PAD 3      // font pixels of plate around the text
#define INK 0.9    // the text's brightness: below full white, like the library's other labels

// Name k's plate at q (pixels from the plate's bottom-left corner), s pixels per font pixel:
// x the text's ink, y the plate.
vec2 nameAt(int k, vec2 q, float s) {
    int len = NAME_LEN[k];
    vec2 size = vec2(float(len * 6 - 1 + 2 * PAD), float(7 + 2 * PAD)) * s;
    if (q.x < 0.0 || q.y < 0.0 || q.x >= size.x || q.y >= size.y) return vec2(0.0);
    ivec2 f = ivec2(floor(q / s)) - ivec2(PAD);
    if (f.x < 0 || f.y < 0 || f.y > 6) return vec2(0.0, 1.0);
    int ci = f.x / 6;
    if (ci >= len || f.x - ci * 6 > 4) return vec2(0.0, 1.0);
    return vec2(glyph(NAMES[NAME_AT[k] + ci], ivec2(f.x - ci * 6, 6 - f.y)), 1.0);
}

// The picture c at pixel px with name k drawn on its plate, the plate's bottom-left corner at o.
vec3 withName(vec3 c, int k, vec2 px, vec2 o, float s) {
    vec2 a = nameAt(k, px - o, s);
    c = mix(c, vec3(0.0), 0.6 * a.y);
    return mix(c, vec3(INK), a.x);
}

// The plate's height in pixels, to place it from the top.
float plateHeight(float s) { return float(7 + 2 * PAD) * s; }
