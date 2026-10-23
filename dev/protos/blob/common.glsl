// DEV ONLY (blob round 1): helpers shared by the overlay shaders. The builder prepends FONT.
// Glyph codes: 0-9 digits, 10-35 A-Z, 36 space, 37 '.', 38 ':', 39 '-', 40 '/', 41 '#',
// 42 '%', 43 '+', 44 '_', 45 '[', 46 ']', 47 '=', 48 '>', 49 '<'.
#define CH_SP 36
#define CH_DOT 37
#define CH_COLON 38
#define CH_DASH 39
#define CH_SLASH 40
#define CH_HASH 41
#define CH_X 33
#define CH_Y 34
#define CH_W 32
#define CH_H 17

// Lit (1) when font pixel p of glyph g is on; p from the cell's bottom-left, 5 x 7.
float glyphPix(int g, ivec2 p) {
    if (g < 0 || p.x < 0 || p.x > 4 || p.y < 0 || p.y > 6) return 0.0;
    int row = FONT[g * 7 + (6 - p.y)];
    return float((row >> (4 - p.x)) & 1);
}

int digitOf(int n, int place) {
    n = abs(n);
    for (int k = 0; k < place; k++) n /= 10;
    return n - (n / 10) * 10;
}

int hexOf(int n, int place) { return (n >> (4 * place)) & 15; }

float hash11(float n) { return fract(sin(n * 127.1 + 311.7) * 43758.5453); }
int ihash(int n) {
    n = (n << 13) ^ n;
    return (n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff;
}

float lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

// Distance from p to segment ab.
float segDist(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
    return length(pa - ba * h);
}

// Text cell geometry: glyphs are 5 x 7 font pixels on a 6 x 9 pitch.
// Returns the character index under px for a label of `len` chars whose bottom-left is o, or -1;
// gp is the font pixel inside that character.
int textCell(vec2 px, vec2 o, float scale, int len, out ivec2 gp) {
    vec2 q = (px - o) / scale;
    gp = ivec2(0);
    if (q.x < 0.0 || q.y < 0.0 || q.y >= 7.0 || q.x >= float(len * 6)) return -1;
    int ci = int(q.x) / 6;
    gp = ivec2(int(q.x) - ci * 6, int(q.y));
    return ci;
}

// 1 inside the label's backing plate (one font pixel of margin).
float plate(vec2 px, vec2 o, float scale, int len) {
    vec2 q = (px - o) / scale;
    return float(q.x >= -1.0 && q.y >= -1.0 && q.x < float(len * 6) && q.y < 8.0);
}
