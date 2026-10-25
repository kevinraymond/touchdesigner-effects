// VHS + CRT (touchdesigner-effects, MIT). The e-ink panel's face. E-ink reflects the room's light and gives
// none, so its white is a light warm gray and its black a dark gray (Fast, after E Ink's A2, a little less of
// both); between them, each pixel eases from where its update started to the gray it is driven to (plus its
// ghosts) over the update's waveform. The capsules leave a faint, still mottle. A full refresh (each burst) takes
// it to black and back.
// Inputs: 0 the picture (for the output's size), 1 the panel's state (eink_state.glsl). Out: R'G'B' and 1.
uniform vec4 uInk;   // as eink_state.glsl: x this update's number, y how far through it, z Ink Mode
uniform vec4 uInk2;  // x the full refresh, 0-1 (1 at its blackest)
out vec4 fragColor;
#define FAST_RANGE 0.85   // Fast's black and white span this much of the others'
#define PAPER vec3(0.80, 0.80, 0.76)
#define INK vec3(0.17, 0.17, 0.18)
#define MOTTLE 0.035   // the capsules' mottle, +- half this
#define BLACK vec3(0.15)   // a full refresh at its blackest

float mottle(vec2 p) {
    vec2 c = p / 3.0, i = floor(c), f = fract(c);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash12(i), hash12(i + vec2(1.0, 0.0)), f.x),
               mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), f.x), f.y);
}

void main() {
    vec4 s = texelFetch(sTD2DInputs[1], ivec2(gl_FragCoord.xy), 0);
    int m = int(uInk.z + 0.5);
    float p = abs(s.a - uInk.x) < 0.5 ? uInk.y : 1.0;         // an update the state hasn't taken: where it ended
    float g = clamp(mix(s.r, s.g + s.b, smoothstep(0.0, 1.0, p)), 0.0, 1.0);
    if (m == 2) g = 0.5 + FAST_RANGE * (g - 0.5);
    vec3 c = mix(INK, PAPER, g) * (1.0 + MOTTLE * (mottle(gl_FragCoord.xy) - 0.5));
    fragColor = vec4(mix(c, BLACK, uInk2.x), 1.0);
}
