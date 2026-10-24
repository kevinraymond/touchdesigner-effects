// Depth Particles (touchdesigner-effects, MIT). The output: the particles (drawn additively, so
// where many overlap they glow) and their glow, over the picture dimmed to Backdrop, or with Show on
// People, what the effect takes for the people: the picture dimmed, the people in orange and the
// depth's brightness beside them in blue, to tune Find, Stand Out and Far Limit by.
// Inputs: 0 the picture; 1 the particles; 2 the particles, blurred; 3 the people (find.glsl).
uniform vec4 uLook;   // x Backdrop, y Glow, z Show (0 particles, 1 people)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec3 pic = texture(sTD2DInputs[0], uv).rgb;
    if (uLook.z > 0.5) {
        vec4 f = texture(sTD2DInputs[3], uv);
        vec3 c = pic * 0.3 + vec3(0.25, 0.55, 1.0) * 0.35 * f.g * (1.0 - f.r);
        fragColor = TDOutputSwizzle(vec4(mix(c, vec3(1.0, 0.55, 0.15), 0.85 * f.r), 1.0));
        return;
    }
    vec3 lit = texture(sTD2DInputs[1], uv).rgb + uLook.y * texture(sTD2DInputs[2], uv).rgb;
    lit = 1.0 - exp(-1.5 * lit);                     // many overlapping particles saturate softly
    vec3 c = 1.0 - (1.0 - pic * uLook.x) * (1.0 - lit);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
