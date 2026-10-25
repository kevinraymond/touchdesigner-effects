// Bent Cam (touchdesigner-effects, MIT). The bridge compresses each frame as a JPEG, as USB webcams send Motion
// JPEG. It cuts the brightness into blocks of 8 x 8 pixels and each color difference into blocks of 16 x 8 (the
// stream's U and V already cover pairs of pixels). It turns each block into its 64 cosine coefficients (the DCT)
// and rounds them to steps from the JPEG standard's tables, coarser as Compression rises (quality 100 down to 5),
// which is what makes blocks and ringing. Then the USB cable loses bits (Block Errors): the decoder misreads the
// stream from some block on. Each block's average is stored as a change from the block before, so every block
// after the error is off by its errors added up, and their detail turns to stripes, up to the next restart marker,
// which puts the decoder right (every RESTART blocks). A burst's error runs to the end of the frame.
// Each error holds still while it lasts, and each lasts a while.
// Inputs: 0 Y, U, V (bytes / 255). Out: at each pixel, the coefficient of its own place in its blocks: r for the
// brightness block (u, v the pixel's place in its 8 x 8 block), g and b for the color blocks (u is half the
// pixel's place across its 16 x 8 block).
uniform vec4 uJpg;    // x Compression 0-1, y Block Errors 0-1, z seconds (lib clock_seconds())
uniform vec4 uBurst;  // x the burst's envelope (0-1), y its number, z 1 if it was a drop's
out vec4 fragColor;
#define DC_STEP 160.0     // how far a misread average may go each block, in DC units (8 per level of the byte)
#define AC_AMP 3.0        // a misread coefficient: up to this many of its own steps, either way
#define AC_HIT 0.25       // the share of a damaged block's coefficients that are misread
#define RESTART 8         // blocks (16 x 8 pixels) between the stream's restart markers

// The JPEG standard's quantization tables (ITU-T T.81, Annex K), row by row (v, then u).
const float QY[64] = float[64](16., 11., 10., 16., 24., 40., 51., 61., 12., 12., 14., 19., 26., 58., 60., 55.,
    14., 13., 16., 24., 40., 57., 69., 56., 14., 17., 22., 29., 51., 87., 80., 62., 18., 22., 37., 56., 68., 109., 103., 77.,
    24., 35., 55., 64., 81., 104., 113., 92., 49., 64., 78., 87., 103., 121., 120., 101., 72., 92., 95., 98., 112., 100., 103., 99.);
const float QC[64] = float[64](17., 18., 24., 47., 99., 99., 99., 99., 18., 21., 26., 66., 99., 99., 99., 99.,
    24., 26., 56., 99., 99., 99., 99., 99., 47., 66., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99.,
    99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99., 99.);

// A table's step at quality q (1-100), as the Independent JPEG Group's libjpeg scales it.
float qstep(float t, float q) {
    float s = q < 50.0 ? 5000.0 / q : 200.0 - 2.0 * q;
    return clamp(floor((t * s + 50.0) / 100.0), 1.0, 255.0);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    int W = int(uTDOutputInfo.res.z), H = int(uTDOutputInfo.res.w);
    int n = lineOf(p, H), x = p.x;
    int u = x & 7, uc = (x & 15) >> 1, v = n & 7, x0 = x & ~7, xc0 = x & ~15, y0 = n & ~7;
    float cu[8], cuc[8], cv[8];
    for (int i = 0; i < 8; i++) {
        cu[i] = cos(float(2 * i + 1) * float(u) * PI / 16.0);
        cuc[i] = cos(float(2 * i + 1) * float(uc) * PI / 16.0);
        cv[i] = cos(float(2 * i + 1) * float(v) * PI / 16.0);
    }
    vec3 F = vec3(0.0);
    for (int j = 0; j < 8; j++) {
        int row = H - 1 - min(y0 + j, H - 1);                // past the frame's edge, its last line again
        for (int i = 0; i < 8; i++) {
            float yb = texelFetch(sTD2DInputs[0], ivec2(min(x0 + i, W - 1), row), 0).r;
            vec2 c = texelFetch(sTD2DInputs[0], ivec2(min(xc0 + 2 * i, W - 1), row), 0).gb;
            F.x += (yb * 255.0 - 128.0) * cu[i] * cv[j];
            F.yz += (c * 255.0 - 128.0) * cuc[i] * cv[j];
        }
    }
    float s = 0.25 * (v == 0 ? 0.70710678 : 1.0);
    F *= vec3(s * (u == 0 ? 0.70710678 : 1.0), vec2(s * (uc == 0 ? 0.70710678 : 1.0)));
    float q = 100.0 - 95.0 * uJpg.x;
    vec3 Q = vec3(qstep(QY[v * 8 + u], q), vec2(qstep(QC[v * 8 + uc], q)));
    F = round(F / Q) * Q;

    // Block errors. The stream has a restart marker every RESTART blocks (16 x 8 pixels each, in reading order),
    // where the decoder starts afresh: a steady error runs from its block to the next marker. A burst's runs from
    // a block in the top half to the end of the frame, as if the decoder never found another marker.
    int mcuW = (W + 15) / 16, mx = x >> 4, row = n >> 3, rows = (H + 7) / 8, g = row * mcuW + mx;
    int from = -1;
    uint seed = 0u;
    uint iv = uint(g / RESTART);
    float life = 0.3 + 0.7 * die(iv, 41u, 0u);
    uint ep = uint(floor(uJpg.z / life + die(iv, 42u, 0u)));
    if (die(iv, ep, 43u) < 0.3 * uJpg.y * uJpg.y) {
        from = int(iv) * RESTART + int(die(iv, ep, 44u) * float(RESTART));
        seed = ihash(iv * 7919u + ep);
    }
    if (burstKind(uBurst.x, uBurst.y, uBurst.z) == BURST_BLOCKS) {
        uint b = uint(uBurst.y + 0.5);
        int g0 = int(die(b, 45u, 0u) * 0.5 * float(rows)) * mcuW + int(die(b, 46u, 0u) * float(mcuW));
        if (g >= g0) {
            from = max(g0, row * mcuW);                      // its drift is walked from the row's start
            seed = ihash(b * 104729u + uint(row));
        }
    }
    if (from >= 0 && g >= from) {
        vec3 dc = vec3(0.0);
        for (int j = from; j <= g; j++)
            dc += vec3(die(seed, uint(j), 1u), die(seed, uint(j), 2u), die(seed, uint(j), 3u)) - 0.5;
        if (u == 0 && v == 0) F.x += 2.0 * DC_STEP * dc.x;
        if (uc == 0 && v == 0) F.yz += 2.0 * DC_STEP * dc.yz;
        uint by = uint(x >> 3), slot = uint(v * 8 + u), slotc = uint(v * 8 + uc);
        if ((u > 0 || v > 0) && die(seed ^ by, slot, 4u) < AC_HIT)
            F.x += (die(seed ^ by, slot, 5u) - 0.5) * 2.0 * AC_AMP * Q.x;
        if ((uc > 0 || v > 0) && die(seed ^ uint(mx), slotc, 6u) < AC_HIT)
            F.yz += (vec2(die(seed ^ uint(mx), slotc, 7u), die(seed ^ uint(mx), slotc, 8u)) - 0.5) * 2.0 * AC_AMP * Q.yz;
    }
    fragColor = vec4(F, 1.0);
}
