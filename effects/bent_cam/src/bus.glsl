// Bent Cam (touchdesigner-effects, MIT). The bus from the sensor to the camera's bridge chip, bent. The sensor
// sends each line as a stream of bytes in YUYV order: for each pair of pixels, Y (the first one's brightness),
// U (the pair's blue difference), Y (the second one's) and V (the pair's red difference), in BT.601's 8-bit
// ranges, one line after the next. The bridge reads eight data lines, D0 to D7, on each tick of the pixel clock
// and takes the bytes in that order. Wires soldered across the sensor's pins bend that in four ways:
// - Shorts: a data line wired to ground or to power reads 0 or 1 whatever is sent (stuck), and two lines wired
//   together both read the lower or the higher of the two (bridged). Which lines, and how, depends on the camera
//   (Camera): each of the lot's 50 has six shorts, in LOT (the builder writes it in from lot.py). Shorts connects
//   them one after another, and the one it is connecting touches on and off, in pieces of lines that come and go.
// - Byte Slip: the bridge takes the bytes one, two or three places late, so it reads color as brightness and
//   brightness as color (1 or 3) or swaps U and V (2). Brightness bytes read as color turn the dark parts green
//   and the light parts pink.
// - Clock Slips: the pixel clock gains or loses a tick here and there, so from that point the bytes come a place
//   early or late, until it loses or gains one back, or to the end of the line (the bridge starts each line afresh). Each beat slips a sliver of a
//   few lines, somewhere new each time: too small to count as a flash.
// - Sync: the sensor's lines are longer than the bridge counts, so each line starts a little later in the stream
//   than the one before. The picture shears, and every few lines the bytes slip a place, in bands.
// Inputs: 0 the camera's picture (R'G'B'). Out: Y, U, V as the bridge read them (bytes / 255).
uniform vec4 uBus;    // x Camera, y Shorts 0-1, z Byte Slip (bytes, 0-3), w Clock Slips 0-1
uniform vec4 uBus2;   // x Sync 0-1, y seconds (lib clock_seconds()), z the beat's kick (1 on the beat, falling to 0), w the beat's number
uniform vec4 uBurst;  // x the burst's envelope (0-1), y its number, z 1 if it was a drop's
out vec4 fragColor;
#define PIECE 7           // a short touching on and off does it in pieces of 2^PIECE bytes (64 pixels)
#define SLIPS 2           // places on each line where the pixel clock may slip
#define FRAME_SLIP 0.33   // a drop's burst starts the frame this far down
#define BEAT_LINES 6      // the lines each beat's sliver slips
#define TO_END 0.25       // the share of slips that never recover and run to the end of the line

int W, H, L, kind;

int yByte(vec3 c) { return clamp(int(round(16.0 + 219.0 * dot(c, vec3(0.299, 0.587, 0.114)))), 0, 255); }
int uByte(vec3 c) { return clamp(int(round(128.0 + 224.0 * dot(c, vec3(-0.168736, -0.331264, 0.5)))), 0, 255); }
int vByte(vec3 c) { return clamp(int(round(128.0 + 224.0 * dot(c, vec3(0.5, -0.418688, -0.081312)))), 0, 255); }

int wrap(int k) { int N = L * H; return ((k % N) + N) % N; }

// Byte k of the frame's stream (0 <= k < L x H), as the sensor sends it.
int sensorByte(int k) {
    int m = k / L, j = k - m * L, pair = j >> 2, t = j & 3;
    ivec2 a = ivec2(2 * pair, H - 1 - m), b = ivec2(min(2 * pair + 1, W - 1), H - 1 - m);
    vec3 ca = clamp(texelFetch(sTD2DInputs[0], a, 0).rgb, 0.0, 1.0);
    if (t == 0) return yByte(ca);
    vec3 cb = clamp(texelFetch(sTD2DInputs[0], b, 0).rgb, 0.0, 1.0);
    if (t == 2) return yByte(cb);
    vec3 c = 0.5 * (ca + cb);
    return t == 1 ? uByte(c) : vByte(c);
}

// The byte at stream place k as it reaches the bridge, through the camera's shorts (LOT, from lot.py).
int bend(int v, int k) {
    int cam = clamp(int(uBus.x + 0.5), 1, CAMERAS) - 1;
    float s = kind == BURST_SHORTS ? float(SHORTS) : uBus.y * float(SHORTS);
    for (int i = 0; i < SHORTS; i++) {
        float w = clamp(s - float(i), 0.0, 1.0);
        if (w <= 0.0) break;
        if (w < 1.0) {                                       // touching on and off, a piece at a time
            uint id = uint(k >> PIECE) * 8u + uint(i), c = uint(cam);
            float life = 0.5 + die(id, c, 21u);
            uint ep = uint(floor(uBus2.y / life + die(id, c, 22u)));
            if (die(id, ep, c) >= w) continue;
        }
        ivec3 f = LOT[cam * SHORTS + i];                     // how, line a, line b
        int ba = (v >> f.y) & 1, bb = (v >> f.z) & 1;
        if (f.x == 0) v &= ~(1 << f.y);                      // grounded
        else if (f.x == 1) v |= 1 << f.y;                    // tied to power
        else {                                               // bridged: both read the lower, or the higher
            int both = f.x == 2 ? (ba & bb) : (ba | bb);
            v = (v & ~((1 << f.y) | (1 << f.z))) | (both << f.y) | (both << f.z);
        }
    }
    return v;
}

// Whether byte i falls in a slip placed by the dice (seed): most are a stretch of the line where the clock gained a
// tick and later lost one (or lost one and later gained it), placed so every part of the line is as likely to be
// in one; TO_END of them never recover and run to the line's end. +1 or -1 inside, 0 outside.
int slip(int i, uint seed) {
    float len = float(L) * (0.05 + 0.45 * die(seed, 1u, 39u) * die(seed, 2u, 39u));
    bool toEnd = die(seed, 3u, 39u) < TO_END;
    float x0 = toEnd ? die(seed, 4u, 39u) * float(L) : die(seed, 4u, 39u) * (float(L) + len) - len;
    float x1 = toEnd ? float(L) : x0 + len;
    return float(i) >= x0 && float(i) < x1 ? (die(seed, 5u, 39u) < 0.5 ? -1 : 1) : 0;
}

// How many places the pixel clock has slipped on line n at byte i.
int clockSlip(int n, int i) {
    float rate = 0.35 * uBus.w * uBus.w;
    int off = 0;
    if (uBus2.z > 0.5) {                                     // the beat's sliver, while the beat is fresh
        uint b = uint(uBus2.w + 0.5);
        int top = int(die(b, 36u, 0u) * float(H - BEAT_LINES));
        if (n >= top && n < top + BEAT_LINES) off += slip(i, ihash(b * 0x27d4eb2du + uint(n)));
    }
    for (int s = 0; s < SLIPS; s++) {
        uint id = uint(n * SLIPS + s);
        float life = 0.4 + 0.8 * die(id, 31u, 0u);
        uint ep = uint(floor(uBus2.y / life + die(id, 32u, 0u)));
        if (die(id, ep, 33u) < rate) off += slip(i, ihash(id * 0x9E3779B9u ^ ep));
    }
    return off;
}

int bridgeByte(int start, int n, int i) {
    int k = wrap(start + i + clockSlip(n, i));
    return bend(sensorByte(k), k);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    W = int(uTDOutputInfo.res.z);
    H = int(uTDOutputInfo.res.w);
    L = 2 * W;
    kind = burstKind(uBurst.x, uBurst.y, uBurst.z);
    int n = lineOf(p, H), pair = p.x >> 1;
    float drift = uBus2.x * uBus2.x * float(W);              // Sync: bytes the frame drifts by, top to bottom
    int start = n * L + int(floor(float(n) * drift / float(H))) + int(uBus.z + 0.5) + (kind == BURST_SLIP ? 1 : 0);
    if (kind == BURST_FRAME) start += int(FRAME_SLIP * float(H)) * L + int(uBurst.y + 0.5) % 4;
    float y = float(bridgeByte(start, n, 4 * pair + 2 * (p.x & 1)));
    float u = float(bridgeByte(start, n, 4 * pair + 1));
    float v = float(bridgeByte(start, n, 4 * pair + 3));
    fragColor = vec4(vec3(y, u, v) / 255.0, 1.0);
}
