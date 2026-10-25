// VHS + CRT (touchdesigner-effects, MIT). The deck's output filter. VHS records luma as FM on a carrier
// between 3.4 and 4.4 MHz, so after demodulating, the deck cuts everything above about 3 MHz steeply, noise
// and specks included. That keeps the luma clear of the 3.58 MHz color subcarrier, so a tape's noise doesn't
// turn into rainbows on the way to the TV, and a steep filter rings a little at edges, as decks do. A
// windowed sinc (Hann window, DECK_CYCLES cycles of the cutoff each side) on the luma; chroma passes.
// Inputs: 0 the tape (Y, I, Q); 1 the picture, for its aspect. Out: Y, I, Q, 1.
uniform vec4 uDeck;   // x Tape on
out vec4 fragColor;
#define PI 3.14159265
#define US_PER_H 39.45
#define DECK_BW 3.0       // MHz
#define DECK_CYCLES 6.0

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec4 here = texelFetch(sTD2DInputs[0], p, 0);
    if (uDeck.x < 0.5) { fragColor = here; return; }
    int W = int(uTD2DInfos[0].res.z);
    float texH = (uTD2DInfos[1].res.z / uTD2DInfos[1].res.w) / float(W);
    float fc = DECK_BW * US_PER_H * texH;                   // cycles per sample
    int R = int(ceil(DECK_CYCLES / fc));
    float acc = 0.0, wsum = 0.0;
    for (int k = -R; k <= R; k++) {
        int xs = clamp(p.x + k, 0, W - 1);
        float t = float(k);
        float w = (k == 0 ? 2.0 * fc : sin(2.0 * PI * fc * t) / (PI * t)) * (0.5 + 0.5 * cos(PI * t / float(R + 1)));
        acc += w * texelFetch(sTD2DInputs[0], ivec2(xs, p.y), 0).x;
        wsum += w;
    }
    fragColor = vec4(acc / wsum, here.yzw);
}
