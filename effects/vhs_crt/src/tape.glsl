// VHS + CRT (touchdesigner-effects, MIT). The tape: what recording on VHS and playing it back does to each
// line. The deck keeps luma (brightness) to about 3 MHz and chroma (color) to about half a megahertz, a
// sixth as much, which is why colors bleed: both go through causal lowpass filters (three one-pole filters
// in a row, as analog circuits do), so edges smear to the right, never to the left, and the chroma, slow to
// settle, smears furthest. Playback sharpening adds back a bright halo to the right of edges. The noise has
// the bandwidth of its channel, so the luma's grain and the chroma's blotches stretch along the line as on
// tape. With Wear come white specks trailing off to the right, dropouts (streaks where the oxide is gone), a
// hue that wanders line by line and more of everything; where the heads mistrack, white streaks, more noise
// and the color fading out; at the head switch, a line of noise. Tape Speed (SP, LP, EP) sets the bandwidths.
// Inputs: 0 line_in (Y, I, Q); 1 the picture, for its aspect. Out: Y, I, Q, 1.
uniform vec4 uSpeed;  // x luma bandwidth (MHz, 3 dB down), y chroma bandwidth, z chroma delay (H), w sharpening
out vec4 fragColor;
#define CASCADE 0.51  // three equal one-pole lowpasses in a row are 3 dB down at 0.51 of each one's cutoff
#define MAXTAPS 96
#define SPECK 0.012   // a white speck trails off over this many H
#define SPECKS 12.0   // white specks a field at Wear 1
#define DROPOUTS 0.3  // dropouts a field at Wear 1

// The pole of a one-pole lowpass, three of which in a row are 3 dB down at mhz, for samples texH apart:
// each sample keeps this much of the last.
float pole(float mhz, float texH) { return exp(-texH * 2.0 * PI * cycH(mhz / CASCADE)); }
int taps(float b) { return min(int(12.0 / -log(b)) + 3, MAXTAPS); }
// Noise of unit variance at sample x of a line in a field.
float noiseAt(int x, uint line, uint f, uint k) { return (die(uint(x + 8192), line, f * 8u + k) - 0.5) * 3.4641; }
// A streak from x0 on: it rises over rise samples and fades over len.
float comet(float x, float x0, float rise, float len) {
    return smoothstep(x0 - rise, x0 + rise, x) * exp(-max(x - x0, 0.0) / len);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec4 here = texelFetch(sTD2DInputs[0], p, 0);
    if (uTape.x < 0.5) { fragColor = here; return; }
    int W = int(uTD2DInfos[0].res.z);
    float N = uT.y, x = float(p.x);
    int L = int(N) - 1 - p.y;
    float y = (float(L) + 0.5) / N;
    float texH = (uTD2DInfos[1].res.z / uTD2DInfos[1].res.w) / float(W);   // one sample, in H
    uint f = field(), line = uint(L);
    float wear = uTape.y, b = band(y), loud = 1.0 + 0.6 * uBurst.z;

    // Luma, through the deck's lowpass and one at half its bandwidth (the sharpening subtracts it). The
    // noise takes the narrower one's bandwidth, scaled to unit variance after it.
    float bY = pole(uSpeed.x, texH), bY2 = pole(uSpeed.x * 0.5, texH);
    float aY = 0.0, wY = 0.0, aY2 = 0.0, wY2 = 0.0, nY = 0.0, nY2 = 0.0, gY = 1.0, gY2 = 1.0;
    int n1 = taps(bY2);
    for (int n = 0; n < n1; n++) {
        int xs = p.x - n;
        float v = xs >= 0 ? texelFetch(sTD2DInputs[0], ivec2(xs, p.y), 0).x : 0.0;   // before the line: black
        float c = float((n + 1) * (n + 2)) * 0.5;           // three one-pole filters in a row
        aY += c * gY * v; wY += c * gY;
        aY2 += c * gY2 * v; wY2 += c * gY2;
        nY += c * gY2 * noiseAt(xs, line, f, 1u); nY2 += c * gY2 * c * gY2;
        gY *= bY; gY2 *= bY2;
    }
    float Yl = aY / wY;
    float sY = (0.008 + 0.035 * wear) * loud + 0.12 * b;
    float Y = Yl + uSpeed.w * (Yl - aY2 / wY2) + sY * nY / sqrt(nY2);
    float rise = 3.0 * (-1.0 / log(bY));                   // how fast the luma channel can rise, in samples

    // Chroma: the same filter at its own bandwidth. The deck makes up for the filter's delay (its mean,
    // 3 tau), all but uSpeed.z, so colors sit a little right of where they belong.
    float bC = pole(uSpeed.y, texH), tauC = -1.0 / log(bC);
    int off = int(floor(3.0 * tauC - (uSpeed.z * (0.6 + 0.8 * wear)) / texH + 0.5));
    vec2 aC = vec2(0.0), nC = vec2(0.0);
    float wC = 0.0, nC2 = 0.0, gC = 1.0;
    int n2 = taps(bC);
    for (int n = 0; n < n2; n++) {
        int xs = p.x - n + off;
        vec2 iq = (xs >= 0 && xs < W) ? texelFetch(sTD2DInputs[0], ivec2(xs, p.y), 0).yz : vec2(0.0);
        float c = float((n + 1) * (n + 2)) * 0.5 * gC;
        aC += c * iq; wC += c;
        nC += c * vec2(noiseAt(xs, line, f, 4u), noiseAt(xs, line, f, 5u)); nC2 += c * c;
        gC *= bC;
    }
    float sC = (0.008 + 0.03 * wear) * loud + 0.06 * b;
    vec2 iq = aC / wC + sC * nC / sqrt(nC2);
    // The hue wanders line by line (the color-under's phase), and tape takes a little saturation away.
    float th = 0.03 + 0.25 * wear * (die(line, f, 6u) - 0.5);
    iq = mat2(cos(th), sin(th), -sin(th), cos(th)) * iq * 0.9;
    iq *= 1.0 - 0.9 * b;                                    // mistracking loses the color first

    // White specks: a few a field, each trailing off to the right.
    float pLine = SPECKS * wear / N;
    for (uint k = 0u; k < 3u; k++) {
        if (die(line, f, 20u + k) < pLine / 3.0) {
            float x0 = die(line, f, 30u + k) * float(W);
            Y += (0.4 + 0.5 * die(line, f, 40u + k)) * comet(x, x0, rise, SPECK / texH);
        }
    }
    // Mistracking: white streaks, a few a line, of random lengths.
    if (b > 0.0) {
        uint bs = bandSeed(y);
        float w = (0.06 + 0.15 * die(line, bs, 7u)) / texH;  // the line's cells, in samples
        float sh = w * die(line, bs, 8u);
        float cell = floor((x + sh) / w);
        uint ci = uint(cell + 1.0);
        float x0 = (cell + 0.5 * die(ci, line, bs * 8u + 9u)) * w - sh;
        float len = (0.1 + 0.4 * die(ci, line, bs * 8u + 10u)) * w;
        float on = step(die(ci, line, bs * 8u + 6u), 0.6 * b) * comet(x, x0, rise, len);
        Y = mix(Y, 0.65 + 0.3 * die(ci, line, bs), on * b);
        iq *= 1.0 - on;
    }
    // Dropouts: a streak of white where the oxide is missing, fading out.
    if (die(line, f, 9u) < DROPOUTS * wear / N) {
        float x0 = die(line, f, 10u) * float(W), len = (0.03 + 0.12 * die(line, f, 11u)) / texH;
        float on = 0.85 * comet(x, x0, rise, len);
        Y = mix(Y, 0.9, on); iq *= 1.0 - on;
    }
    // The head switch's own line of noise.
    if (uTape.w > 0.5 && abs(y - (1.0 - HEAD_SWITCH)) < 0.75 / N) {
        Y = mix(Y, Y * 0.6 + 0.25 * die(uint(x / (rise + 1.0)), line, f), 0.5);
        iq *= 0.5;
    }
    fragColor = vec4(clamp(Y, -0.2, 1.3), iq, 1.0);
}
