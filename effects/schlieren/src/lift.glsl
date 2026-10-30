// Schlieren (touchdesigner-effects, MIT): where the air rises. Air above something warm rises in a column, the lift
// falling off with height over Reach, and slow noise drifting up wavers it so the column sways and breaks into eddies.
// The lift is worked out here from the picture's warmth at its source, which is made afresh every frame and never
// carried: the heat the air carries (heat.glsl) never pushes the air. (A pending application, Huawei's US 2025/0117558,
// claims a velocity obtained from the very density field it then advects; the design keeps out of that.)
// Inputs: 0 the warmth (lib warmth(): r 0-1; sets the size; mipmapped, so each step of the march reads the warmth
// averaged over the step: read at single cells, the column came out as a ladder of bands, which the air rose in).
// Out: r the lift 0-1 and more where the noise swells it, g the warmth spread a little (for a beat's puff), b the
// warmth smoothed over about one cell of the movement's grid (an eighth of the picture's size), which heats the air:
// heat.glsl sharpens its edge, and sharpened as it was, the movement's cells came out as a grid of bumps in the heat.
uniform vec4 uL;   // x Reach (frame heights), y how much the noise wavers it 0-1, z the time (s, wrapped)
out vec4 fragColor;

#define STEPS 32
#define NOISE_CELL 0.12   // the noise's cells, frame heights
#define NOISE_RISE 0.25   // how fast the noise drifts up, frame heights a second

float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return 2.0 * mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
                     mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x), u.y) - 1.0;
}

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    // March down twice Reach: the warmest thing below, falling off with how far below it is. Below the frame is cold
    // (Input Extend Mode Zero).
    float best = 0.0;
    float lod = log2(max(2.0 * uL.x / float(STEPS) / px.y, 1.0));
    for (int k = 0; k <= STEPS; k++) {
        float d = 2.0 * uL.x * float(k) / float(STEPS);
        best = max(best, textureLod(sTD2DInputs[0], uv - vec2(0.0, d), lod).r * exp(-d / uL.x));
    }
    float n = vnoise(vec2(uv.x * uTD2DInfos[0].res.z / uTD2DInfos[0].res.w, uv.y - uL.z * NOISE_RISE) / NOISE_CELL);
    float warm = 0.0;
    for (int k = -1; k <= 1; k++)
        for (int j = -1; j <= 1; j++)
            warm += textureLod(sTD2DInputs[0], uv + 3.0 * px * vec2(k, j), 0.0).r;
    // A 5 x 5 binomial filter with its taps 2 cells apart.
    float soft = 0.0;
    float w5[5] = float[5](1.0, 4.0, 6.0, 4.0, 1.0);
    for (int k = -2; k <= 2; k++)
        for (int j = -2; j <= 2; j++)
            soft += w5[k + 2] * w5[j + 2] * textureLod(sTD2DInputs[0], uv + 2.0 * px * vec2(k, j), 0.0).r;
    fragColor = vec4(best * max(1.0 + uL.y * n, 0.0), warm / 9.0, soft / 256.0, 1.0);
}
