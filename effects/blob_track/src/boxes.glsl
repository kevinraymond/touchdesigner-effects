// Blob Track (touchdesigner-effects, MIT). Shared by tiles.glsl and draw.glsl, so the tiles list
// exactly what the picture draws: the uniforms, the box table and each box's shape and links.
// The builder defines TABLE, the input the box table (table.glsl) is on.
uniform vec4 uLook;    // x line width, y label size (pixels at 720 high), z Picture (0 gray, 1 original, 2 dimmed), w Inside (0 none, 1 invert, 2 threshold, 3 zoom)
uniform vec4 uLook2;   // x Labels (0 off, 1 ID, 2 ID and position, 3 words), y Links (0 off, 1 nearest, 2 two nearest), z Accent (0 orange, 1 blue, 2 white), w time (s)
uniform vec4 uBeat;    // x beat envelope (1 on a beat, falling to 0), y beat count, z level 0-1, w source (3 Fosfora)
uniform vec4 uSong;    // x bar envelope (0.3 s), y bar count, z build 0-1, w section envelope (1.5 s)
uniform vec4 uFlash;   // x flash envelope (through the Flashing gate), y 1 when that flash is a drop's, z drop envelope (1.5 s), w section count
uniform vec4 uOn;      // x Scramble Labels, y Spawn Links, z Fill Boxes, w Song Moments

#define MAXB 64
vec4 T(int i, int r) { return texelFetch(sTD2DInputs[TABLE], ivec2(i, r), 0); }

uint uhash(uint x) {
    x ^= x >> 16; x *= 0x7feb352du;
    x ^= x >> 15; x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}
int hashi(int a, int b) { return int(uhash(uint(a) * 1664525u + uint(b) * 1013904223u + 12345u) & 0x7fffffffu); }

// Set by setup(): the output's size, line width and label scale in pixels, the beat state.
vec2 gRes;
float gLw, gS, gMoments, gBeatEnv, gBarEnv, gBuild, gSectionEnv, gDropEnv, gW1, gW2, gW34;
int gN, gLabels, gBeatN, gBarN;

void setup(vec2 res) {
    gRes = res;
    float ps = res.y / 720.0;
    gLw = max(1.0, uLook.x * ps);
    gS = max(1.0, floor(uLook.y * ps + 0.5));
    gLabels = int(uLook2.x + 0.5);
    gMoments = uOn.w;
    gBeatEnv = uBeat.x;
    gBeatN = int(uBeat.y + 0.5);
    gBarN = int(uSong.y + 0.5);
    gBarEnv = uSong.x * gMoments;
    gBuild = uSong.z * gMoments;
    gSectionEnv = uSong.w * gMoments;
    gDropEnv = uFlash.z * gMoments;
    int links = int(uLook2.y + 0.5);
    // Links: the nearest neighbors (Links); a build adds the 3rd and 4th, a drop shows them all.
    gW1 = max(links >= 1 ? 1.0 : 0.0, gDropEnv);
    gW2 = max(links >= 2 ? 1.0 : 0.0, gDropEnv);
    gW34 = max(gBuild, gDropEnv);
    gN = int(T(0, 1).w + 0.5);
}

// Box i: center and half size in pixels, how far it has faded in (0-1, eased), its label ID.
// False when the slot is empty. A box locks on: it closes in from a little larger as it appears,
// and again on a new section.
bool boxAt(int i, out vec2 c, out vec2 hs, out float e, out int id, out vec4 b, out vec4 m, out vec4 f) {
    b = T(i, 0); m = T(i, 1); f = T(i, 2);
    c = b.xy * gRes;
    hs = max(b.zw * gRes * 0.5, vec2(3.0 * gRes.y / 720.0));
    e = smoothstep(0.0, 1.0, f.x);
    id = int(m.x + 0.5);
    hs *= 1.0 + 0.25 * (1.0 - e) + 0.4 * gSectionEnv;
    return f.x > 0.0;
}

// Box i's link k (0-3 the nearest neighbors, 4 the partner a beat gives it): the box it goes to
// (-1 for none) and how strong it is.
int linkOf(int i, int k, int id, vec4 m, vec4 f, out float w) {
    w = 0.0;
    if (k == 0 && m.y >= 0.0) { w = gW1; return int(m.y); }
    if (k == 1 && m.z >= 0.0) { w = gW2; return int(m.z); }
    if (k == 2 && f.z >= 0.0) { w = gW34; return int(f.z); }
    if (k == 3 && f.w >= 0.0) { w = gW34; return int(f.w); }
    // On a beat a quarter of the boxes reach for a random partner; the line fades over the beat.
    if (k == 4 && uOn.y > 0.5 && gN > 1 && gBeatEnv > 0.0 && (hashi(id, gBeatN) & 3) == 0) {
        int j = hashi(id * 7 + 3, gBeatN) % gN;
        if (j != i) { w = gBeatEnv; return j; }
    }
    return -1;
}

// The rectangle box i and its labels cover (pixels).
void footprint(vec2 c, vec2 hs, out vec2 lo, out vec2 hi) {
    float pad = gLw + 1.0;
    lo = c - hs - vec2(2.0 * gS, 13.0 * gS) - pad;
    hi = vec2(max(c.x + hs.x, c.x - hs.x + 44.0 * gS), c.y + hs.y + 13.0 * gS) + pad;
}
