// VHS + CRT (touchdesigner-effects, MIT). The cable to the TV and the TV's decoder. Composite puts color on
// a 3.58 MHz subcarrier on top of the brightness (NTSC: Y + I cos + Q sin, its phase turning half a cycle
// every line) and the TV pulls them apart again: a notch filter takes the subcarrier out of the brightness,
// and multiplying by the subcarrier and lowpassing brings the color back. Neither is clean: color left in
// the brightness shows as dots along colored edges, and fine brightness detail near the subcarrier's
// frequency turns into color (rainbows). Broadcast NTSC also turns the phase half a cycle every field, so
// the dots crawl and the rainbows flicker 30 times a second: on fine detail in saturated red, a flash in
// every part of the picture (WCAG 2.3.1). Here the phase holds still from field to field: the dots stay
// put and the rainbows don't flicker. S-Video keeps brightness and color on their own wires: no dots,
// color still soft. RGB: the picture as it comes.
// Last, the red guard (red_guard.glsl).
// Inputs: 0 the tape's output (Y, I, Q); 1 the picture, for its aspect. Out: R'G'B' and 1.
uniform vec4 uSig;    // x Signal (0 Composite, 1 S-Video, 2 RGB), z Lines
out vec4 fragColor;
#define PI 3.14159265
#define US_PER_H 39.45
#define FSC 3.579545    // NTSC's color subcarrier, MHz
#define CHROMA_BW 1.0   // the TV's chroma lowpass, MHz (3 dB down)
#define GAMMA 2.2

vec3 at(int x, int y, int W) { return x >= 0 && x < W ? texelFetch(sTD2DInputs[0], ivec2(x, y), 0).xyz : vec3(0.0); }

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    int W = int(uTD2DInfos[0].res.z);
    float texH = (uTD2DInfos[1].res.z / uTD2DInfos[1].res.w) / float(W);
    vec3 yiq = at(p.x, p.y, W);
    int mode = int(uSig.x + 0.5);
    if (mode < 2) {
        // A Gaussian lowpass 3 dB down at CHROMA_BW: sigma = 0.1325 / f.
        float sg = 0.1325 / (CHROMA_BW * US_PER_H) / texH;
        int J = int(ceil(3.0 * sg));
        if (mode == 0) {
            float fs = FSC * US_PER_H * texH;               // subcarrier cycles per sample
            int L = int(uSig.z) - 1 - p.y;
            float ph0 = PI * float(L & 1);
            int K = int(ceil(1.5 / fs));                    // the notch: 1.5 subcarrier cycles each side
            int R = max(J, K);
            float bp = 0.0, wb = 0.0, wg = 0.0, s0 = 0.0;
            vec2 iq = vec2(0.0);
            for (int k = -R; k <= R; k++) {
                vec3 c = at(p.x + k, p.y, W);
                float ph = 2.0 * PI * fs * float(p.x + k) + ph0;
                float s = c.x + c.y * cos(ph) + c.z * sin(ph);   // the composite signal
                if (k == 0) s0 = s;
                if (abs(k) <= K) {
                    float w = 0.5 + 0.5 * cos(PI * float(k) / float(K + 1));
                    bp += w * cos(2.0 * PI * fs * float(k)) * s; wb += w;
                }
                if (abs(k) <= J) {
                    float g = exp(-0.5 * float(k * k) / (sg * sg));
                    iq += g * 2.0 * s * vec2(cos(ph), sin(ph)); wg += g;
                }
            }
            yiq = vec3(s0 - 2.0 * bp / wb, iq / wg);
        } else {
            vec2 iq = vec2(0.0);
            float wg = 0.0;
            for (int k = -J; k <= J; k++) {
                float g = exp(-0.5 * float(k * k) / (sg * sg));
                iq += g * at(p.x + k, p.y, W).yz; wg += g;
            }
            yiq.yz = iq / wg;
        }
    }
    mat3 toRGB = mat3(1.0, 1.0, 1.0, 0.956, -0.272, -1.106, 0.619, -0.647, 1.703);
    vec3 lin = redGuard(pow(clamp(toRGB * yiq, 0.0, 1.0), vec3(GAMMA)));
    fragColor = vec4(pow(lin, vec3(1.0 / GAMMA)), 1.0);
}
