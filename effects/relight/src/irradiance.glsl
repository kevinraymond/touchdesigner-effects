// touchdesigner-effects (MIT), Relight: the light falling on the surface, before its color: each light's Lambert
// diffuse (the cosine of its angle to the normal), falling off with distance, through its shadow. Thin parts let light
// through from behind (after Jimenez et al., "Real-Time Realistic Skin Translucency", 2010): how far a pixel stands
// above the surface around it (surface_wide, a triangle average), as a share of its height, says how thin it is there,
// a finger more than a palm. The light from beyond its side (0.3 less the cosine, so light grazing it from behind
// counts most) comes through attenuated, blue first and red last, Glow of it. Nothing in the picture is singled out:
// every pixel is treated alike (see the patent notes on the docs page).
// Inputs: 0 the surface, 1 the shadows (smaller, read smoothly), 2 the lights, 3 the surface averaged broadly with a
// triangle filter.
// Out: rgb the light (linear), a 1.
uniform vec4 uI;   // x the lamps' falloff radius (a share of the picture's height), y Glow
out vec4 fragColor;

void main() {
    vec2 res = uTDOutputInfo.res.zw, p = gl_FragCoord.xy;
    vec4 s = texelFetch(sTD2DInputs[0], ivec2(p), 0);
    vec4 shade = texture(sTD2DInputs[1], vUV.st);
    vec3 n = normalOf(s), lit = vec3(0.0), behind = vec3(0.0);
    for (int i = 0; i < 4; i++) {
        vec3 col = lightColor(i);
        if (max(max(col.r, col.g), col.b) <= 0.0) continue;
        vec4 l = toLight(i, vec3(p, s.r), res, uI.x * res.y);
        float nl = dot(n, l.xyz);
        lit += col * l.w * shade[i] * max(nl, 0.0);
        behind += col * l.w * max(0.3 - nl, 0.0);
    }
    float thick = 1.0 - clamp((s.r - texture(sTD2DInputs[3], vUV.st).r) / max(s.r, 1.0), 0.0, 1.0);
    lit += behind * exp(-thick * thick / vec3(0.6, 0.15, 0.04)) * uI.y;
    fragColor = vec4(lit, 1.0);
}
