// Blob Track (touchdesigner-effects, MIT). The picture: the input in gray (or as it is, or dimmed),
// a thin box around everything tracked with a treatment inside, lines joining each box to its
// nearest neighbors, an ID above each box and its position below, in the library's 5 x 7 font.
// Audio (input 2, through audio_in): on beats some labels scramble, links spawn and boxes fill
// (the fill through the Flashing gate); Song Moments add a re-label on each bar, more and tighter
// links through a build, one gated turn of the whole picture on a drop and a re-lock of every box
// on a new section (builds, drops and sections come from Fosfora's signal).
// Inputs: 0 the picture; 1 the box table (table.glsl); 2 the local mean (small, gray, blurred);
// 3 the tiles (tiles.glsl). The builder puts the font (glyph(), G_* glyph numbers, WORDS) and
// boxes.glsl before this.
out vec4 fragColor;

// Colors for lines and text kept below full white, and labels without plates: whatever the overlay
// adds or moves changes a 20 x 20 pixel patch's luminance by less than WCAG's 0.1, so boxes and
// labels coming, going and gliding never count as flashes.
const vec3 ORANGE = vec3(1.0, 0.6, 0.18);
const vec3 BLUE = vec3(0.42, 0.68, 1.0);
const vec3 LINE = vec3(0.85);
const vec3 LINK = vec3(0.8, 0.84, 0.9);
const vec3 TEXT2 = vec3(0.55);

float lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

vec3 picture(vec3 c, float mode) {
    if (mode < 0.5) return vec3(smoothstep(0.02, 0.9, lum(c)));
    if (mode < 1.5) return c;
    return c * 0.45;
}

// Coverage of a line w pixels wide from a to b.
float segInk(vec2 p, vec2 a, vec2 b, float w) {
    vec2 lo = min(a, b) - w - 1.0, hi = max(a, b) + w + 1.0;
    if (any(lessThan(p, lo)) || any(greaterThan(p, hi))) return 0.0;
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
    return clamp(w * 0.5 + 0.5 - length(pa - ba * h), 0.0, 1.0);
}

int digit(int n, int place) {
    for (int k = 0; k < place; k++) n /= 10;
    return n % 10;
}

int idChar(int id, int ci) { return ci == 0 ? G_HASH : G_0 + digit(id % 10000, 4 - ci); }

int posChar(vec2 uv, int ci) {   // "X24 Y87": the center, in percent of the picture
    int x = clamp(int(uv.x * 100.0), 0, 99), y = clamp(int(uv.y * 100.0), 0, 99);
    if (ci == 0) return G_X;
    if (ci == 1) return G_0 + x / 10;
    if (ci == 2) return G_0 + x % 10;
    if (ci == 3) return G_SPACE;
    if (ci == 4) return G_Y;
    if (ci == 5) return G_0 + y / 10;
    return G_0 + y % 10;
}

// The character under px in a label of len characters whose bottom-left corner is o, drawn s
// pixels per font pixel; -1 when there is none. gp: the font pixel (x 0-4, y 0-6 top down).
int cellAt(vec2 px, vec2 o, float s, int len, out ivec2 gp) {
    vec2 q = floor((px - o) / s);
    gp = ivec2(0);
    if (q.x < 0.0 || q.y < 0.0 || q.y > 6.0 || q.x >= float(len * 6)) return -1;
    int ci = int(q.x) / 6;
    gp = ivec2(int(q.x) - ci * 6, 6 - int(q.y));
    return ci;
}

// A label character while it scrambles: any digit or letter, changing 10 times a second (drawn
// at half ink, so the changing glyphs don't flicker a patch of the picture).
int noiseChar(int seed, float t) { return G_0 + hashi(seed, int(t * 10.0)) % 36; }

// One label line's text: line 1 the box's number (or a word), line 2 its position. While scr is
// high its characters scramble, settling left to right as it falls.
struct Label { int line, len, id, wi; bool word; float scr; vec2 uv; float t; };

bool scrambled(Label l, int ci) { return l.scr > 1.0 - float(ci + 1) / float(l.len + 1); }

int labelGlyph(Label l, int ci) {
    if (scrambled(l, ci)) return noiseChar(l.id * (l.line == 1 ? 5 : 9) + ci, l.t);
    return l.line == 1 ? (l.word ? WORDS[l.wi * 4 + ci] : idChar(l.id, ci)) : posChar(l.uv, ci);
}

// Where font pixel q (from the label's bottom-left corner, y up) is lit: 1, or 0.5 while its
// character scrambles.
float labelInk(Label l, ivec2 q) {
    if (q.x < 0 || q.y < 0 || q.y > 6 || q.x >= l.len * 6) return 0.0;
    int ci = q.x / 6;
    return glyph(labelGlyph(l, ci), ivec2(q.x - ci * 6, 6 - q.y)) * (scrambled(l, ci) ? 0.5 : 1.0);
}

// The label whose bottom-left corner is o, s pixels per font pixel, at px: x its ink, y a dark
// outline one font pixel wide around it (legible on light pictures without a plate behind it).
vec2 labelAt(Label l, vec2 px, vec2 o, float s) {
    ivec2 q = ivec2(floor((px - o) / s));
    if (q.x < -1 || q.y < -1 || q.y > 7 || q.x > l.len * 6) return vec2(0.0);
    float ink = labelInk(l, q), halo = 0.0;
    for (int dy = -1; dy <= 1 && ink <= 0.0; dy++) {
        for (int dx = -1; dx <= 1; dx++) halo = max(halo, labelInk(l, q + ivec2(dx, dy)));
    }
    return vec2(ink, halo);
}

void main() {
    setup(uTDOutputInfo.res.zw);
    vec2 px = vUV.st * gRes;
    float s = gS, t = uLook2.w;
    vec3 accent = uLook2.z < 0.5 ? ORANGE : uLook2.z < 1.5 ? BLUE : vec3(1.0);
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 col = picture(src, uLook.z);
    float lwLink = max(1.0, gLw * 0.75);

    float insideAny = 0.0, edge = 0.0, link = 0.0, spawn = 0.0, halo = 0.0, ink1 = 0.0, ink2 = 0.0;
    int hit = -1;
    float hitArea = 1e12, hitFade = 0.0;
    vec2 hitC = vec2(0.0);
    // Only the boxes this pixel's tile lists (tiles.glsl).
    vec4 tile = texelFetch(sTD2DInputs[3], ivec2(vUV.st * vec2(textureSize(sTD2DInputs[3], 0))), 0);
    for (int w = 0; w < 4; w++) {
        uint bits = uint(tile[w] + 0.5);
        while (bits != 0u) {
            int i = w * 16 + findLSB(bits);
            bits &= bits - 1u;
            vec2 c, hs; float e; int id; vec4 b, m, f;
            if (!boxAt(i, c, hs, e, id, b, m, f)) continue;
            vec2 d = abs(px - c) - hs;
            float dm = max(d.x, d.y);
            if (dm < 0.0) {
                insideAny = max(insideAny, e);
                float area = hs.x * hs.y;
                if (area < hitArea) { hitArea = area; hit = i; hitC = c; hitFade = e; }
            }
            edge = max(edge, e * clamp(gLw * 0.5 + 0.5 - abs(dm + gLw * 0.5), 0.0, 1.0));
            for (int k = 0; k < 5; k++) {
                float lw_;
                int j = linkOf(i, k, id, m, f, lw_);
                if (j < 0 || lw_ <= 0.0) continue;
                // A link fades with both its ends.
                float ink = lw_ * e * smoothstep(0.0, 1.0, T(j, 2).x) * segInk(px, c, T(j, 0).xy * gRes, lwLink);
                if (k < 4) link = max(link, ink);
                else spawn = max(spawn, ink);
            }

            if (gLabels == 0) continue;
            if (abs(px.y - c.y) > hs.y + 13.0 * s || px.x < c.x - hs.x - 2.0 * s || px.x > c.x - hs.x + 44.0 * s) continue;
            // Line 1: the number, or a word (Labels: Words; and on every other bar with Song Moments).
            bool word = gLabels == 3 || (gMoments > 0.5 && (gBarN & 1) == 1);
            int wi = hashi(id, (gMoments > 0.5 ? gBarN : 0) + 17) % NWORDS;
            // How scrambled, 0-1: while the box fades in, on a beat (a quarter of the labels,
            // briefly), on a bar or a new section (all of them).
            float scr = 1.0 - e;
            if (uOn.x > 0.5 && (hashi(id + 11, gBeatN) & 3) == 0) scr = max(scr, gBeatEnv * gBeatEnv);
            scr = max(scr, max(gBarEnv, gSectionEnv * gSectionEnv * gSectionEnv));
            Label l = Label(1, word ? 4 : 5, id, wi, word, scr, b.xy, t);
            vec2 a = labelAt(l, px, floor(vec2(c.x - hs.x, c.y + hs.y + 3.0 * s)), s);
            ink1 = max(ink1, e * a.x);
            halo = max(halo, e * a.y);
            // Line 2: the position, under boxes tall enough to carry it.
            if (gLabels == 2 && hs.y * 2.0 >= 9.0 * s) {
                l.line = 2;
                l.len = 7;
                a = labelAt(l, px, floor(vec2(c.x - hs.x, c.y - hs.y - 10.0 * s)), s);
                ink2 = max(ink2, e * a.x);
                halo = max(halo, e * a.y);
            }
        }
    }

    // Inside the smallest box around this pixel: the treatment (Inside).
    int inside = int(uLook.w + 0.5);
    if (hit >= 0 && inside > 0) {
        vec3 tr;
        if (inside == 1) {
            tr = 1.0 - col;
        } else if (inside == 2) {
            float mean = texture(sTD2DInputs[2], vUV.st).r, l = lum(src);
            float ink = smoothstep(-0.01, 0.01, l - mean - 0.04);
            tr = mix(vec3(0.05 + 0.3 * smoothstep(mean - 0.15, mean + 0.15, l)), accent, ink);
        } else {
            tr = picture(texture(sTD2DInputs[0], (hitC + (px - hitC) * 0.5) / gRes).rgb, uLook.z);
        }
        col = mix(col, tr, hitFade);
    }
    // A flash (only ever through the Flashing gate): the box insides turn over on a beat
    // (Fill Boxes), the whole picture on a drop.
    col = mix(col, 1.0 - col, uFlash.x * (uFlash.y > 0.5 ? 1.0 : insideAny));
    float linkAlpha = min(1.0, 0.45 + 0.25 * uBeat.z + 0.3 * gBuild);
    col = mix(col, LINK, link * linkAlpha * (1.0 - insideAny));
    col = mix(col, accent, spawn * (1.0 - insideAny));
    col = mix(col, LINE, edge);
    // Labels: the outline only where the picture is darker than the text (where it helps), and the
    // gray position text fainter on bright pictures, so a label changes a patch's luminance by less
    // than WCAG's 0.1 wherever it appears or moves.
    float bg = dot(pow(max(col, 0.0), vec3(2.2)), vec3(0.2126, 0.7152, 0.0722));
    col = mix(col, col * 0.4, halo * 0.6 * (1.0 - smoothstep(0.25, 0.55, bg)));
    col = mix(col, accent, ink1 * 0.85);
    col = mix(col, TEXT2, ink2 * (1.0 - 0.5 * smoothstep(0.4, 0.8, bg)));
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
