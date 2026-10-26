// touchdesigner-effects (MIT), shared by the effects drawn on paper (lib/glsl, lib_glsl()): Paint's watercolor, ink
// and canvas, and Pencil's graphite. Pasted after common.glsl (ihash) in front of the shaders that use it.
// Noise is gradient noise after Perlin ("Improving Noise", SIGGRAPH 2002: quintic fade, hashed gradients). The paper
// is drawn here rather than loaded from a file, so it travels inside the .tox and keeps its scale at any size.

vec2 grad(ivec2 c) {
    float a = 6.2831853 * float(ihash(uint(c.x) ^ ihash(uint(c.y) + 0x9e3779b9U))) / 4294967295.0;
    return vec2(cos(a), sin(a));
}

// Gradient noise, about -0.7 to 0.7.
float gnoise(vec2 p) {
    ivec2 i = ivec2(floor(p));
    vec2 f = fract(p);
    vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
    float a = dot(grad(i), f), b = dot(grad(i + ivec2(1, 0)), f - vec2(1.0, 0.0));
    float c = dot(grad(i + ivec2(0, 1)), f - vec2(0.0, 1.0)), d = dot(grad(i + ivec2(1, 1)), f - vec2(1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// Cold-pressed paper, 0-1 around 0.5: grain a few pixels across over a gentler tooth (p in pixels at 720 high).
float paper(vec2 p) {
    return 0.5 + 0.45 * gnoise(p / 2.5) + 0.3 * gnoise(p / 7.0) + 0.15 * gnoise(p / 19.0);
}
