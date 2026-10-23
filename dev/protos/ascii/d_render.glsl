// DEV ONLY (ASCII round 1), variant D: rain. Each column carries two falling trails of random
// glyphs that change a few times a second (orange, heads paler); between trails the picture is a
// dim blue luminance ramp. The picture's luminance also sets the trails' brightness.
uniform float uScale;
uniform float uTime;       // seconds
#define STATS 1
//@LEVELS
uniform vec3 uHead;
uniform vec3 uTrail;
uniform vec3 uBack;
out vec4 fragColor;
//@FONT
// Integer hash: the "lowbias32" mixer from Chris Wellons' hash-prospector (public domain, Unlicense).
uint mixbits(uint x) {
    x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16;
    return x;
}
float hash(int a, int b, int c) {
    return float(mixbits(uint(a) * 0x9e3779b1u ^ mixbits(uint(b) + 0x632be5abu) ^ mixbits(uint(c) * 0x85ebca77u)) >> 8) / 16777216.0;
}
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 cs = vec2(6.0, 9.0) * uScale;
    vec2 p = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
    ivec2 cell = ivec2(floor(p / cs));
    ivec2 fp = ivec2(floor((p - vec2(cell) * cs) / uScale)) - ivec2(0, 1);
    vec4 c = texelFetch(sTD2DInputs[0], cell, 0);
    float l = level(c.a);
    float rows = ceil(res.y / cs.y);
    float trail = 0.0, head = 0.0;
    for (int k = 0; k < 2; k++) {
        float speed = mix(4.0, 12.0, hash(cell.x, k, 1));    // rows per second
        float len = mix(8.0, 24.0, hash(cell.x, k, 2));
        float span = rows + len + mix(4.0, 40.0, hash(cell.x, k, 3));
        float d = mod(uTime * speed + hash(cell.x, k, 4) * span, span) - float(cell.y);
        if (d >= 0.0 && d < len) {
            float t = 1.0 - d / len;
            trail = max(trail, t * t);
            if (d < 1.0) head = 1.0;
        }
    }
    int flick = int(floor(uTime * mix(2.0, 7.0, hash(cell.x, cell.y, 5)) + hash(cell.x, cell.y, 6) * 10.0));
    int rg = RAIN[int(hash(cell.x, cell.y, 7 + flick) * float(RAIN.length()))];
    int bg = RAMP[clamp(int(l * float(RAMP.length())), 0, RAMP.length() - 1)];
    bool rain = trail > 0.06;
    vec3 col = rain ? mix(uTrail * (0.2 + 0.8 * trail) * (0.12 + 0.88 * l), uHead * (0.3 + 0.7 * l), head)
                    : uBack * (0.2 + 0.8 * l) * step(0.04, l);
    fragColor = TDOutputSwizzle(vec4(col * glyph(rain ? rg : bg, fp), 1.0));
}
