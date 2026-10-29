// touchdesigner-effects (MIT), Relight: the picture lit again. Its colors are the surface's, in linear light, with its
// own lighting flattened by Flatten: where it is brighter than its average, divided down toward it by its blurred
// brightness, or by its own where that is lower, so a dark pixel beside a bright one isn't dimmed with it (the blur
// alone ringed a lit hand with black); never lifted, since a video's darks are mostly noise and blocks. The light is
// the ambient (Ambient) and the lights' (scattered under the surface), both darkened by the occlusion; each light adds
// a highlight, GGX's microfacet distribution with Smith's shadowing and Schlick's Fresnel for a dielectric (F0 0.04),
// the view straight down, Specular of it. Bright light rolls off above 0.8 instead of clipping, and every pixel goes
// through the red guard: colored light on red flowers or skin moves reds across WCAG's saturated-red line.
// Inputs: 0 the picture, 1 the light (sss.glsl), 2 the surface, 3 the shadows, 4 the lights, 5 the picture's brightness
// blurred, 6 its average (1 x 1); 1-3 and 5 smaller, read smoothly.
// Out: the picture.
uniform vec4 uL;   // x Ambient, y Specular, z roughness, w Flatten
uniform vec4 uE;   // x the lamps' falloff radius (a share of the picture's height)
out vec4 fragColor;
#define PI 3.14159265

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

float ggx(float nh, float nl, float nv, float vh, float rough) {
    float a = rough * rough, a2 = a * a, k = a * 0.5;
    float d = a2 / (PI * pow(nh * nh * (a2 - 1.0) + 1.0, 2.0));
    float g = nl / (nl * (1.0 - k) + k) * nv / (nv * (1.0 - k) + k);
    float f = 0.04 + 0.96 * pow(1.0 - vh, 5.0);
    return d * g * f / max(4.0 * nl * nv, 1e-4);
}

void main() {
    vec2 uv = vUV.st;
    vec4 pic = texture(sTD2DInputs[0], uv);
    float shade = texture(sTD2DInputs[5], uv).r, avg = texelFetch(sTD2DInputs[6], ivec2(0), 0).r;
    vec3 lin = toLinear(pic.rgb);
    float own = dot(lin, vec3(0.2126, 0.7152, 0.0722));
    vec3 albedo = lin * pow(clamp((avg + 0.05) / max(min(shade, own), 1e-3), 0.25, 1.0), uL.w);
    vec2 res = vec2(textureSize(sTD2DInputs[2], 0));
    vec4 s = texture(sTD2DInputs[2], uv), through = texture(sTD2DInputs[3], uv);
    vec3 n = normalOf(s), spec = vec3(0.0);
    vec3 p = vec3(uv * res, s.r);
    for (int i = 0; i < 4; i++) {
        vec3 col = lightColor(i);
        if (max(max(col.r, col.g), col.b) <= 0.0) continue;
        vec4 l = toLight(i, p, res, uE.x * res.y);
        float nl = dot(n, l.xyz);
        if (nl <= 0.0) continue;
        vec3 hv = normalize(l.xyz + vec3(0.0, 0.0, 1.0));
        spec += col * l.w * through[i] * nl * ggx(max(dot(n, hv), 0.0), nl, max(n.z, 1e-3), max(hv.z, 0.0), uL.z);
    }
    vec3 c = albedo * (uL.x + texture(sTD2DInputs[1], uv).rgb) * s.a + spec * uL.y;
    c = mix(c, 0.8 + 0.2 * (1.0 - exp(-(c - 0.8) / 0.2)), step(0.8, c));
    c = toSRGB(redGuard(max(c, 0.0)));
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), pic.a));
}
