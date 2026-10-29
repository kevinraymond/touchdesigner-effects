// Frost (touchdesigner-effects, MIT): the Fog style drawn over the picture (fog_atlas.glsl says how the droplets are
// kept). Each droplet is a small lens: through it the picture behind shows shrunk and turned over, its rim dark where
// the light behind is bent away, with a glint of the room's light. Droplets too small to see one by one (under
// TINY pixels) fog the glass between the big ones as a milky haze that scatters the light, the picture's spread wide
// and a little of the room's, so the fog glows where a lamp is behind it. The haze follows how much of the glass the
// small droplets cover.
// Inputs: 0 the picture (mipmapped), 1 the droplets (fog_level.glsl's).
uniform vec4 uL;   // x Ice (how thick the haze is, 0-1), y Glow (how much the light behind shows through, 0-1),
                   // z the room's light the fog scatters
uniform vec4 uTint;   // rgb the fog's color
uniform vec4 uB;   // x a beat's glint now: how much brighter the droplets' glints
out vec4 fragColor;

#define TINY 1.5        // droplets smaller than this (pixels) make the haze, bigger ones are drawn as lenses
#define SPREAD 3.0      // how much wider than itself a droplet sees of the picture behind it
#define WIDE 6.0        // the light behind, spread wide: this mip level

void main() {
    N = textureSize(sTD2DInputs[1], 0).x;
    ASP = aspect(0);
    vec2 res = uTDOutputInfo.res.zw;
    float px = 1.0 / max(res.x, res.y);              // a pixel, in the droplets' units
    vec2 uv = vUV.st;
    vec2 p = uv * ASP;
    vec4 best = vec4(0.0);
    for (int k = 0; k < LEVELS; k++) {
        ivec2 cc = cellof(k, p);
        for (int y = -1; y <= 1; y++)
            for (int x = -1; x <= 1; x++) {
                vec4 d = drop(1, k, cc + ivec2(x, y));
                if (d.b > best.b && distance(d.xy, p) < d.b + px) best = d;
            }
    }
    // the haze: how much of the glass around (level 0's 3 x 3 cells) the droplets too small to see cover
    float cs = cellsize(0), cover = 0.0;
    ivec2 c0 = cellof(0, p);
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++) {
            vec4 d = drop(1, 0, c0 + ivec2(x, y));
            if (d.b > 0.0 && d.b < TINY * px) cover += 3.14159 * d.b * d.b;
        }
    cover = clamp(cover / (9.0 * cs * cs) * 2.0, 0.0, 1.0);
    vec3 pic = texture(sTD2DInputs[0], uv).rgb;
    float wide = luma(textureLod(sTD2DInputs[0], uv, WIDE).rgb);
    vec3 light = uTint.rgb * (uL.z + uL.y * 1.6 * wide);
    vec3 blur = textureLod(sTD2DInputs[0], uv, 3.0).rgb;
    vec3 c = mix(pic, blur * 0.7 + light * 0.45, cover * uL.x);
    if (best.b >= TINY * px) {
        vec2 u = (p - best.xy) / best.b;
        float q = dot(u, u);
        vec2 seen = (best.xy - u * best.b * SPREAD) / ASP;
        vec3 through = textureLod(sTD2DInputs[0], seen, 1.5).rgb;
        float rim = pow(smoothstep(0.5, 1.0, q), 1.5);
        float glint = pow(max(1.0 - length(u - vec2(-0.35, 0.4)) / 0.3, 0.0), 2.0);
        vec3 drop = through * (1.0 - 0.7 * rim) + light * (0.25 + 0.8 * glint * (1.0 + uB.x));
        float inside = 1.0 - smoothstep(best.b - px, best.b + px, distance(p, best.xy));
        c = mix(c, drop, inside);
    }
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), 1.0));
}
