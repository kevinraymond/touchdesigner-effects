// Particles (touchdesigner-effects, MIT). The air, for Behavior Push and Flow, as a stream function:
// sim.glsl takes its curl as the air's velocity. Air that moves as the curl of a field never piles up
// or thins out, and where the field holds one value the air stands still. So the field is the wind's
// own (Flow; Push has still air) plus the swirling noise, ramped down near the subject to a single value
// across it: the air goes round the subject instead of through it (Bridson, Hourihan and Nordenstam,
// "Curl-Noise for Procedural Fluid Flow", SIGGRAPH 2007, its section on boundaries). That value is the
// wind's at the middle of the subject nearby (within about a third of a frame height), which parts the
// wind evenly round one person and round each of several far enough apart; one value for all of them
// would set the air spinning round each one off the middle.
// Inputs: 0 the subject, blurred widely (how near it is); 1 emit (emit.glsl: inside, and inside times
// position), blurred more widely still: the middle of the subject nearby. Thin parts, an arm say, blur to
// less than half, so a little air passes through them (sim.glsl hides the particles behind the subject
// in Flow), and the air bends gently instead of turning sharply round them.
// Out: r the stream function (frame heights times frame heights per second).
uniform vec4 uAir;    // x, y the wind (frame heights per second, x across, y up), z swirl, w seconds
uniform vec4 uFrame;  // x aspect (width / height)
out vec4 fragColor;

// The wind's own stream function at w: its curl is the wind, the same everywhere.
float wind(vec2 w) { return uAir.x * w.y - uAir.y * w.x; }

void main() {
    vec2 uv = vUV.st;
    vec2 w = vec2((uv.x - 0.5) * uFrame.x, uv.y - 0.5);
    float near = texture(sTD2DInputs[0], uv).r;
    vec4 around = texture(sTD2DInputs[1], uv);
    vec2 mid = around.r > 1e-4 ? vec2((around.b / around.r - 0.5) * uFrame.x, around.a / around.r - 0.5) : w;
    // 1 in the open air, falling to 0 as the subject comes near and 0 across it.
    float ramp = 1.0 - smoothstep(0.0, 0.5, near);
    // The swirl: the same slowly changing noise as Emit's, about 2.5 swirls per frame height.
    float swirl = uAir.z * TDSimplexNoise(vec3(w * 2.5, uAir.w * 0.15));
    fragColor = vec4(ramp * (wind(w) + swirl) + (1.0 - ramp) * wind(mid), 0.0, 0.0, 1.0);
}
