// touchdesigner-effects (MIT), Scan Processor: what the yokes do to each line of the raster, one pixel a line (x = 0
// for the top line). Paik and Abe drove their Wobbulator's yokes from signal generators; here there is one generator a
// band of the music, its level that band's, each a sine of its own number of cycles down the frame (the sub bass's half
// a cycle, a bow; the brilliance's 13), and the signal is their sum laid along the raster from top to bottom, the time
// the beam takes over one field.
//   Wobbulator  each line pushed sideways by the signal (the horizontal yoke) and down or up (the vertical yoke) by the
//               same generators a quarter cycle later, each divided by its cycles, so the low bands move the lines most
//               and they bunch and spread in broad bands; a fold guard keeps a line from passing its neighbor (lines
//               crossing streaked the picture like a venetian blind); a beat bows the raster.
//   Scanimate   each line turned about the middle like a ribbon, the twist growing from the top line to the bottom
//               (Harrison's raster twist), from the low bands; the lines rippled sideways by the high ones; a beat
//               twists it further. Bend, from the middle bands, is the same for every line: a uniform of scan.glsl.
//   FM          each line's pleats shifted by the signal: the phase of the frequency modulation of the beam's sweep.
// Inputs: 0 the oscillators' phases (phase.glsl, 7 x 1).
// Out, per line: r its sideways shift as a share of the width (Wobbulator, Scanimate), or its pleats' phase in cycles
// (FM); g how far it moves down, in line spacings (Wobbulator); b its width, the cosine of its twist, negative where the
// ribbon shows its back (Scanimate; 1 otherwise).
uniform vec4 uW0;   // the bands' levels, sub bass to mid
uniform vec4 uW1;   // upper mid, presence, brilliance, the strike (signed, alternating, ringing down)
uniform vec4 uM;    // Scan (0 Wobbulator, 1 Scanimate, 2 FM), Amount, Beat Kick, seconds (wrapped)
uniform vec4 uS;    // the low, middle and high bands' levels (Scanimate), 0
out vec4 fragColor;

#define PI 3.14159265
const float CYCLES[7] = float[7](0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0);
const float SIDEWAYS = 0.1;   // Wobbulator: the sideways push at Amount 1, a share of the width a unit of signal
const float DOWN = 0.06;      // Wobbulator: the vertical yoke at Amount 1, a share of the height
const float BOW = 0.06;       // Wobbulator: a beat's bow at Beat Kick 1, a share of the width
const vec3 TWIST = vec3(0.4, 1.2, 0.6);   // Scanimate: the twist at the ends, in quarter turns: Amount x (TWIST.x +
                                          // TWIST.y x the low bands) + Beat Kick x TWIST.z x the strike
const float RIPPLE = 0.1;     // Scanimate: the high bands' sideways ripple at Amount 1, a share of the width
const float FOLD = 0.6;       // Wobbulator: the most a line moves down or up against its neighbor, in line spacings
const float REACH = 1.5;      // Wobbulator: the vertical yoke eases toward DOWN x REACH x Amount at most, which
                              // scan.glsl searches (its uR.w, set by the builder from the same numbers)

float level(int k) { return k < 4 ? uW0[k] : uW1[k - 4]; }

float signal(float u) {
    float s = 0.0;
    for (int k = 0; k < 7; k++)
        s += level(k) * sin(2.0 * PI * (CYCLES[k] * u + texelFetch(sTD2DInputs[0], ivec2(k, 0), 0).r));
    return 0.5 * s;
}

// The vertical yoke's signal: each generator a quarter cycle on and divided by its cycles, so its slope down the frame
// is at most 2 pi x 0.25 x the levels' sum (in line spacings a line, times DOWN x Amount): the fold guard's bound.
float drop(float u) {
    float s = 0.0;
    for (int k = 0; k < 7; k++)
        s += level(k) / CYCLES[k] * cos(2.0 * PI * (CYCLES[k] * u + texelFetch(sTD2DInputs[0], ivec2(k, 0), 0).r));
    return 0.25 * s;
}

void main() {
    float lines = uTDOutputInfo.res.z;
    float u = (floor(gl_FragCoord.x) + 0.5) / lines;
    int mode = int(uM.x + 0.5);
    float amount = uM.y, kick = uM.z, t = uM.w, strike = uW1.w;
    vec4 o = vec4(0.0, 0.0, 1.0, 1.0);
    if (mode == 0) {
        o.r = SIDEWAYS * amount * signal(u) + BOW * kick * strike * sin(PI * u);
        float sum = 0.0;
        for (int k = 0; k < 7; k++)
            sum += level(k);
        float slope = DOWN * amount * 0.5 * PI * sum;             // the most a line can move against the next
        float most = max(DOWN * REACH * amount * lines, 1e-3);
        o.g = most * tanh(DOWN * amount * drop(u) * lines * min(1.0, FOLD / max(slope, 1e-6)) / most);
    } else if (mode == 1) {
        float twist = amount * (TWIST.x + TWIST.y * uS.x) + kick * TWIST.z * strike;
        float theta = 0.5 * PI * twist * (2.0 * u - 1.0) + 0.3 * amount * sin(0.4 * t);
        o.b = cos(theta);
        o.r = RIPPLE * amount * uS.z * sin(2.0 * PI * (6.0 * u + 0.1 * t));
    } else {
        o.r = fract(0.08 * t) + 0.75 * signal(u);
    }
    fragColor = o;
}
