// touchdesigner-effects (MIT), Temporal Resonator: the picture with the strings' echoes added behind whatever stands
// out from the background now, so the live subject stays in front of its own echoes. An echo moves a red near WCAG's
// saturated-red line back and forth across it (the red flowers measured half a red flash a second more than the clip),
// so every pixel goes through lib red_guard.glsl, as Slit-Scan's and Motion Magnify's do. Guarding only where an echo
// showed switched the guard on and off as echoes came and went, which flipped reds across the line more often still
// (the flowers, 2 red flashes a second against the clip's 1).
// Inputs: 0 the picture, 1 the echo (string.glsl's buffer 1: rgb the echo, signed; a what stands out now), at the
// ring's size and read smoothly.
// Out: the picture.
uniform vec4 uE;   // x Strength: how bright the echoes show
out vec4 fragColor;

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void main() {
    vec4 x = texture(sTD2DInputs[0], vUV.st);
    vec4 r = texture(sTD2DInputs[1], vUV.st);
    vec3 add = uE.x * r.rgb * (1.0 - r.a);
    vec3 c = toSRGB(redGuard(toLinear(clamp(x.rgb + add, 0.0, 1.0))));
    fragColor = TDOutputSwizzle(vec4(c, x.a));
}
