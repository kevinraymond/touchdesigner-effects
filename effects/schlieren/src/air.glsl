// Schlieren (touchdesigner-effects, MIT): one step of the air's velocity, before it is made incompressible (lib
// incompressible()). Stable fluids (J. Stam, "Stable Fluids", SIGGRAPH 1999; on the GPU as in M. Harris, "Fast Fluid
// Dynamics Simulation on the GPU", GPU Gems ch. 38, 2004): the velocity is carried along by itself (semi-Lagrangian),
// its curls kept alive by vorticity confinement (R. Fedkiw, J. Stam, H. W. Jensen, "Visual Simulation of Smoke",
// SIGGRAPH 2001). Three things push it: the lift above what is warm (lift.glsl, from the picture's warmth, never from
// the heat the air carries), a beat's puff, which throws the warm air up at once so it rolls up into eddies, and the
// picture's movement, which drags the air along where something moves. A puff is as strong as asked where a small
// share of the picture is warm (a person, a hand) and weaker where more of it is, so it never heaves the whole frame's
// air at once (flowers swaying in the wind, all warm, flashed whole on every puff). Velocities are in grid cells a
// second, y up.
// Inputs: 0 the lift (lift.glsl: r the lift, g the warmth; sets the size), 1 the velocity last frame (Feedback TOP),
// 2 the picture's movement (lib flow_speed(): rg cells a second at its own size, b how sure), 3 how much of the picture
// is warm (an Analyze TOP's average of the warmth: r, one pixel).
uniform vec4 uT;   // x this frame's step (s), y Rise (frame heights a second^2 where the lift is 1), z swirl (frame
                   // heights), w the velocity's half-life (s)
uniform vec4 uP;   // x Stir, y a beat's puff now (frame heights a second^2 where it is warm)
out vec4 fragColor;
#define MAX_SPEED 0.4   // frame heights a second: real plumes rise a few tenths of a meter a second; air at up to 1 frame
                        // height a second (Rise 1) swept the relief past the flash test's cells 3 times a second over
                        // red flowers swaying in the wind, with Flashing Off
#define PUFF_AREA 0.05  // a puff is full strength while at most this share of the picture is warm (0.1 left red flowers
                        // swaying in the wind at the edge of Calm's limit)

vec2 vel(vec2 p) { return texture(sTD2DInputs[1], p).rg; }

// The curl of the velocity at p, per second.
float curl(vec2 p, vec2 px) {
    return 0.5 * (vel(p + vec2(px.x, 0.0)).y - vel(p - vec2(px.x, 0.0)).y
                - vel(p + vec2(0.0, px.y)).x + vel(p - vec2(0.0, px.y)).x);
}

void main() {
    float dt = uT.x;
    vec2 px = uTD2DInfos[0].res.xy;
    float h = uTD2DInfos[0].res.w;                             // the grid's height in cells
    vec2 uv = vUV.st;
    vec2 v = vel(uv - dt * vel(uv) * px);

    // Vorticity confinement: push across the gradient of |curl|, toward the middle of each swirl.
    float w = curl(uv, px);
    vec2 g = 0.5 * vec2(abs(curl(uv + vec2(px.x, 0.0), px)) - abs(curl(uv - vec2(px.x, 0.0), px)),
                        abs(curl(uv + vec2(0.0, px.y), px)) - abs(curl(uv - vec2(0.0, px.y), px)));
    vec2 n = g / (length(g) + 1e-5);
    vec2 f = uT.z * h * w * vec2(n.y, -n.x);
    vec2 lift = texture(sTD2DInputs[0], uv).rg;
    float puff = uP.y * min(1.0, PUFF_AREA / max(texelFetch(sTD2DInputs[3], ivec2(0), 0).r, 1e-4));
    f.y += h * (uT.y * lift.r + puff * lift.g);
    v += f * dt;

    // Where the picture moves (and the flow is sure of it), the air is dragged along with it.
    vec4 m = texture(sTD2DInputs[2], uv);
    vec2 mv = m.rg * h / uTD2DInfos[2].res.w;                 // into this grid's cells a second
    float sure = smoothstep(2e-4, 1e-3, m.b) * smoothstep(0.02, 0.08, length(mv) / h);
    v = mix(v, mv, 1.0 - exp(-dt * 10.0 * uP.x * sure));

    v *= exp2(-dt / uT.w);
    float s = length(v);
    if (s > MAX_SPEED * h) v *= MAX_SPEED * h / s;
    fragColor = vec4(v, 0.0, 1.0);
}
