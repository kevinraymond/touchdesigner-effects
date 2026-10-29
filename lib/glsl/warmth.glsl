// touchdesigner-effects (MIT), shared by the effects whose picture warms what it touches (lib/glsl, warmth()):
// Frost thaws by it. One heat field from what stands out in front (or inside the mask) and what moves, each
// spread a little around itself, eased so it rises quickly and falls slowly: a hand that moves warms the glass
// at once and leaves it to cool behind it. A clip slower than the project repeats each frame (change reads 0
// between its frames), so the movement is held from the last new frame rather than read as stillness. On the first
// frame (the feedback's alpha is 0) the change is against nothing, so nothing has moved yet. A change below a dead
// zone warms nothing: haze drifting through a dark room changes it a little everywhere.
// Inputs: 0 what stands out or the mask (r 0-1; sets the size), 1 the change since the last frame (lib
// change.glsl: r |change|, at 1/8), 2 the clock (lib clock.glsl: r 1 on a new input frame), 3 this pass's last
// output (Feedback TOP).
// Out: r the warmth 0-1, g the movement held from the last new frame.
uniform vec4 uW;   // x how much what stands out warms, y how much movement warms, z the change that warms fully,
                   // w the change below which nothing warms
uniform vec4 uR;   // x this frame's step (s), y the time to rise (s), z the time to fall (s)
out vec4 fragColor;

// A 3 x 3 tent around uv in input i's texels: what warms spreads a little around itself.
float spread(int i, vec2 uv) {
    vec2 o = uTD2DInfos[i].res.xy;
    float s = 4.0 * texture(sTD2DInputs[i], uv).r;
    s += 2.0 * (texture(sTD2DInputs[i], uv + vec2(o.x, 0.0)).r + texture(sTD2DInputs[i], uv - vec2(o.x, 0.0)).r
              + texture(sTD2DInputs[i], uv + vec2(0.0, o.y)).r + texture(sTD2DInputs[i], uv - vec2(0.0, o.y)).r);
    s += texture(sTD2DInputs[i], uv + o).r + texture(sTD2DInputs[i], uv - o).r
       + texture(sTD2DInputs[i], uv + vec2(o.x, -o.y)).r + texture(sTD2DInputs[i], uv + vec2(-o.x, o.y)).r;
    return s / 16.0;
}

void main() {
    vec2 uv = vUV.st;
    vec4 last = texture(sTD2DInputs[3], uv);
    bool fresh = texelFetch(sTD2DInputs[2], ivec2(0), 0).r > 0.5;
    float moved = last.a == 0.0 ? 0.0 : fresh ? smoothstep(uW.w, uW.z, spread(1, uv)) : last.g;
    float target = max(uW.x * spread(0, uv), uW.y * moved);
    float t = target > last.r ? uR.y : uR.z;
    float w = mix(target, last.r, exp(-uR.x / max(t, 1e-3)));
    fragColor = vec4(w, moved, 0.0, 1.0);
}
