// ASCII (touchdesigner-effects, MIT): a glyph in every cell. Input 0 is the cells (cells.glsl),
// input 1 the glyph atlas a Text TOP draws from a system font, input 2 the automatic white point
// (stats.glsl). A cell with a clear edge gets the line glyph along it (| \ - /); the others get a
// glyph from the current set by brightness (each set ordered by ink, lightest first), and cells
// below the black point stay empty. The builder replaces the GLYPHS line below with the glyph
// tables and the 5 x 7 bitmap font (lib/font5x7.py).
uniform vec4 uCell;     // cell width, height, grid origin x, y
uniform vec4 uFont;     // 0 system font (atlas) or 1 bitmap 5x7; font size in pixels (atlas) or pixels per font pixel (bitmap)
uniform vec4 uTone;     // black point, gamma, automatic levels 0..1, backdrop 0..1
uniform vec4 uEdge;     // share of the cell one direction must hold, its share of all the cell's edges, edges on, loudness
uniform vec4 uLook;     // color mode (0 orange and blue, 1 source, 2 mono), mono ink r, g, b
uniform vec4 uGlyphs;   // glyph set (its menu index + sections), beat count, share of cells that change set on a beat
uniform vec4 uAudio;    // contrast pop 0..1 and reverse video 0..1 (both after the flash gate), build 0..1, level 0..1
uniform vec4 uRipple;   // a beat's ripple: how far out (0..1; 0 none), the half diagonal and the ring's width (frame heights), on
out vec4 fragColor;

//@GLYPHS

const vec3 ORANGE = vec3(1.0, 0.58, 0.16);
const vec3 BLUE = vec3(0.30, 0.56, 1.0);
const vec3 PALE = vec3(1.0, 0.92, 0.80);
const vec3 PAPER = vec3(0.02, 0.025, 0.04);
const float ADVANCE = 0.6;   // a monospaced glyph's width, in em (Courier New, Menlo, Consolas...)
const float CAP = 0.58;      // the height of capitals and digits, in em: centered in the cell

// MurmurHash3's 32-bit finalizer (Austin Appleby, public domain): a cell's dice roll for a beat.
float roll(ivec2 cell, float beat, uint salt) {
    uint h = uint(cell.x) * 0x9E3779B1u ^ uint(cell.y) * 0x85EBCA77u ^ (uint(beat) + salt) * 0xC2B2AE3Du;
    h ^= h >> 16; h *= 0x85EBCA6Bu; h ^= h >> 13; h *= 0xC2B2AE35u; h ^= h >> 16;
    return float(h) / 4294967295.0;
}

// How much glyph ch inks pixel `local` (pixels from the cell's lower-left corner) in the atlas:
// glyph ch sits in slot ch, left edge SLOT_X and baseline SLOT_Y from the slot's lower-left corner.
float atlasInk(int ch, vec2 local, vec2 cs) {
    float fs = uFont.y;
    ivec2 slot = ivec2(ch % ATLAS_COLS, ATLAS_ROWS - 1 - ch / ATLAS_COLS);
    ivec2 origin = ivec2(floor((cs - vec2(ADVANCE, CAP) * fs) * 0.5 + 0.5));   // the glyph's left edge and baseline in the cell
    ivec2 q = ivec2(floor(local)) - origin + ivec2(SLOT_X, SLOT_Y);
    if (q.x < 0 || q.y < 0 || q.x >= SLOT_W || q.y >= SLOT_H) return 0.0;
    return texelFetch(sTD2DInputs[1], slot * ivec2(SLOT_W, SLOT_H) + q, 0).r;
}

// The same from the 5 x 7 bitmap font: a cell is 6 x 9 font pixels, the glyph in its top-left 5 x 7
// after one empty row.
float bitmapInk(int ch, vec2 local) {
    ivec2 f = ivec2(floor(local / uFont.y));
    return glyph(BITMAP[ch], ivec2(f.x, 7 - f.y));
}

void main() {
    vec2 cs = uCell.xy;
    vec2 p = gl_FragCoord.xy - uCell.zw;
    ivec2 grid = ivec2(uTD2DInfos[0].res.zw);
    ivec2 cell = clamp(ivec2(floor(p / cs)), ivec2(0), grid - 1);
    vec2 local = p - vec2(cell) * cs;
    vec4 c = texelFetch(sTD2DInputs[0], cell, 0);
    int packed = int(c.a + 0.5);
    int dir = clamp(packed / 65536, 0, 3);
    float share = float((packed / 256) % 256) / 255.0;
    float coherence = float(packed % 256) / 255.0;
    float lum = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
    // In the ripple's ring? The cell's middle, in frame heights from the middle of the picture.
    vec2 res = uTDOutputInfo.res.zw;
    vec2 at = ((vec2(cell) + 0.5) * cs + uCell.zw - 0.5 * res) / res.y;
    bool ring = uRipple.w > 0.5 && uRipple.x > 0.0 && abs(length(at) - uRipple.x * uRipple.y) < 0.5 * uRipple.z;

    // Tone: levels (a build lowers the black point, so the darks fill in), then the contrast pop.
    float white = mix(1.0, texelFetch(sTD2DInputs[2], ivec2(0), 0).r, uTone.z);
    float black = uTone.x * (1.0 - 0.6 * uAudio.z);
    float l = pow(clamp((lum - black) / max(white - black, 0.02), 0.0, 1.0), uTone.y);
    l = mix(l, smoothstep(0.08, 0.75, l), uAudio.x);

    // Glyph: the line along a clear edge (loudness and a build make more cells qualify), else the ramp.
    float need = uEdge.x * (1.0 - 0.5 * uEdge.w * uAudio.w) * (1.0 - 0.4 * uAudio.z);
    bool edge = uEdge.z > 0.5 && l > 0.0 && share >= need && coherence >= uEdge.y;
    int ch = -1;
    if (edge) {
        ch = EDGE[dir];
    } else if (l > 0.0) {
        int set = int(uGlyphs.x) % SETS_N;
        if (ring || roll(cell, uGlyphs.y, 0u) < uGlyphs.z)
            set = (set + 1 + int(roll(cell, uGlyphs.y, 7u) * float(SETS_N - 1))) % SETS_N;
        int n = SET_LEN[set];
        ch = SETS[SET_START[set] + min(int(l * float(n)), n - 1)];
    }
    float ink = ch < 0 ? 0.0 : (uFont.x < 0.5 ? atlasInk(ch, local, cs) : bitmapInk(ch, local));

    // Color: brightness always follows the picture, so nothing rests on hue alone.
    int mode = int(uLook.x + 0.5);
    vec3 hue;
    if (mode == 0)
        hue = edge ? ORANGE : mix(BLUE, PALE, smoothstep(0.7, 1.0, l));
    else if (mode == 1)
        hue = c.rgb / max(max(c.r, c.g), max(c.b, 1e-3));
    else
        hue = uLook.yzw;
    // The ripple's ring takes the other accent color (in Mono only its glyphs change).
    if (ring && mode != 2)
        hue = edge || (mode == 1 && dot(hue, vec3(1.0, 0.0, -1.0)) > 0.0) ? BLUE : ORANGE;
    float bright = (edge ? 0.45 + 0.55 * sqrt(l) : 0.3 + 0.7 * l) * (1.0 + 0.3 * uAudio.x);
    vec3 paper = mix(PAPER, c.rgb * 0.45, uTone.w);
    vec3 col = mix(paper, hue * bright, ink);
    // A drop: reverse video in every cell that holds a glyph, its ink color as paper and the glyph cut out of it.
    if (ch >= 0)
        col = mix(col, mix(hue * max(bright, 0.45), paper, ink), uAudio.y);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
