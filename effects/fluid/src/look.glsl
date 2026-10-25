// Fluid (touchdesigner-effects, MIT): what the fluid carries, drawn over the picture (dimmed by
// Backdrop). Ink: its colors, opaque where it is thick. Smoke: soft and see-through (it absorbs light
// as it thickens, after the Beer-Lambert law), lit from above left by the slope of its thickness, so
// its billows show. Fire: its heat as flame colors, orange through yellow to white,
// brighter as it is hotter, added onto the picture. A beat's puff (uL.z, through the flash gate) makes the
// flames burn hotter and the smoke catch more light for a moment.
// Inputs: 0 the picture, 1 the dye (rgb color times amount, a amount).
uniform vec4 uL;   // x: Look (0 Ink, 1 Smoke, 2 Fire), y: Backdrop, z: a beat's puff now (0-1, times Beat Puffs)
out vec4 fragColor;
#define FIRE_GLOW 1.2
#define SMOKE_GLOW 0.6

// A flame's color by its heat, 0 to 1. Its coolest is orange, never red: green stays at least 0.6 of red
// (0.33 of it in linear light), so red is at most 75% of the three in linear light, under the 80% at
// which WCAG 2.3.1 counts a color as saturated red (its red flash threshold is stricter). Flickering red
// flame edges measured 2.5 red flashes a second with Flashing Off, and dark orange (green at 0.35 of red,
// 0.1 in linear light) still 2.0 (dev/flash.py on the dancer).
vec3 flame(float t) {
    float r = smoothstep(0.0, 0.35, t);
    return vec3(r, r * (0.6 + 0.3 * smoothstep(0.2, 0.8, t)), 0.75 * smoothstep(0.55, 1.0, t)) * (0.4 + 0.8 * t);
}

void main() {
    vec2 uv = vUV.st;
    vec3 back = texture(sTD2DInputs[0], uv).rgb * uL.y;
    vec4 d = texture(sTD2DInputs[1], uv);
    vec3 col = d.rgb / max(d.a, 1e-3);
    vec3 c;
    if (uL.x < 0.5) {
        c = mix(back, col, clamp(d.a * 1.4, 0.0, 1.0));
    } else if (uL.x < 1.5) {
        vec2 px = 3.0 * uTD2DInfos[1].res.xy;
        vec2 slope = 0.5 * vec2(texture(sTD2DInputs[1], uv + vec2(px.x, 0.0)).a - texture(sTD2DInputs[1], uv - vec2(px.x, 0.0)).a,
                                texture(sTD2DInputs[1], uv + vec2(0.0, px.y)).a - texture(sTD2DInputs[1], uv - vec2(0.0, px.y)).a);
        float lit = clamp(0.85 + 6.0 * dot(slope, vec2(0.6, -0.8)), 0.45, 1.3);
        float alpha = 1.0 - exp(-1.0 * d.a);
        c = back * (1.0 - alpha) + col * lit * (1.0 + SMOKE_GLOW * uL.z) * alpha;
    } else {
        c = back + flame(min(d.a * (1.0 + FIRE_GLOW * uL.z), 1.0));
    }
    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
