// VHS + CRT (touchdesigner-effects, MIT). The plasma panel. Each color of each pixel is a small cell of gas
// whose discharge lights a phosphor, and a cell is either lit or dark: a gray is made by lighting it in some of
// the frame's sub-fields, pulses of 1, 2, 4 ... 128 units of light one after another (a binary code, 8
// sub-fields), or, as later panels did, 1 to 16 and then up to seven of 32 (12 sub-fields, a redundant code).
// A cell's light is linear, so the signal goes to linear light and 256 steps, dithered where the darkest steps
// would band (a pattern that moves every field, the shimmer in a plasma's shadows). A still picture looks right.
// But an eye that follows something moving adds up each frame's pulses along its own path, from different
// cells: where a moving gradient crosses a value at which the code changes a lot (127 to 128: 1 to 64 go off,
// 128 comes on), it sees light or dark bands that aren't in the picture (dynamic false contours). So each
// sub-field is read here where the eye is when it lights, from the picture's motion (lib speed.glsl), at the
// panel's 60 frames a second. The green phosphor glows on after each pulse (about 10 ms to a tenth), the red a
// little less, the blue hardly at all (1 ms or less), so half of each pulse's red and green is read where the eye
// is twice the phosphor's decay time later (its light's middle one decay time late): a moving light thing trails
// yellow and leads blue. Then the cells (three side by side inside their ribs), the front glass's glow,
// and last the red guard (red_guard.glsl) on every pixel.
// Inputs: 0 the picture (for the output's size), 1 the signal (R'G'B', one row a line), 2 the glow (linear,
// blurred), 3 the motion (lib speed.glsl: rg cells per second, its cells a quarter of the picture's).
// Out: R'G'B' and 1.
uniform vec4 uPl;   // x Mask Size, y Sub-Fields (0 binary, 1 redundant), z Glow, w the panel's frame (mod 4096,
                    // counted in Python: a 32-bit float of the seconds is only good to milliseconds after hours)
out vec4 fragColor;
#define RATE 60.0       // the panel's frames a second
#define ADDRESS 0.3     // of a frame spent addressing the cells, shared among the sub-fields; the rest is light
// Twice each phosphor's decay time, in frames: green 4.3 ms (10 ms to a tenth), red taken as 2.6 ms (6 ms to a
// tenth; no figure found), blue none.
#define LAG vec3(0.31, 0.52, 0.0)
#define COLOR 0.3       // how much of the colors' stripes shows; the rest is even light
#define GAP 0.6         // and of the ribs between rows
#define LIT_X 0.7       // each cell lit over this much of its width (the ribs between them)
#define LIT_Y 0.75      // and of its height
#define BLACK 0.002     // a dark cell's glow (the priming discharge), of white

const float W8[8] = float[8](1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0);
const float W12[12] = float[12](1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0, 32.0);

// Each color's step, 0-255, of the cell under p (output pixels), dithered.
ivec3 level(vec2 p, float P, vec2 res, float field) {
    ivec2 cell = ivec2(floor(p / P));
    vec3 c = pow(clamp(texture(sTD2DInputs[1], (vec2(cell) + 0.5) * P / res).rgb, 0.0, 1.0), vec3(GAMMA));
    float d = fract(bayer4(cell) + 0.618034 * field);
    return ivec3(clamp(floor(c * 255.0 + d), 0.0, 255.0));
}

// Whether sub-field k is lit for step v.
float lit(int v, int k, bool redundant) {
    if (!redundant || k < 5) return float((v >> k) & 1);
    return k - 5 < (v >> 5) ? 1.0 : 0.0;
}

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    float P = pitch(uPl.x, res);
    bool redundant = uPl.y > 0.5;
    int n = redundant ? 12 : 8;
    float field = uPl.w;
    vec2 v = texture(sTD2DInputs[3], vUV.st).rg * res / uTD2DInfos[3].res.zw / RATE;   // pixels a frame
    float A = ADDRESS / float(n), S = (1.0 - ADDRESS) / 255.0, t = 0.0;
    vec3 acc = vec3(0.0);
    for (int k = 0; k < n; k++) {
        float w = redundant ? W12[k] : W8[k];
        float tk = t + A + 0.5 * w * S - 0.5;                // the middle of its light, from the frame's middle
        t += A + w * S;
        ivec3 now = level(gl_FragCoord.xy + v * tk, P, res, field);
        ivec3 r = level(gl_FragCoord.xy + v * (tk + LAG.r), P, res, field);
        ivec3 g = level(gl_FragCoord.xy + v * (tk + LAG.g), P, res, field);
        acc += w * vec3(0.5 * (lit(now.r, k, redundant) + lit(r.r, k, redundant)),
                        0.5 * (lit(now.g, k, redundant) + lit(g.g, k, redundant)),
                        lit(now.b, k, redundant));
    }
    vec3 lin = (BLACK + (1.0 - BLACK) * acc / 255.0) * cells(gl_FragCoord.xy, P, LIT_X, LIT_Y, COLOR, GAP);
    lin = mix(lin, texture(sTD2DInputs[2], vUV.st).rgb, 0.3 * uPl.z);
    fragColor = vec4(pow(redGuard(clamp(lin, 0.0, 1.0)), vec3(1.0 / GAMMA)), 1.0);
}
