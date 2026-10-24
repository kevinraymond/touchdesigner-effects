// Blob Track (touchdesigner-effects, MIT). Follows each detected blob by its ID in one of 64 slots,
// so boxes glide instead of jumping with each picture frame. A box shows only once its blob has
// lasted a moment (haze and specks that come and go never get one), then fades in, and fades out
// when lost: never popping, so the overlay itself doesn't flicker (all in seconds, not frames). A box whose blob vanished takes over the new blob that
// overlaps it most (match.glsl), keeping its label; a new blob takes the first free slot and the
// next label number (the effect's own count, so no two boxes ever share one).
// Inputs: 0 the detector's list (bt_pick.glsl or grid_pick.glsl); 1 this TOP's previous output;
// 2 match.glsl.
// Out, column = slot: row 0 smoothed center u, v, width, height; row 1 the ID followed, fade 0-1
// (0: free; held but not shown yet: HIDDEN), age (s), 1 while detected; row 2 x the label number,
// y (every slot) the labels handed out so far.
uniform vec4 uClock;   // x seconds since the last frame, y smoothing time (s), z fade-in (s), w fade-out (s)
uniform vec4 uShow;    // x how long a blob must last before its box shows (s)
#define HIDDEN 0.001
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

// Slot s's claim on its entry beats every other slot's (best overlap, then lowest slot).
bool wins(int s, vec4 ms) {
    for (int t = 0; t < N; t++) {
        if (t == s) continue;
        vec4 mt = M(t);
        if (abs(mt.x - ms.x) < 0.5 && (mt.y > ms.y || (mt.y == ms.y && t < s))) return false;
    }
    return true;
}

void main() {
    int s = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    int n = min(int(L(0, 1).w + 0.5), N);
    float dt = uClock.x;
    float k = 1.0 - exp(-dt / max(uClock.y, 1e-3));
    vec4 o0 = S(s, 0), o1 = S(s, 1), o2 = S(s, 2);
    vec4 n0 = vec4(-1.0, -1.0, 0.0, 0.0), n1 = vec4(-1.0, 0.0, 0.0, 0.0), n2 = vec4(-1.0, 0.0, 0.0, 0.0);
    if (o1.y > 0.0) {
        // Held: follow its blob, take over the one that replaced it, or fade out where it was.
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
            float fade = o1.z + dt < uShow.x ? HIDDEN : min(1.0, o1.y + dt / uClock.z);
            n1 = vec4(L(j, 1).x, fade, o1.z + dt, 1.0);
        } else {
            n0 = o0;
            n1 = vec4(o1.x, max(0.0, o1.y - dt / uClock.w), o1.z + dt, 0.0);
        }
    }
    // New blobs (no box holds or takes over their ID) go to the free slots in order: the f-th
    // free slot takes the f-th new blob and label number base + f + 1.
    int f = 0, free = 0, fresh = 0, mine = -1;
    for (int t = 0; t < N; t++) {
        if (S(t, 1).y > 0.0) continue;
        if (t < s) f++;
        free++;
    }
    for (int i = 0; i < N; i++) {
        if (i >= n) break;
        if (idHeld(L(i, 1).x) || claimed(i)) continue;
        if (fresh == f && o1.y <= 0.0) mine = i;
        fresh++;
    }
    float base = max(S(0, 2).y, 0.0);
    if (mine >= 0) {
        n0 = L(mine, 0);
        n1 = vec4(L(mine, 1).x, HIDDEN, 0.0, 1.0);
        n2.x = mod(base + float(f) + 1.0, 10000.0);
    }
    n2.y = base + float(min(free, fresh));
    fragColor = row == 0 ? n0 : row == 1 ? n1 : n2;
}
