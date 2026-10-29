// touchdesigner-effects (MIT), Relight: light scattering under the surface, one direction a pass (across, then down),
// as Jimenez et al.'s separable subsurface scattering blurs the diffuse light in two one-dimensional passes (Computer
// Graphics Forum 34(6), 2015). Here the profile is a single Gaussian a channel, red widest (light travels furthest
// under skin, wax or marble as red), and the blur follows the surface: a sample whose height differs from this pixel's
// counts less, so light doesn't bleed across a depth edge. Scatter of the result replaces the light, the same
// everywhere.
// Inputs: 0 the light (irradiance.glsl), 1 the surface (r height).
// Out: the light, blurred along one direction.
uniform vec4 uD;   // xy the direction in pixels, z Scatter's share (0 or 1), w red's width (pixels)
out vec4 fragColor;
#define TAPS 6

void main() {
    vec2 res = uTDOutputInfo.res.zw, p = gl_FragCoord.xy;
    vec4 c = texelFetch(sTD2DInputs[0], ivec2(p), 0);
    if (uD.z <= 0.0 || uD.w <= 0.0) {
        fragColor = c;
        return;
    }
    float h = texelFetch(sTD2DInputs[1], ivec2(p), 0).r;
    vec3 width = uD.w * vec3(1.0, 0.4, 0.2), sum = c.rgb, weight = vec3(1.0);
    for (int k = -TAPS; k <= TAPS; k++) {
        if (k == 0) continue;
        float x = 2.5 * uD.w * float(k) / float(TAPS);
        vec2 q = (p + uD.xy * x) / res;
        float dh = (texture(sTD2DInputs[1], q).r - h) / max(0.5 * uD.w, 1.0);
        vec3 w = exp(-0.5 * x * x / (width * width)) * exp(-dh * dh);
        sum += texture(sTD2DInputs[0], q).rgb * w;
        weight += w;
    }
    fragColor = vec4(mix(c.rgb, sum / weight, uD.z), c.a);
}
