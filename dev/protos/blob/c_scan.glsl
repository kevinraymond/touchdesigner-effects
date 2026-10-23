// DEV ONLY (blob round 1, variant C "scanner"): a dim blue-gray picture; inside each box the
// region magnified in gray with its brightest detail cut to one bit in orange, a scan line; white corner brackets
// and edge ticks; a hex tag above and the size in pixels below; dashed links to the nearest blob.
// Inputs: 0 picture, 1 blob table (unpack.glsl), 2 blurred mono (the local mean for the one-bit cut).
uniform float uTime;
uniform vec4 uLook;   // x zoom, y one-bit offset above the local mean, z label scale, w bracket length px
out vec4 fragColor;

const vec3 ORANGE = vec3(1.0, 0.6, 0.18);

int sizeChar(int ci, ivec2 wh) {     // "123X045"
    if (ci < 3) return digitOf(wh.x, 2 - ci);
    if (ci == 3) return CH_X;
    return digitOf(wh.y, 6 - ci);
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 col = lum(src) * vec3(0.42, 0.52, 0.72);
    int n = nPacked();
    float s = uLook.z;
    int hit = -1; vec2 hc = vec2(0.0), hhs = vec2(1.0); float best = 1e12;
    float br = 0.0, tick = 0.0, link = 0.0, tag = 0.0, dim = 0.0, plt = 0.0;
    for (int i = 0; i < n; i++) {
        vec4 b = P(i, 0), m1 = P(i, 1);
        vec2 c = b.xy * res;
        vec2 hs = max(b.zw * res * 0.5, vec2(6.0));
        vec2 q = abs(px - c);
        vec2 d = q - hs;
        if (max(d.x, d.y) < 0.0 && hs.x * hs.y < best) { best = hs.x * hs.y; hit = i; hc = c; hhs = hs; }
        float L = min(uLook.w, 0.6 * min(hs.x, hs.y));
        if ((abs(d.x) < 1.0 && q.y > hs.y - L && q.y < hs.y + 1.0) ||
            (abs(d.y) < 1.0 && q.x > hs.x - L && q.x < hs.x + 1.0)) br = 1.0;
        if ((q.x < 0.5 && d.y > 3.0 && d.y < 9.0) || (q.y < 0.5 && d.x > 3.0 && d.x < 9.0)) tick = 1.0;
        if (m1.y >= 0.0) {
            vec2 c2 = P(int(m1.y), 0).xy * res;
            vec2 lo = min(c, c2) - 2.0, hi = max(c, c2) + 2.0;
            if (all(greaterThan(px, lo)) && all(lessThan(px, hi))) {
                vec2 ab = c2 - c;
                float t = clamp(dot(px - c, ab) / max(dot(ab, ab), 1e-6), 0.0, 1.0);
                float dash = step(0.45, fract(t * length(ab) / 7.0 - uTime * 1.5));
                link = max(link, (1.0 - smoothstep(0.2, 1.0, segDist(px, c, c2))) * dash);
            }
        }
        if (abs(px.y - c.y) > hs.y + 12.0 * s || px.x < c.x - hs.x - 2.0 || px.x > c.x - hs.x + 44.0 * s) continue;
        int id = int(m1.x + 0.5);
        int hx = ihash(id) & 0xffff;
        ivec2 gp;
        vec2 o = vec2(c.x - hs.x, c.y + hs.y + 3.0 * s);
        int ci = textCell(px, o, s, 6, gp);
        plt = max(plt, plate(px, o, s, 6));
        if (ci >= 0) tag = max(tag, glyphPix(ci == 0 ? 0 : ci == 1 ? CH_X : hexOf(hx, 5 - ci), gp));
        vec2 o2 = vec2(c.x - hs.x, c.y - hs.y - 10.0 * s);
        ci = textCell(px, o2, s, 7, gp);
        if (ci >= 0) dim = max(dim, glyphPix(sizeChar(ci, ivec2(b.zw * res + 0.5)), gp));
    }
    if (hit >= 0) {
        vec2 zuv = (hc + (px - hc) / uLook.x) / res;
        float z = lum(texture(sTD2DInputs[0], zuv).rgb);
        float mean = texture(sTD2DInputs[2], zuv).r;
        float ink = smoothstep(-0.01, 0.01, z - mean - uLook.y);
        col = mix(vec3(0.08 + 0.5 * smoothstep(mean - 0.12, mean + 0.12, z)), ORANGE, ink);
        float sy = hc.y - hhs.y + fract(uTime * 0.4 + hash11(float(hit))) * 2.0 * hhs.y;
        col = mix(col, vec3(1.0), 0.7 * (1.0 - smoothstep(0.0, 1.5, abs(px.y - sy))));
    }
    col = mix(col, vec3(0.75, 0.85, 1.0), link * 0.7);
    col = mix(col, vec3(1.0), max(br, tick));
    col = mix(col, col * 0.15, plt * 0.9);
    col = mix(col, vec3(1.0), tag);
    col = mix(col, vec3(0.75, 0.85, 1.0), dim);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
