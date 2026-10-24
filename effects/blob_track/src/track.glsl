// Blob Track (touchdesigner-effects, MIT). Follows each detected blob by its ID in one of 64 slots,
// so boxes glide instead of jumping with each picture frame. A box shows only once its blob has
// lasted a moment (haze and specks that come and go never get one), then fades in, and fades out
// when lost: never popping, so the overlay itself doesn't flicker (all in seconds, not frames).
// Detectors lose a blob for a moment or hand it a new ID whenever it splits, merges or dims, so a
// box that has shown keeps its place when its blob vanishes: it coasts on along its last motion for
// a hold time before it fades, and takes over the new blob that matches it (match.glsl: overlapping
// it, or close by and of a similar size), keeping its label.
// Max Count limits the boxes showing, not the blobs followed: boxes keep what they follow, and a
// blob that has lasted long enough waits for room before its box shows (the longest waiting
// first). A new blob takes the first free slot; it gets the next label number (the effect's own
// count, so no two boxes ever share one) when its box first shows, so blobs that never show don't
// use numbers up.
// Inputs: 0 the detector's list (bt_pick.glsl or grid_pick.glsl); 1 this TOP's previous output;
// 2 match.glsl.
// Out, column = slot: row 0 smoothed center u, v, width, height; row 1 the ID followed, fade 0-1
// (0: free; held but not shown yet: HIDDEN), age (s), seconds since its blob was last detected (0
// while detected); row 2 x the label number (-1 until the box shows), y (every slot) the labels
// handed out so far, zw its velocity (u, v a second).
uniform vec4 uClock;   // x seconds since the last frame, y smoothing time (s), z fade-in (s), w fade-out (s)
uniform vec4 uShow;    // x how long a blob must last before its box shows (s), y how long a lost box
                       // coasts before it fades (s), z Max Count
#define HIDDEN 0.001
#define VEL_SMOOTH 0.25  // seconds over which the velocity follows the box's motion
#define VEL_FADE 0.5     // seconds over which a coasting box's velocity falls by 1/e
out vec4 fragColor;
#define N 64

vec4 L(int i, int r) { return texelFetch(sTD2DInputs[0], ivec2(i, r), 0); }
vec4 S(int s, int r) { return texelFetch(sTD2DInputs[1], ivec2(s, r), 0); }
vec4 M(int s) { return texelFetch(sTD2DInputs[2], ivec2(s, 0), 0); }

bool idHeld(float id) {
    for (int s = 0; s < N; s++) {
        vec4 m = S(s, 1);
        if (m.y > 0.0 && abs(m.x - id) < 0.5) return true;
    }
    return false;
}

// Some box takes over list entry j this frame.
bool claimed(int j) {
    for (int s = 0; s < N; s++) {
        if (abs(M(s).x - float(j)) < 0.5) return true;
    }
    return false;
}

// Slot s's claim on its entry beats every other slot's (best match, then lowest slot).
bool wins(int s, vec4 ms) {
    for (int t = 0; t < N; t++) {
        if (t == s) continue;
        vec4 mt = M(t);
        if (abs(mt.x - ms.x) < 0.5 && (mt.y > ms.y || (mt.y == ms.y && t < s))) return false;
    }
    return true;
}

bool showing(vec4 m) { return m.y >= 2.0 * HIDDEN; }

// Slot t's blob has lasted long enough for a box, which isn't showing yet.
bool ready(vec4 m, float dt) { return m.y > 0.0 && m.y < 2.0 * HIDDEN && m.z + dt >= uShow.x; }

// Slot a (state ma) came before slot b: older, or as old and a lower slot.
bool before(vec4 ma, int a, vec4 mb, int b) { return ma.z > mb.z || (ma.z == mb.z && a < b); }

// Slot t's box shows for the first time this frame: ready, and there is room for it beside the
// boxes showing and the ready ones that came before it.
bool showsNow(int t, float dt, int showingCount) {
    vec4 m = S(t, 1);
    if (!ready(m, dt)) return false;
    int ahead = 0;
    for (int u = 0; u < N; u++) {
        vec4 mu = S(u, 1);
        if (u != t && ready(mu, dt) && before(mu, u, m, t)) ahead++;
    }
    return float(showingCount + ahead) < uShow.z;
}

void main() {
    int s = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    int n = min(int(L(0, 1).w + 0.5), N);
    float dt = uClock.x;
    float k = 1.0 - exp(-dt / max(uClock.y, 1e-3));
    vec4 o0 = S(s, 0), o1 = S(s, 1), o2 = S(s, 2);
    vec4 n0 = vec4(-1.0, -1.0, 0.0, 0.0), n1 = vec4(-1.0, 0.0, 0.0, 0.0), n2 = vec4(-1.0, 0.0, 0.0, 0.0);
    // The boxes showing (as of the last frame), and how many of them came before this one: past
    // Max Count (after Max Count was lowered), a box fades out.
    int showingCount = 0, rank = 0;
    for (int t = 0; t < N; t++) {
        vec4 m = S(t, 1);
        if (!showing(m)) continue;
        showingCount++;
        if (t != s && before(m, t, o1, s)) rank++;
    }
    bool over = showing(o1) && float(rank) >= uShow.z;
    // Label numbers go to the boxes showing for the first time, in slot order.
    float base = max(S(0, 2).y, 0.0);
    int earlier = 0, firsts = 0;
    for (int t = 0; t < N; t++) {
        if (!showsNow(t, dt, showingCount)) continue;
        if (t < s) earlier++;
        firsts++;
    }
    if (o1.y > 0.0) {
        // Held: follow its blob, take over the one that replaced it, or coast on, then fade out.
        int j = -1;
        for (int i = 0; i < N; i++) {
            if (i >= n) break;
            if (abs(L(i, 1).x - o1.x) < 0.5) { j = i; break; }
        }
        vec4 ms = M(s);
        if (j < 0 && ms.x >= 0.0 && wins(s, ms)) j = int(ms.x + 0.5);
        n2 = o2;
        if (j >= 0) {
            n0 = mix(o0, L(j, 0), k);
            vec2 v = dt > 0.0 ? (n0.xy - o0.xy) / dt : o2.zw;
            n2.zw = mix(o2.zw, v, 1.0 - exp(-dt / VEL_SMOOTH));
            float fade = HIDDEN;
            if (showing(o1)) {
                fade = over ? max(0.0, o1.y - dt / uClock.w) : min(1.0, o1.y + dt / uClock.z);
            } else if (showsNow(s, dt, showingCount)) {
                fade = max(HIDDEN + dt / uClock.z, 2.0 * HIDDEN);
                n2.x = mod(base + float(earlier) + 1.0, 10000.0);
            }
            n1 = vec4(L(j, 1).x, fade, o1.z + dt, 0.0);
        } else if (!showing(o1)) {
            n1 = vec4(o1.x, 0.0, o1.z + dt, o1.w + dt);  // never showed: let it go
        } else {
            float lost = o1.w + dt;
            n2.zw = o2.zw * exp(-dt / VEL_FADE);
            n0 = vec4(clamp(o0.xy + n2.zw * dt, vec2(0.0), vec2(1.0)), o0.zw);
            float fade = lost < uShow.y && !over ? o1.y : max(0.0, o1.y - dt / uClock.w);
            n1 = vec4(o1.x, fade, o1.z + dt, lost);
        }
    }
    // New blobs (no box holds or takes over their ID) go to the free slots in order: the f-th
    // free slot takes the f-th new blob.
    int f = 0, fresh = 0, mine = -1;
    for (int t = 0; t < N; t++) {
        if (S(t, 1).y > 0.0) continue;
        if (t < s) f++;
    }
    for (int i = 0; i < N; i++) {
        if (i >= n) break;
        if (idHeld(L(i, 1).x) || claimed(i)) continue;
        if (fresh == f && o1.y <= 0.0) mine = i;
        fresh++;
    }
    if (mine >= 0) {
        n0 = L(mine, 0);
        n1 = vec4(L(mine, 1).x, HIDDEN, 0.0, 0.0);
        n2 = vec4(-1.0, 0.0, 0.0, 0.0);
    }
    n2.y = base + float(firsts);
    fragColor = row == 0 ? n0 : row == 1 ? n1 : n2;
}
