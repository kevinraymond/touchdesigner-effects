// touchdesigner-effects (MIT), Lens Flare: shared by its shaders (pasted in front of each).
// Picture units: from the picture's middle, in units of its half diagonal, y up. The half diagonal stands for the
// lens's image height at the edge of its field (lenses.py), so a ghost lands where that lens would put it.

vec2 to_picture(vec2 pixel, vec2 res) {
    return (pixel - 0.5 * res) / (0.5 * length(res));
}

vec3 srgb_to_linear(vec3 c) {
    return mix(c / 12.92, pow((max(c, vec3(0.0)) + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

vec3 linear_to_srgb(vec3 c) {
    return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}

// The iris: a regular polygon of n blades with corners 1 from its middle, rounded toward that circle by r (0-1),
// turned by angle a (radians). iris() gives the signed distance to its edge, negative inside, in the same units. It is
// two steps, so shapes that share a direction (a ghost's three colors) share the costly part: iris_cos(), the cosine
// of the angle from the nearest blade's middle, then iris_at(), the distance at length len.
float iris_cos(float angle, float n, float a) {
    float seg = 6.2831853 / n;
    float t = angle - a;
    return cos(mod(t + 0.5 * seg, seg) - 0.5 * seg);
}

float iris_at(float len, float cos_t, float n, float r) {
    return mix(len * cos_t - cos(3.1415927 / n), len - 1.0, r);
}

float iris(vec2 p, float n, float a, float r) {
    return iris_at(length(p), iris_cos(atan(p.y, p.x), n, a), n, r);
}

// The iris's area (corners 1 from its middle), for spreading a ghost's light over it.
float iris_area(float n, float r) {
    return mix(0.5 * n * sin(6.2831853 / n), 3.1415927, r);
}
