// touchdesigner-effects (MIT), Relight: reading the lights (lights.glsl's 4 x 2 texture), pasted in front of the
// shaders that light the surface, after the builder defines LIGHTS as the input that holds them.
// Row 0, light i: a lamp's place (x, y as a share of the picture, z its height as a share of the picture's height,
// w 1), or a sun's direction (xyz toward the sun, unit, w 0). Row 1: its color times its intensity (0: no light).

vec4 lightPlace(int i) { return texelFetch(LIGHTS, ivec2(i, 0), 0); }
vec3 lightColor(int i) { return texelFetch(LIGHTS, ivec2(i, 1), 0).rgb; }

// From p (x, y in pixels of a pass the size res, z the surface's height in the same pixels): the direction toward
// light i (xyz, unit) and how much of it arrives (w): a lamp falls off with distance past radius pixels, a sun doesn't.
vec4 toLight(int i, vec3 p, vec2 res, float radius) {
    vec4 l = lightPlace(i);
    if (l.w < 0.5) return vec4(l.xyz, 1.0);
    vec3 d = vec3(l.xy * res, l.z * res.y) - p;
    float dist = max(length(d), 1e-3), q = dist / radius;
    return vec4(d / dist, 1.0 / (1.0 + q * q));
}

// The surface's normal from surface.glsl's g and b.
vec3 normalOf(vec4 s) { return vec3(s.g, s.b, sqrt(max(1.0 - s.g * s.g - s.b * s.b, 0.0))); }
