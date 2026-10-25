// Fluid (touchdesigner-effects, MIT): one step of the air's (or water's) velocity, before it is made
// incompressible. Stable fluids (J. Stam, "Stable Fluids", SIGGRAPH 1999; on the GPU as in M. Harris,
// "Fast Fluid Dynamics Simulation on the GPU", GPU Gems ch. 38, 2004): the velocity is carried along
// by itself (semi-Lagrangian: each cell looks back along its velocity and takes what was there),
// curls are kept alive by vorticity confinement (R. Fedkiw, J. Stam, H. W. Jensen, "Visual
// Simulation of Smoke", SIGGRAPH 2001), what the fluid carries rises by its amount (buoyancy, as in
// the same paper), and the input's motion drags the fluid along where the input moves. Velocities
// are in grid cells per second, y up.
// Inputs: 0 the input's motion (motion.glsl; sets the size), 1 the velocity last frame (Feedback TOP),
// 2 the dye last frame (a: how much ink, smoke or heat is there).
uniform vec4 uT;   // x: this frame's step (s)
uniform vec4 uF;   // x: Push, y: swirl (vorticity confinement, frame heights per second), z: rise (frame heights
                   // per second^2 where the dye is full), w: the velocity's half-life (s)
out vec4 fragColor;
#define MAX_SPEED 4.0

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
    vec2 f = uF.y * h * w * vec2(n.y, -n.x);

    f.y += uF.z * h * texture(sTD2DInputs[2], uv).a;
    v += f * dt;

    // Where the input moves (and the flow is sure of it), the fluid is dragged along with it.
    vec4 m = texture(sTD2DInputs[0], uv);
    float sure = smoothstep(2e-4, 1e-3, m.b) * smoothstep(0.02, 0.08, length(m.rg) * px.y);   // frame heights / s
    v = mix(v, m.rg * uF.x, 1.0 - exp(-dt * 30.0 * sure));

    v *= exp2(-dt / uF.w);
    // Never faster than MAX_SPEED frame heights a second.
    float s = length(v);
    if (s > MAX_SPEED * h) v *= MAX_SPEED * h / s;
    fragColor = vec4(v, 0.0, 1.0);
}
