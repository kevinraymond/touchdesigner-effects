// touchdesigner-effects (MIT), Caustics: the pool's floor (the picture) seen from above through the water. The view,
// straight down, refracts through the surface's slope, so the floor wobbles under the waves, by Refraction of what the
// water's depth would bend it (the caustics need deep water, and a floor bent that far no longer reads). The floor is
// lit by the caustics where it lies, Caustics of their full strength, and its colors are absorbed by the water on the
// way, red first (Beer-Lambert: e^(-Water Color x depth x (2, 0.9, 0.5)), depth as a share of the picture's height), so
// deeper water is bluer. The sun glints on the surface where it slopes to mirror the sun up. Brightening the floor's
// reds with the moving light moves them across WCAG's saturated-red line, so every pixel goes through the red guard.
// Inputs: 0 the picture, 1 the surface (surface.glsl), 2 the caustics (caustics.glsl), both half the picture's size and
// read smoothly.
// Out: the picture.
uniform vec4 uV;   // x Refraction, y Caustics, z Water Color, w the index of refraction
uniform vec4 uL;   // xyz the sun's direction (unit, downward), w the glint's strength
out vec4 fragColor;

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void main() {
    vec2 uv = vUV.st;
    vec2 half_res = vec2(textureSize(sTD2DInputs[1], 0));
    vec4 s = texture(sTD2DInputs[1], uv);
    vec3 n = normalize(vec3(-s.g, -s.b, 1.0));
    vec3 tv = refract(vec3(0.0, 0.0, -1.0), n, 1.0 / uV.w);
    vec2 at = uv + tv.xy * uV.x * max(s.a + s.r, 0.0) / max(-tv.z, 1e-3) / half_res;
    vec4 floorc = texture(sTD2DInputs[0], at);
    vec3 light = 1.0 + uV.y * (texture(sTD2DInputs[2], at).rgb - 1.0);
    vec3 absorb = exp(-uV.z * (s.a / half_res.y) * vec3(2.0, 0.9, 0.5));
    vec3 c = floorc.rgb * max(light, 0.0) * absorb;
    vec3 mirror = reflect(uL.xyz, n);
    c += uL.w * pow(max(mirror.z, 0.0), 400.0);
    c = toSRGB(redGuard(toLinear(clamp(c, 0.0, 1.0))));
    fragColor = TDOutputSwizzle(vec4(c, floorc.a));
}
