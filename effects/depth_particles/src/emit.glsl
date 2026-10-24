// Depth Particles (touchdesigner-effects, MIT). Where particles may be born. An Analyze TOP
// averages this over the frame, which gives how much of the frame each kind of emitter covers
// (sim.glsl paces emission with it) and the people's middle (where a drop's shockwave starts).
// Inputs: 0 the people (find.glsl).
// Out: r 1 inside the people; g 1 on their outline (inside, with outside within 2 pixels);
// b and a r times this pixel's position (u, v), for the middle.
out vec4 fragColor;

float inside(ivec2 q) {
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    return texelFetch(sTD2DInputs[0], clamp(q, ivec2(0), size - 1), 0).r;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float m = inside(p);
    float around = min(min(inside(p + ivec2(2, 0)), inside(p - ivec2(2, 0))),
                       min(inside(p + ivec2(0, 2)), inside(p - ivec2(0, 2))));
    vec2 uv = (vec2(p) + 0.5) / uTDOutputInfo.res.zw;
    fragColor = vec4(m, m * (1.0 - around), m * uv);
}
