// Pixel Sort (touchdesigner-effects, MIT). The sort, a compute shader: each workgroup takes one line of pixels
// across the picture toward the sort's angle, finds its spans, sorts each span by value and writes its pixels back in
// that order. Lines are digital lines (within 45 degrees of horizontal one pixel per column, line = y - round(x tan),
// else one per row), so every pixel lies in exactly one line and nothing is resampled.
// One sort of the whole line sorts every span at once: each pixel's key is (where its span starts, its value, its
// place in the line), so the spans keep their places in the line and each one comes out sorted within itself (a
// segmented sort by composite key, a widely known technique). A pixel outside every span is a span of one and stays
// where it is. The sort is a bitonic sorting network (K. E. Batcher, "Sorting networks and their applications", AFIPS
// 1968) on keys in shared memory; where each span starts comes from a max-scan (W. D. Hillis and G. L. Steele,
// "Data parallel algorithms", CACM 1986).
// Inputs: 0 the picture, 1 key.glsl (r the value, g in a span, b a cut). Out: the sorted picture, one write a pixel.
layout (local_size_x = 512) in;
uniform vec4 uLine;   // x, y: cosine and sine of the angle the sort runs toward (each span's values rise that way),
                      // z: how wide a beat's tears are (1: 6 to 18 lines at 720; 0 none), w: the beat's number
uniform vec4 uWhole;  // x: 1 while a drop sorts every line whole

#define NT 512u
#define MAXN 2048u    // lines up to 2048 pixels; the Non-Commercial license stops at 1280
#define SYNC memoryBarrierShared(); barrier()

shared uint sA[MAXN];
shared uint sB[MAXN];
shared int sLo, sHi;
shared uint sAny;

// Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
uint ihash(uint x) {
    x ^= x >> 16; x *= 0x7feb352du;
    x ^= x >> 15; x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}

// A beat's tears: is the line at f (0-1 across the lines) in one of its three slivers, one in each third of the
// picture so they stay apart? Those lines sort whole and against the grain, their bright end where the spans around
// them have their dark one: a few thin streaks that stand out, too little of the picture to count as a flash. Sorted
// whole but with the grain they hardly showed (dev/reaction.py: 1.07 times the change after a beat as before).
bool tear(float f) {
    if (uLine.z <= 0.0) return false;
    float row = f * 720.0;
    for (int k = 0; k < 3; k++) {
        uint h = ihash(uint(uLine.w) * 7u + uint(k) + 1u);
        float at = 24.0 + 240.0 * float(k) + float(h % 192u);
        if (abs(row - at) < 3.0 * (1.0 + float((h >> 12) % 3u)) * uLine.z) return true;
    }
    return false;
}

// The line's geometry, shared by every invocation of the workgroup.
bool shallow, forward;
int along, line, lo, n;
float slope;

// The pixel at place i along the line, counted in the sort's direction.
ivec2 pixel(int i) {
    int m = forward ? lo + i : lo + n - 1 - i;
    int minor = line + int(round(float(m) * slope));
    return shallow ? ivec2(m, minor) : ivec2(minor, m);
}

void main() {
    uint tid = gl_LocalInvocationID.x;
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    float c = uLine.x, s = uLine.y;
    shallow = abs(c) >= abs(s);
    along = shallow ? size.x : size.y;
    int across = shallow ? size.y : size.x;
    slope = shallow ? s / c : c / s;
    forward = shallow ? c > 0.0 : s > 0.0;
    int rise = int(round(float(along - 1) * slope));
    int lines = across + abs(rise);
    int g = int(gl_WorkGroupID.x);
    if (g >= lines) return;                          // more workgroups are dispatched than any angle needs
    line = g - max(rise, 0);

    // The stretch of the line inside the picture (one piece: the line's minor coordinate only rises or only falls).
    if (tid == 0u) { sLo = along; sHi = -1; sAny = 0u; }
    SYNC;
    for (int m = int(tid); m < along; m += int(NT)) {
        int minor = line + int(round(float(m) * slope));
        if (minor >= 0 && minor < across) { atomicMin(sLo, m); atomicMax(sHi, m); }
    }
    SYNC;
    lo = sLo;
    n = sHi - sLo + 1;
    if (n <= 0) return;
    uint N = 2u;
    while (N < uint(n)) N <<= 1;
    bool torn = tear((float(g) + 0.5) / float(lines));
    bool whole = uWhole.x > 0.5 || torn;

    // Each pixel's flags: 1 in a span, 2 a cut. Places past the line's end (up to N) are pads.
    for (uint i = tid; i < N; i += NT) {
        uint f = 0u;
        if (i < uint(n)) {
            vec4 k = texelFetch(sTD2DInputs[1], pixel(int(i)), 0);
            f = (whole || k.g > 0.5 ? 1u : 0u) | (!whole && k.b > 0.5 ? 2u : 0u);
        }
        sA[i] = f;
    }
    SYNC;
    // A span breaks at the line's start, at a pixel outside every span, at a span's first pixel and at a cut.
    for (uint i = tid; i < N; i += NT) {
        uint f = sA[i];
        bool brk = i == 0u || (f & 1u) == 0u || (sA[i - 1u] & 1u) == 0u || (f & 2u) != 0u;
        if (!brk) sAny = 1u;
        sB[i] = brk ? i : 0u;
    }
    SYNC;
    if (sAny == 0u) {                                // no span longer than a pixel: the line as it is
        for (int i = int(tid); i < n; i += int(NT)) {
            ivec2 p = pixel(i);
            imageStore(mTDComputeOutputs[0], p, TDOutputSwizzle(texelFetch(sTD2DInputs[0], p, 0)));
        }
        return;
    }
    // Where each pixel's span starts: the last break at or before it, an inclusive max-scan, ping-ponging between the
    // two arrays. Always 11 steps (an odd number), so the starts end up in sA.
    for (uint off = 1u; off < MAXN; off <<= 1) {
        bool fromB = (off & 0x555u) != 0u;           // steps 1, 3, 5... read sB
        for (uint i = tid; i < N; i += NT) {
            if (fromB) sA[i] = i >= off ? max(sB[i], sB[i - off]) : sB[i];
            else       sB[i] = i >= off ? max(sA[i], sA[i - off]) : sA[i];
        }
        SYNC;
    }
    // Keys: span start (11 bits), value (10 bits), place (11 bits). Pads sort last.
    for (uint i = tid; i < N; i += NT) {
        uint key = 0xffffffffu;
        if (i < uint(n)) {
            float v = texelFetch(sTD2DInputs[1], pixel(int(i)), 0).r;
            if (torn) v = 1.0 - v;
            key = (sA[i] << 21) | (uint(clamp(v, 0.0, 1.0) * 1023.0 + 0.5) << 11) | i;
        }
        sB[i] = key;
    }
    SYNC;
    // The bitonic network over N places, rising.
    for (uint k = 2u; k <= N; k <<= 1) {
        for (uint j = k >> 1; j > 0u; j >>= 1) {
            for (uint q = tid; q < N / 2u; q += NT) {
                uint i = ((q & ~(j - 1u)) << 1) | (q & (j - 1u));
                uint a = sB[i], b = sB[i | j];
                if ((a > b) == ((i & k) == 0u)) { sB[i] = b; sB[i | j] = a; }
            }
            SYNC;
        }
    }
    // Each place takes the pixel whose key landed there.
    for (uint i = tid; i < uint(n); i += NT) {
        vec4 col = texelFetch(sTD2DInputs[0], pixel(int(sB[i] & 2047u)), 0);
        imageStore(mTDComputeOutputs[0], pixel(int(i)), TDOutputSwizzle(col));
    }
}
