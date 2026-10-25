// VHS + CRT (touchdesigner-effects, MIT). The tape's first pass: the picture read line by line, as a
// deck plays it back. Each line averages the rows of the picture it covers and is read where the deck's
// unsteady time base puts it: a jitter that changes every field, the slow edge wave, the top of the frame
// bending sideways (flagging), the lines after the head switch pushed right, and lines torn sideways where
// the heads mistrack. A drop slips the picture down part of a frame, the black bar between frames
// showing above it. Out: Y, I, Q (NTSC's YIQ, from the picture's R'G'B') and 1, kept to a broadcast
// signal's bandwidths (luma 4.2 MHz, chroma 1.3) unless the Signal is RGB.
// Inputs: 0 the picture.
uniform vec4 uMode;   // x Signal (0 Composite, 1 S-Video, 2 RGB)
out vec4 fragColor;
#define LUMA_BW 4.2
#define CHROMA_BW 1.3

void main() {
    float N = uT.y, W = uTDOutputInfo.res.z;
    int L = int(N) - 1 - int(gl_FragCoord.y);                // line 0 at the top
    float y = (float(L) + 0.5) / N;
    vec2 res = uTD2DInfos[0].res.zw;
    float aspect = res.x / res.y, texH = aspect / W;
    uint f = field(), line = uint(L);
    float wear = uTape.y, t = uT.x;

    float dx = 0.0;                                          // how far right this line lands, in H
    if (uTape.x > 0.5) {
        dx += (0.0012 * wear + 0.008 * uT.z) * (die(line, f, 1u) * 2.0 - 1.0);   // a beat kicks every line sideways
        dx += 0.0025 * wear * wave(float(L) * 0.12 + t * 2.0, 3u);
        float top = clamp(1.0 - y / FLAGGING, 0.0, 1.0);
        dx -= 0.012 * wear * top * top * (0.6 + 0.4 * sin(t * 0.9));
        if (uTape.w > 0.5 && y > 1.0 - HEAD_SWITCH) {
            float k = (y - (1.0 - HEAD_SWITCH)) / HEAD_SWITCH;
            dx += (0.02 + 0.025 * k) * (1.0 + 0.4 * (die(f, 2u, 2u) - 0.5));
        }
    }
    float b = band(y);                                       // a burst tears lines with the tape off too
    uint bs = bandSeed(y);
    // The tearing: each line's own offset, which a burst holds still and the steady band lets drift
    // (smoothly, about twice a second: one that jumps every field flickers edges 30 times a second).
    float tb = bs >= 0x40000000u ? float(bs & 0xffffu) * 7.3 : t;
    float tear = bs >= 0x40000000u ? die(line, bs, 4u) * 2.0 - 1.0 : wave(t * 2.0, line + 50u);
    dx += b * (0.015 + 0.05 * b) * tear + 0.02 * b * wave(float(L) * 0.3 + tb * 2.0, 5u);

    // Gaussian lowpasses 3 dB down at the broadcast bandwidths (sigma = 0.1325 / f), in samples.
    bool rgb = uMode.x > 1.5;
    float sgY = 0.1325 / cycH(LUMA_BW) / texH, sgC = 0.1325 / cycH(CHROMA_BW) / texH;
    int K = rgb ? 0 : int(ceil(3.0 * sgC));
    int S = clamp(int(ceil(res.y / N)), 1, 8);
    mat3 toYIQ = mat3(0.299, 0.5959, 0.2115, 0.587, -0.2746, -0.5227, 0.114, -0.3213, 0.3112);
    vec3 acc = vec3(0.0);
    float wy = 0.0, wc = 0.0;
    for (int k = -K; k <= K; k++) {
        float u = vUV.s - dx / aspect + float(k) / W;
        vec3 c = vec3(0.0);
        if (u >= 0.0 && u <= 1.0) {
            for (int s = 0; s < S; s++) {
                float ys = (float(L) + (float(s) + 0.5) / float(S)) / N;
                ys = mod(ys - uT.w, 1.08);                   // a slip: 0.08 of a frame of blanking between frames
                if (ys < 1.0) c += texture(sTD2DInputs[0], vec2(u, 1.0 - ys)).rgb;
            }
            c = toYIQ * (c / float(S));
        }
        float gy = rgb ? 1.0 : exp(-0.5 * float(k * k) / (sgY * sgY)), gc = rgb ? 1.0 : exp(-0.5 * float(k * k) / (sgC * sgC));
        acc += vec3(gy * c.x, gc * c.yz);
        wy += gy; wc += gc;
    }
    fragColor = vec4(acc.x / wy, acc.yz / wc, 1.0);
}
