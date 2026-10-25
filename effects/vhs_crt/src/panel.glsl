// VHS + CRT (touchdesigner-effects, MIT). What the flat screens share, pasted in front of lcd_state.glsl,
// lcd.glsl, plasma.glsl, eink_state.glsl and eink.glsl: the panel's pixel pitch, its cells, and an ordered dither.
// A panel's pixel is three cells side by side, red, green and blue, Mask Size pixels wide at 720 high; each
// shows one value over the whole cell, the signal where the cell's middle is (the panel's scaler).
#define GAMMA 2.2

// The panel's pixel pitch, in output pixels.
float pitch(float maskSize, vec2 res) { return max(maskSize * res.y / 720.0, 2.0); }

// Where the signal is read for the cell under p (output pixels): the middle of its cell, in UV.
vec2 cellUV(vec2 p, float P, vec2 res) { return (floor(p / P) + 0.5) * P / res; }

// How much of [a, b] (in pitches) a stripe from lo to hi in every pitch covers, 0-1: the exact share, so
// cells a pixel or two wide don't alias.
float stripeTo(float x, float lo, float hi) { return floor(x) * (hi - lo) + clamp(fract(x) - lo, 0.0, hi - lo); }
float stripe(float a, float b, float lo, float hi) { return (stripeTo(b, lo, hi) - stripeTo(a, lo, hi)) / (b - a); }

// The light each color's cells give the output pixel at frag, mean 1 over the panel: each cell lit over gx of its
// width and gy of its height from its corner, dark beyond (the black matrix, the ribs), so a cell a whole number of
// pixels across shows its gap as one sharp dark line. Only part of the pattern is kept, the rest is even light:
// color of the colors' stripes, about as much as a CRT's mask shows, so no output pixel is ever one pure color
// (the red guard then has little to do), and gap of the dark lines between rows, which hold no color.
vec3 cells(vec2 frag, float P, float gx, float gy, float color, float gap) {
    float a = (frag.x - 0.5) / P, b = (frag.x + 0.5) / P, w = gx / 3.0;
    vec3 cx;
    for (int k = 0; k < 3; k++)
        cx[k] = stripe(a, b, float(k) / 3.0, float(k) / 3.0 + w) / w;
    float cy = stripe((frag.y - 0.5) / P, (frag.y + 0.5) / P, 1.0 - gy, 1.0) / gy;
    return mix(vec3(1.0), cx, color) * mix(1.0, cy, gap);
}

// A 4 x 4 ordered (Bayer) dither threshold in 0-1.
float bayer4(ivec2 p) {
    const int M[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
    return (float(M[(p.y & 3) * 4 + (p.x & 3)]) + 0.5) / 16.0;
}
