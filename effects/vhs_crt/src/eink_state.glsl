// VHS + CRT (touchdesigner-effects, MIT). The e-ink panel's state. E-ink is ink, not light: black and white
// particles in tiny capsules, pulled to the front or the back by the voltage under each pixel, staying where they
// were left. Changing a pixel takes a waveform of pulses lasting a good fraction of a second, so video on it is a
// run of updates, each starting as the last one ends, as fast as Ink Mode's waveform allows (E Ink's modes, as the
// IT8951 controller lists them): 16 Grays after GL16 (450 ms), 4 Grays after DU4 (290 ms), Fast after A2 (120 ms,
// black or white only, dithered here). Each update drives only the pixels that change (a partial update), straight
// to their new gray and never quite there: some of the gray before stays behind (a ghost), carrying a share of the
// ghost before it, and where a pixel doesn't change again its ghost stays, so the ghosts of where things were pile
// up. A full refresh (each burst) drives every pixel to black and back, and the picture comes back clean. Which
// update it is comes from the clock in Python's double precision (Ink Mode's waveform time sets the updates), the
// same number for this pass and eink.glsl: a 32-bit float of the seconds since TouchDesigner started is only good
// to a few milliseconds after some hours, and two passes working the update out from it disagreed near its start
// (this pass then missed the update, and the face replayed the last one: a flash). Each pixel keeps the number of
// the update it last took, so a cook missed or repeated never takes one twice or loses one.
// Inputs: 0 the picture (for the output's size), 1 the signal (R'G'B', one row a line), 2 this pass's last
// frame (Feedback TOP). Out, in grays (0 black, 1 white): r where this update started from, g the gray it drives
// to, b its ghost, a the number of the update it took (mod 1024, exact in 16 bits). eink.glsl shows it.
uniform vec4 uInk;   // x this update's number (mod 1024), y how far through it (0-1), z Ink Mode (0 16 grays,
                     // 1 4 grays, 2 fast), w Ghosting
uniform vec4 uInk2;  // x the full refresh, 0-1 (1 at its blackest)
out vec4 fragColor;
const float LEVELS[3] = float[3](16.0, 4.0, 2.0);
const float GHOST[3] = float[3](0.12, 0.15, 0.18);  // of each step left behind at Ghosting 0.5 (twice at 1)

void main() {
    int m = int(uInk.z + 0.5);
    float n = LEVELS[m] - 1.0;
    vec4 s = texture(sTD2DInputs[2], vUV.st);
    float y = dot(clamp(texture(sTD2DInputs[1], vUV.st).rgb, 0.0, 1.0), vec3(0.299, 0.587, 0.114));
    float want = clamp(floor(y * n + bayer4(ivec2(gl_FragCoord.xy))) / n, 0.0, 1.0);
    if (abs(s.a - uInk.x) > 0.5) {                             // an update this pixel hasn't taken yet
        s.r = s.g + s.b;                                        // the last one has finished
        if (abs(want - s.g) > 0.5 / n) {                       // the pixel changes: drive it
            s.b = 2.0 * GHOST[m] * uInk.w * (s.g + s.b - want);
            s.g = want;
        }
        s.a = uInk.x;
    }
    if (uInk2.x > 0.95) s = vec4(want, want, 0.0, uInk.x);     // a full refresh at its blackest: clean
    fragColor = s;
}
