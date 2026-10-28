// touchdesigner-effects (MIT), Words: where every word goes, kept from frame to frame. A compute shader, one workgroup
// of 1024 invocations, each holding one word's slot.
//
// Placing is Wordle's (J. Feinberg 2008; F. Viegas, M. Wattenberg and J. Feinberg, "Participatory Visualization with
// Wordle", InfoVis 2009): one word at a time, at the biggest size it fits, at the best free spot, never on a word
// already placed. The test is on the grid of cells (cells.glsl): each row of cells is a few 32-bit masks in shared
// memory, one bit a cell, so a word's box fits where its rows' bits are clear in the occupancy and in its size's mask
// of cells it may not cover. Every invocation tests its share of the spots at every size at once, and the best one
// wins by an atomic maximum on a key that puts size first, then how good the spot is.
//   Cloud     words only on the subject (Shape From, grown by Spread), the best spot the deepest inside its distance
//             field: ShapeWordle's idea (Y. Wang et al., "ShapeWordle: Tailoring Wordles using Shape-aware
//             Archimedean Spirals", TVCG 2020) of spiraling out from the shape's deepest point. The most frequent
//             words come first and may be biggest, each word once; then repeats fill in, smaller.
//   Portrait  the whole picture, the words in the text's order, each where the picture's detail allows its size
//             (big words on flat areas, small ones on the features), first spots first in reading order.
//   Lines     the text in lines that run around the subject's outline, ring after ring, after Hebrew micrography
//             and R. Maharik et al., "Digital Micrography" (SIGGRAPH 2011): the lines are the level sets of the
//             distance to the outline (without a subject, the distance from the top: a page). Each word lies along its
//             line, turned to it and upright, the words in the text's order, written on along the line from the last
//             word placed as long as there is room (a few reads, no search); where there isn't, the best free spot
//             just after another word, then on the lines nearest the subject.
// Kept from frame to frame (after EdWordle, Y. Wang et al., TVCG 2018, which moves only the words an edit disturbs):
// a word of Cloud rides the picture's motion (Follow), one of Lines follows its line, one of Portrait stays where it is
// and the picture moves under it (riding a dancer, white words flashed where she moved). One that runs into an older
// one is pushed off it (a word of Lines along its line), and one still on it, or out of its region, for more than HOLD
// seconds fades out. New words fill what is free, a few a frame (Fill Speed), each fading in. In Portrait and Lines a
// word fading out leaves its place free at once, so a new one fades in over it rather than leave a dark hole in the
// page; in Cloud it keeps its place until it is gone (there its next copy, or another word, landed on it as it faded).
// A cut changes only the picture under the words (fading them all out and in again flashed the whole picture): the
// ones that no longer fit go, as ever.
//
// Inputs: 0 the last frame's slots (this pass's output, a Feedback TOP), 1 the cells with the subject steadied
// (region.glsl), 2 the subject's signed distance field (field.glsl: in cells, negative inside; r slowed for Lines, g as
// it is), 3 the words (a pixel each; rows x, y, w, asc, desc, count, rank, fpx), 4 their ink in the atlas
// (ink.glsl), 5 the order (order: a word index a pixel, 1024 x 4, -1 past the end), 6 the motion (rg pixels per second
// at its own size), 7 Lines' lines (rings.glsl: the slowed field and its slope, read filtered).
// Out SLOTS x 4: row 0 each word's ink box (middle x, y, width, height in the picture's pixels), row 1 (word, level,
// alpha, state: 1 shown or fading in, -1 fading out, 0 a free slot), row 2 (seconds out of its region, angle, age in
// seconds, its line for Lines); row 3 pixel 0 (the next word of the order, Lines: 1 while its text runs on, seconds
// since a search found no room, 0),
// pixel 1 (Lines: where the text ends, x, y, its direction, its line).
#define SLOTS 1024
#define LEVELS 8
#define ROWU 5                         // masks a row: 160 cells
#define MAXROWS 160
#define MASK (MAXROWS * ROWU)
#define MEM (MASK * (LEVELS + 1))      // the occupancy, then a mask a level
#define NONE 0xFFFFFFFFu
#define OUTSIDE 0.15                   // a word may lie this share out of its region before it counts as out
#define TOUCH 0.2                      // words overlap past this share of the smaller one's height to count as touching
#define SPACE 0.12                     // room kept beside a word, a share of its line's height (a word space is 0.25)
#define LINE_SPACE 0.18                // Lines: the same, so words written on along a line keep a word space between
#define LEAD 0.04                      // room kept above and below it
#define PUSH 0.5                       // how much of an overlap a word is pushed out of each frame: pushed out of all
                                       // of it, a word between two older ones jumps to the other side and back every
                                       // frame (a flash); half settles it between them
#define LEAVE 0.5                      // a word goes in this share of Fade (it comes in over all of it)
#define TRIES 3                        // words in a row that find no room end this frame's filling
#define IDLE 0.25                      // once a frame finds no room, look again only when a word leaves or after this
                                       // long (the search is most of the cost, and a full picture has no room)
#define RING 1.15                      // Lines: from one line to the next, in lines' heights
#define DRIFT 0.35                     // Lines: how far a word's ends may stray from its line, in lines
#define TURN 0.866                     // Lines: a word whose line turns more than 30 degrees under it is out
#define STATE 0
#define CELLS 1
#define FIELD 2
#define VOCAB 3
#define INK 4
#define ORDER 5
#define MOTION 6
#define RINGS 7
layout (local_size_x = SLOTS) in;

uniform vec4 uGrid;   // x, y the picture's size (pixels), z Layout (0 Cloud, 1 Portrait, 2 Lines), w levels
uniform vec4 uSize;   // x Smallest, y Largest (pixels: a line's height), z Detail, w Spread (cells)
uniform vec4 uTime;   // x this frame's step (s), y Fade (s), z hold (s), w words to place this frame
uniform vec4 uMove;   // x Follow (0-1)

shared uint sMem[MEM];
shared uint sKey;
shared uint sSlot;
shared uint sPick;
shared uint sCount;
shared uint sDetail;
shared uint sTokens;
shared uint sLive;                     // how many slots hold a word shown (or fading in), listed in sMem from 5120
shared uint sShown[32];                // the words on screen, a bit each
shared uint sFreed;                    // a word started to leave this frame

int GW, GH, NL, MODE;
vec2 CELL;                             // a cell's size in pixels
bool ANY;                              // the subject was found

float levelSize(int L) {
    return NL <= 1 ? uSize.x : uSize.x * pow(uSize.y / uSize.x, float(L) / float(NL - 1));
}

// The room a word of level L keeps around its ink, each side (pixels).
vec2 roomOf(float L) {
    return vec2(MODE == 2 ? LINE_SPACE : SPACE, LEAD) * levelSize(int(L + 0.5));
}

// The bits of mask word k (cells 32k to 32k + 31) that columns c0 to c1 - 1 cover.
uint span(int c0, int c1, int k) {
    int a = max(c0 - 32 * k, 0);
    int b = min(c1 - 32 * k, 32);
    if (b <= a) return 0u;
    uint hi = b >= 32 ? NONE : ((1u << uint(b)) - 1u);
    return hi & ~((1u << uint(a)) - 1u);
}

// Is the box of cells [c0, c1) x [r0, r1) free in the occupancy and allowed for level L?
bool fits(int c0, int c1, int r0, int r1, int L) {
    int base = MASK * (1 + L);
    for (int r = r0; r < r1; r++)
        for (int k = c0 >> 5; k <= (c1 - 1) >> 5; k++)
            if (((sMem[r * ROWU + k] | sMem[base + r * ROWU + k]) & span(c0, c1, k)) != 0u) return false;
    return true;
}

// How many cells of the box level L may not cover.
int forbidden(int c0, int c1, int r0, int r1, int L) {
    int base = MASK * (1 + L), n = 0;
    for (int r = r0; r < r1; r++)
        for (int k = c0 >> 5; k <= (c1 - 1) >> 5; k++)
            n += bitCount(sMem[base + r * ROWU + k] & span(c0, c1, k));
    return n;
}

void take(int c0, int c1, int r0, int r1) {
    for (int r = max(r0, 0); r < min(r1, GH); r++)
        for (int k = max(c0, 0) >> 5; k <= (min(c1, GW) - 1) >> 5; k++)
            atomicOr(sMem[r * ROWU + k], span(max(c0, 0), min(c1, GW), k));
}

bool taken(ivec2 c) {
    if (c.x < 0 || c.y < 0 || c.x >= GW || c.y >= GH) return false;
    return (sMem[c.y * ROWU + (c.x >> 5)] & (1u << uint(c.x & 31))) != 0u;
}

// A turned box (middle p, half sizes h, direction u along it): is every cell whose middle lies in it free (Lines)?
// With mark, take them instead. The box is a strip along the word's middle, so lines next to each other never meet.
bool turned(vec2 p, vec2 h, vec2 u, bool mark) {
    vec2 v = vec2(-u.y, u.x);
    vec2 ext = abs(u) * h.x + abs(v) * h.y;
    ivec2 lo = ivec2(floor((p - ext) / CELL)), hi = ivec2(ceil((p + ext) / CELL));
    if (!mark && (lo.x < 0 || lo.y < 0 || hi.x > GW || hi.y > GH)) return false;
    for (int r = max(lo.y, 0); r < min(hi.y, GH); r++)
        for (int c = max(lo.x, 0); c < min(hi.x, GW); c++) {
            vec2 q = (vec2(c, r) + 0.5) * CELL - p;
            if (abs(dot(q, u)) > h.x || abs(dot(q, v)) > h.y) continue;
            if (mark) atomicOr(sMem[r * ROWU + (c >> 5)], 1u << uint(c & 31));
            else if (taken(ivec2(c, r))) return false;
        }
    return true;
}

// The cells a box of pixels touches (it may reach past the grid).
ivec4 cellsOf(vec4 box) {
    vec2 lo = (box.xy - 0.5 * box.zw) / CELL, hi = (box.xy + 0.5 * box.zw) / CELL;
    return ivec4(floor(lo + 0.02), ceil(hi - 0.02));
}

// The signed distance to the subject's outline at a cell, in cells (negative inside): as it is for Cloud, slowed for
// Lines (field.glsl).
float fieldAt(ivec2 c) {
    vec4 f = texelFetch(sTD2DInputs[FIELD], clamp(c, ivec2(0), ivec2(GW - 1, GH - 1)), 0);
    return MODE == 2 ? f.r : f.g;
}

int orderAt(uint i) {
    return int(floor(texelFetch(sTD2DInputs[ORDER], ivec2(int(i & 1023u), int(i >> 10)), 0).r + 0.5));
}

// Lines' field at a point (pixels): the distance to the subject's outline, negative inside, and its slope; without a
// subject, the distance from the top of the picture, so the lines run across it like a page.
vec3 ringAt(vec2 p) {
    if (!ANY) return vec3(uGrid.y - p.y, 0.0, -1.0);
    vec3 f = textureLod(sTD2DInputs[RINGS], p / uGrid.xy, 0.0).rgb;
    return vec3(f.r * CELL.y, f.gb * CELL.y / CELL);
}

float phiAt(vec2 p) {
    return ringAt(p).x;
}

// The biggest level a word may take at a cell (-1: none).
int allowedAt(ivec2 c, float meanDetail) {
    if (MODE == 2) return NL - 1;
    vec4 cl = texelFetch(sTD2DInputs[CELLS], c, 0);
    if (MODE == 1) {
        float q = cl.g / max(meanDetail, 1e-4) * mix(0.25, 4.0, uSize.z);
        return NL - 1 - clamp(int(floor(2.0 * log2(1.0 + q))), 0, NL - 1);
    }
    if (!ANY) return NL - 1;
    return cl.r > 0.5 || fieldAt(c) < uSize.w ? NL - 1 : -1;
}

// How good a spot is, 0-4095: Cloud deep inside the subject (or the frame's middle without one), Portrait any.
uint scoreAt(ivec2 c) {
    if (MODE == 1) return 0u;
    float d = ANY ? -fieldAt(c) : float(min(min(c.x, GW - 1 - c.x), min(c.y, GH - 1 - c.y)));
    return uint(clamp(d / 64.0, 0.0, 1.0) * 4095.0);
}

// Lines: a word of size s on the line through the middle of cell c, if it lies close to one: its middle, its direction
// (upright: reading rightward, or up a line that runs straight up and down), its line, and whether it fits there free.
// Only every other cell across and down is tried (a word's line takes it from there), so a cell lying within one
// cell of a line will do.
bool onLine(ivec2 c, vec2 s, float S, out vec2 p, out vec2 u, out float k) {
    p = (vec2(c) + 0.5) * CELL;
    u = vec2(1.0, 0.0);
    k = 0.0;
    vec3 f = ringAt(p);
    float ph = f.x;
    k = floor(ph / S);
    float off = ph - (k + 0.5) * S;
    if (abs(off) > CELL.y) return false;
    vec2 g = f.yz;
    float gl = length(g);
    if (gl < 0.3) return false;
    p -= g / gl * off / gl;
    u = vec2(g.y, -g.x) / gl;
    if (u.x < -1e-3 || (abs(u.x) <= 1e-3 && u.y < 0.0)) u = -u;
    float c0 = (k + 0.5) * S;
    if (abs(phiAt(p + 0.5 * s.x * u) - c0) > DRIFT * S || abs(phiAt(p - 0.5 * s.x * u) - c0) > DRIFT * S) return false;
    return true;
}

// Lines: a word of size s written on from q (where the last word ended) along u on line k: its middle p and direction
// (u, turned to the line there), if it stays on its line and the place is free.
bool writeOn(vec2 q, vec2 dir, float k, vec2 s, float S, out vec2 p, out vec2 u) {
    vec2 room = roomOf(0.0);
    p = q + dir * (0.5 * s.x + room.x);
    u = dir;
    vec3 f = ringAt(p);
    float gl = length(f.yz);
    if (gl < 0.3) return false;
    float off = f.x - (k + 0.5) * S;
    if (abs(off) > 0.5 * S) return false;
    p -= f.yz / gl * off / gl;
    u = vec2(f.z, -f.y) / gl;
    if (dot(u, dir) < 0.0) u = -u;
    if (dot(u, dir) < TURN || u.x < -0.3) return false;
    float c0 = (k + 0.5) * S;
    if (abs(phiAt(p + 0.5 * s.x * u) - c0) > DRIFT * S || abs(phiAt(p - 0.5 * s.x * u) - c0) > DRIFT * S) return false;
    return turned(p, vec2(0.5 * s.x + room.x, 0.55 * CELL.y), u, false);
}

void main() {
    uint t = gl_LocalInvocationIndex;
    ivec2 grid = textureSize(sTD2DInputs[CELLS], 0);
    GW = min(grid.x, ROWU * 32);
    GH = min(grid.y, MAXROWS);
    CELL = uGrid.xy / vec2(grid);
    NL = clamp(int(uGrid.w + 0.5), 1, LEVELS);
    MODE = int(uGrid.z + 0.5);
    float dt = uTime.x;
    float S = RING * levelSize(0);              // Lines: the lines' spacing

    vec4 box = texelFetch(sTD2DInputs[STATE], ivec2(t, 0), 0);
    vec4 info = texelFetch(sTD2DInputs[STATE], ivec2(t, 1), 0);
    vec4 more = texelFetch(sTD2DInputs[STATE], ivec2(t, 2), 0);
    vec4 glob = texelFetch(sTD2DInputs[STATE], ivec2(0, 3), 0);
    vec4 chain = texelFetch(sTD2DInputs[STATE], ivec2(1, 3), 0);
    if (any(isnan(box)) || any(isnan(info)) || any(isnan(more))) {
        box = info = more = glob = chain = vec4(0.0);
    }
    // The text, the font or the case changed (the words are counted anew): a word whose ink no longer has its box's
    // shape now names another word, and goes at once rather than show stretched.
    if (info.w != 0.0) {
        vec4 ink = texelFetch(sTD2DInputs[INK], ivec2(int(info.x + 0.5), 0), 0);
        float now = (ink.z - ink.x) / max(ink.w - ink.y, 1e-3), was = box.z / max(box.w, 1e-3);
        if (abs(now - was) > 0.03 * was) box = info = more = vec4(0.0);
    }

    // ---- the subject, the picture's detail, the order's length
    if (t == 0u) {
        sCount = 0u;
        sDetail = 0u;
        sTokens = 4096u;
        sLive = 0u;
        sFreed = 0u;
    }
    if (t < 32u) sShown[t] = 0u;
    memoryBarrierShared();
    barrier();
    uint inside = 0u;
    float detail = 0.0;
    for (int a = int(t); a < GW * GH; a += SLOTS) {
        vec4 cl = texelFetch(sTD2DInputs[CELLS], ivec2(a % GW, a / GW), 0);
        inside += cl.r > 0.5 ? 1u : 0u;
        detail += cl.g;
    }
    atomicAdd(sCount, inside);
    atomicAdd(sDetail, uint(detail * 1024.0));
    for (uint i = t; i < 4096u; i += uint(SLOTS))
        if (texelFetch(sTD2DInputs[ORDER], ivec2(int(i & 1023u), int(i >> 10)), 0).r < -0.5) atomicMin(sTokens, i);
    memoryBarrierShared();
    barrier();
    ANY = sCount >= 24u;
    float meanDetail = float(sDetail) / 1024.0 / float(GW * GH);

    // ---- carried: by the picture's motion (Cloud), or along with its line (Lines)
    bool hit = false;
    if (info.w != 0.0 && MODE == 2) {
        vec3 f = ringAt(box.xy);
        vec2 g = f.yz;
        float gl = length(g);
        if (gl > 0.3) {
            // half way back onto its line a frame, at most a quarter of a line: the field is bilinear between cells,
            // and a full step there overshoots and comes back the next frame, a word shaking every other frame
            float off = f.x - (more.w + 0.5) * S;
            vec2 back = g / gl * off / gl;
            box.xy -= back * min(0.5, 0.25 * S / max(length(back), 1e-3));
            vec2 u = vec2(g.y, -g.x) / gl;
            vec2 was = vec2(cos(more.y), sin(more.y));
            if (dot(u, was) < 0.0) u = -u;
            hit = dot(u, was) < TURN || abs(off) > 0.5 * S || u.x < -0.3;
            u = normalize(was + u);
            more.y = atan(u.y, u.x);
        } else {
            hit = true;
        }
    } else if (info.w != 0.0 && MODE == 0 && uMove.x > 0.0) {
        vec2 res = vec2(textureSize(sTD2DInputs[MOTION], 0));
        vec2 v = vec2(0.0);
        for (int k = 0; k < 5; k++) {
            vec2 o = vec2(k == 1 ? -0.3 : k == 2 ? 0.3 : 0.0, k == 3 ? -0.3 : k == 4 ? 0.3 : 0.0);
            v += textureLod(sTD2DInputs[MOTION], (box.xy + o * box.zw) / uGrid.xy, 0.0).rg;
        }
        box.xy += v / 5.0 / res * uGrid.xy * uMove.x * dt;
    }

    // ---- touching an older word (boxes in shared memory for now). Cloud and Portrait push a word off an older one,
    // as EdWordle moves words as rigid bodies; one still deep in it after that counts as out of its region. Lines'
    // words stay on their lines and only count as out.
    sMem[4u * t] = floatBitsToUint(box.x);
    sMem[4u * t + 1u] = floatBitsToUint(box.y);
    sMem[4u * t + 2u] = floatBitsToUint(box.z);
    sMem[4u * t + 3u] = floatBitsToUint(box.w);
    sMem[4096u + t] = floatBitsToUint(info.w > 0.0 ? more.z : -1.0);
    // its angle and (Lines) its line, 16 bits each
    sMem[6144u + t] = (uint(fract(more.y / 6.2831853) * 65535.0 + 0.5) << 16) | (uint(int(more.w) + 32768) & 65535u);
    if (info.w > 0.0) sMem[5120u + atomicAdd(sLive, 1u)] = t;
    memoryBarrierShared();
    barrier();
    uint live = sLive;
    vec2 push = vec2(0.0);
    if (info.w > 0.0) {
        vec2 room = roomOf(info.y);
        vec2 ua = vec2(cos(more.y), sin(more.y));
        for (uint n = 0u; n < live; n++) {
            uint j = sMem[5120u + n];
            float aj = uintBitsToFloat(sMem[4096u + j]);
            if (j == t || aj < more.z || (aj == more.z && j > t)) continue;   // younger: it yields to this one
            vec4 b = vec4(uintBitsToFloat(sMem[4u * j]), uintBitsToFloat(sMem[4u * j + 1u]),
                          uintBitsToFloat(sMem[4u * j + 2u]), uintBitsToFloat(sMem[4u * j + 3u]));
            vec2 d = box.xy - b.xy;
            float tol = TOUCH * min(box.w, b.w);
            if (MODE == 2) {
                // Lines: only words on the same line meet; a crowded one is pushed along it, away from the older one
                uint packed = sMem[6144u + j];
                if (int(packed & 65535u) - 32768 != int(more.w)) continue;
                float aj2 = float(packed >> 16) / 65535.0 * 6.2831853;
                vec2 ub = vec2(cos(aj2), sin(aj2));
                float along = 0.5 * (box.z + abs(dot(ub, ua)) * b.z + abs(dot(vec2(-ub.y, ub.x), ua)) * b.w) + room.x
                              - abs(dot(d, ua));
                float across = 0.5 * (box.w + b.w) - abs(dot(d, vec2(-ua.y, ua.x)));
                if (along <= 0.0 || across <= 0.0) continue;
                push += (dot(d, ua) < 0.0 ? -1.0 : 1.0) * along * ua;
                hit = hit || along - room.x > tol;
                continue;
            }
            vec2 over = 0.5 * (box.zw + b.zw) + room - abs(d);
            if (over.x <= 0.0 || over.y <= 0.0) continue;
            if (over.x < over.y) push.x += (d.x < 0.0 ? -1.0 : 1.0) * over.x;
            else push.y += (d.y < 0.0 ? -1.0 : 1.0) * over.y;
            hit = hit || (over.x - room.x > tol && over.y - room.y > tol);
        }
    }
    memoryBarrierShared();
    barrier();
    box.xy += PUSH * push;

    // ---- the masks: the occupancy, and for each level the cells it may not cover; a mask word (32 cells of a row)
    // an invocation, built in registers and written once
    for (uint i = t; i < uint(MASK); i += uint(SLOTS)) sMem[i] = 0u;
    for (int m = int(t); m < GH * ROWU; m += SLOTS) {
        int r = m / ROWU, k = m - r * ROWU;
        uint bits[LEVELS];
        for (int L = 0; L < LEVELS; L++) bits[L] = 0u;
        for (int i = 0; i < 32; i++) {
            int col = 32 * k + i;
            if (col >= GW) break;
            for (int L = max(allowedAt(ivec2(col, r), meanDetail) + 1, 0); L < NL; L++) bits[L] |= 1u << uint(i);
        }
        for (int L = 0; L < NL; L++) sMem[MASK * (1 + L) + m] = bits[L];
    }
    memoryBarrierShared();
    barrier();

    // ---- each word still in its region? (Portrait allows a level of slack, so detail at the edge of a word's
    // limit doesn't flip it in and out)
    if (info.w > 0.0) {
        ivec4 cb = cellsOf(box);
        int L = clamp(int(info.y + 0.5) - (MODE == 1 ? 1 : 0), 0, NL - 1);
        int total = max((cb.z - cb.x) * (cb.w - cb.y), 1);
        ivec4 in_ = ivec4(max(cb.xy, ivec2(0)), min(cb.zw, ivec2(GW, GH)));
        int bad = total - max(in_.z - in_.x, 0) * max(in_.w - in_.y, 0);
        if (in_.z > in_.x && in_.w > in_.y) bad += forbidden(in_.x, in_.z, in_.y, in_.w, L);
        bool ok = !hit && float(bad) <= OUTSIDE * float(total);
        more.x = ok ? 0.0 : more.x + dt;
        if (more.x > uTime.z || bad >= total) {
            info.w = -1.0;
            atomicOr(sFreed, 1u);
        }
    }
    if (info.w != 0.0) {
        info.z = clamp(info.z + info.w * dt / max(uTime.y * (info.w < 0.0 ? LEAVE : 1.0), 1e-3), 0.0, 1.0);
        more.z += dt;
        if (info.w < 0.0 && info.z <= 0.0) {
            box = info = more = vec4(0.0);
        }
    }
    if (info.w > 0.0 || (MODE == 0 && info.w != 0.0)) {
        vec2 room = roomOf(info.y);
        if (MODE == 2) {
            turned(box.xy, vec2(0.5 * box.z + room.x, 0.55 * CELL.y), vec2(cos(more.y), sin(more.y)), true);
        } else {
            ivec4 cb = cellsOf(box + vec4(0.0, 0.0, 2.0 * room));
            take(cb.x, cb.z, cb.y, cb.w);
        }
    }
    if (info.w > 0.0) {
        int w = int(info.x + 0.5);
        atomicOr(sShown[(w >> 5) & 31], 1u << uint(w & 31));
    }
    memoryBarrierShared();
    barrier();

    // ---- new words into what is free
    uint ntok = sTokens;
    float next = mod(glob.x, max(float(ntok), 1.0));
    float far = length(uGrid.xy);
    int fails = 0, placed = 0;
    bool idle = glob.z > 0.0 && glob.z < IDLE && sFreed == 0u;
    for (int n = 0; n < (idle ? 0 : int(uTime.w)) && ntok > 0u && fails < TRIES; n++) {
        if (t == 0u) {
            sKey = 0u;
            sSlot = NONE;
            sPick = NONE;
        }
        memoryBarrierShared();
        barrier();
        // Which word: Cloud the best-ranked word not on screen, else (and Portrait, Lines) the next one in order.
        uint tok;
        int cap = MODE == 2 ? 0 : NL - 1;
        if (MODE == 0) {
            if (t < ntok) {
                int w = orderAt(t);
                if ((sShown[(w >> 5) & 31] & (1u << uint(w & 31))) == 0u) atomicMin(sPick, t);
            }
            memoryBarrierShared();
            barrier();
            bool fresh = sPick != NONE;
            tok = fresh ? sPick : uint(next) % ntok;
            if (!fresh) next = mod(next + 1.0, float(ntok));
            cap = NL - 1 - int(floor(0.75 * log2(1.0 + float(tok))));
            if (!fresh) cap = min(cap, NL / 2 - 1);
            cap = clamp(cap, 0, NL - 1);
        } else {
            tok = uint(next) % ntok;
            next = mod(next + 1.0, float(ntok));
        }
        int word = orderAt(tok);
        vec4 ink = texelFetch(sTD2DInputs[INK], ivec2(word, 0), 0);
        float line = texelFetch(sTD2DInputs[VOCAB], ivec2(word, 3), 0).r +
                     texelFetch(sTD2DInputs[VOCAB], ivec2(word, 4), 0).r;
        vec2 inkPx = ink.zw - ink.xy;
        uint best = 0u;
        int bestL = -1;
        // Lines: on along the line from the last word, if there is room (every invocation works it out alike)
        vec2 cp, cu;
        bool written = MODE == 2 && glob.y > 0.5 && word >= 0 && inkPx.x > 0.0 && line > 0.0 &&
                       writeOn(chain.xy, vec2(cos(chain.z), sin(chain.z)), chain.w, inkPx * levelSize(0) / line, S, cp,
                               cu);
        if (written) best = 1u << 27;
        else if (word >= 0 && inkPx.x > 0.0 && inkPx.y > 0.0 && line > 0.0) {
            for (int a = int(t); a < GW * GH; a += SLOTS) {
                int c0 = a % GW, r0 = a / GW;
                if (MODE == 2) {
                    if (((c0 | r0) & 1) != 0) continue;
                    vec2 size = inkPx * levelSize(0) / line, room = roomOf(0.0), p, u;
                    float k;
                    if (!onLine(ivec2(c0, r0), size, S, p, u, k)) continue;
                    if (!turned(p, vec2(0.5 * size.x + room.x, 0.55 * CELL.y), u, false)) continue;
                    // a word just after another, on its line, first; then the lines nearest the subject (or the top)
                    bool after = taken(ivec2(floor((p - u * (0.5 * size.x + room.x + 0.75 * CELL.x)) / CELL)));
                    uint near = uint(clamp(1.0 - abs((k + 0.5) * S) / far, 0.0, 1.0) * 2047.0);
                    uint key = (1u << 27) | ((after ? 2048u + near : near) << 15) | uint(a & 32767);
                    best = max(best, key);
                    continue;
                }
                for (int L = cap; L > bestL; L--) {
                    vec2 size = inkPx * levelSize(L) / line + 2.0 * roomOf(float(L));
                    ivec2 b = max(ivec2(ceil(size / CELL - 0.05)), ivec2(1));
                    if (c0 + b.x > GW || r0 + b.y > GH || !fits(c0, c0 + b.x, r0, r0 + b.y, L)) continue;
                    uint place = MODE == 1 ? uint(32767 - ((GH - r0 - b.y) * GW + c0)) : uint(a);
                    uint key = (uint(L + 1) << 27) | (scoreAt(ivec2(c0, r0) + b / 2) << 15) | (place & 32767u);
                    if (key > best) {
                        best = key;
                        bestL = L;
                    }
                    break;
                }
            }
        }
        atomicMax(sKey, best);
        if (info.w == 0.0) atomicMin(sSlot, t);
        memoryBarrierShared();
        barrier();
        uint key = sKey;
        uint slot = sSlot;
        memoryBarrierShared();
        barrier();
        if (key == 0u || slot == NONE) {
            // no room for it (or no free slot): Cloud passes over it for the rest of this frame; Lines' text stops
            glob.y = 0.0;
            if (t == 0u && word >= 0) atomicOr(sShown[(word >> 5) & 31], 1u << uint(word & 31));
            memoryBarrierShared();
            barrier();
            fails++;
            continue;
        }
        fails = 0;
        placed++;
        int L = int(key >> 27) - 1;
        vec2 size = inkPx * levelSize(L) / line;
        int place = int(key & 32767u);
        if (MODE == 2) {
            vec2 p = cp, u = cu;
            float k = chain.w;
            if (!written) onLine(ivec2(place % GW, place / GW), size, S, p, u, k);
            chain = vec4(p + u * (0.5 * size.x + roomOf(0.0).x), atan(u.y, u.x), k);
            glob.y = 1.0;
            if (t == slot) {
                box = vec4(p, size);
                info = vec4(float(word), 0.0, 0.0, 1.0);
                more = vec4(0.0, atan(u.y, u.x), 0.0, k);
            }
            if (t == 0u) turned(p, vec2(0.5 * size.x + roomOf(0.0).x, 0.55 * CELL.y), u, true);
        } else {
            ivec2 b = max(ivec2(ceil((size + 2.0 * roomOf(float(L))) / CELL - 0.05)), ivec2(1));
            ivec2 c = MODE == 1 ? ivec2((32767 - place) % GW, GH - b.y - (32767 - place) / GW)
                                : ivec2(place % GW, place / GW);
            if (t == slot) {
                box = vec4((vec2(c) + 0.5 * vec2(b)) * CELL, size);
                info = vec4(float(word), float(L), 0.0, 1.0);
                more = vec4(0.0);
            }
            if (t == 0u) take(c.x, c.x + b.x, c.y, c.y + b.y);
        }
        if (t == 0u) atomicOr(sShown[(word >> 5) & 31], 1u << uint(word & 31));
        memoryBarrierShared();
        barrier();
    }

    imageStore(mTDComputeOutputs[0], ivec2(t, 0), TDOutputSwizzle(box));
    imageStore(mTDComputeOutputs[0], ivec2(t, 1), TDOutputSwizzle(info));
    imageStore(mTDComputeOutputs[0], ivec2(t, 2), TDOutputSwizzle(more));
    if (t == 0u) {
        // seconds since a search found no room
        float wait = idle ? glob.z + dt : (placed == 0 && fails > 0 ? dt : 0.0);
        imageStore(mTDComputeOutputs[0], ivec2(0, 3), TDOutputSwizzle(vec4(next, MODE == 2 ? glob.y : 0.0, wait, 0.0)));
        imageStore(mTDComputeOutputs[0], ivec2(1, 3), TDOutputSwizzle(chain));
    }
}
