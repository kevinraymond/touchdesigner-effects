// DEV ONLY (blob round 1, variant E "grid"): GPU-only detection, no Blob Track TOP and no data
// leaving the GPU. Four passes picked by PASS (the builder defines it):
//   1 energy: per grid cell, mean motion (frame difference), mean and max brightness
//   2 smooth: temporal low-pass of the energy grid (input 1 = its own last frame)
//   3 peaks:  cells that are local maxima above a threshold, and each one's nearest other peak
//   4 draw:   boxes sized by score, links to the nearest peak, cell labels, score bars
uniform float uTime;
uniform vec4 uP;      // x threshold, y motion weight, z highlight weight, w highlight knee
uniform vec4 uLook;   // x label scale, y smoothing (pass 2)
out vec4 fragColor;

#if PASS == 1
void main() {
    ivec2 cell = ivec2(gl_FragCoord.xy);
    vec2 inRes = uTD2DInfos[0].res.zw;
    vec2 cs = inRes / uTDOutputInfo.res.zw;
    float mot = 0.0, br = 0.0, mx = 0.0;
    for (int y = 0; y < 8; y++) for (int x = 0; x < 8; x++) {
        vec2 uv = (vec2(cell) + (vec2(x, y) + 0.5) / 8.0) * cs / inRes;
        float a = lum(texture(sTD2DInputs[0], uv).rgb), b = lum(texture(sTD2DInputs[1], uv).rgb);
        mot += abs(a - b); br += a; mx = max(mx, a);
    }
    fragColor = vec4(mot / 64.0, br / 64.0, mx, 1.0);
}
#elif PASS == 2
void main() {
    vec4 cur = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    vec4 old = texelFetch(sTD2DInputs[1], ivec2(gl_FragCoord.xy), 0);
    fragColor = mix(old, cur, uLook.y);
}
#elif PASS == 3
ivec2 G;
float score(ivec2 c) {
    if (any(lessThan(c, ivec2(0))) || any(greaterThanEqual(c, G))) return 0.0;
    vec4 e = texelFetch(sTD2DInputs[0], c, 0);
    return e.x * uP.y + max(e.z - uP.w, 0.0) * uP.z;
}
bool isPeak(ivec2 c) {
    float s = score(c);
    if (s < uP.x) return false;
    for (int y = -2; y <= 2; y++) for (int x = -2; x <= 2; x++) {
        if (x == 0 && y == 0) continue;
        float o = score(c + ivec2(x, y));
        if (o > s || (o == s && (y * 5 + x) < 0)) return false;
    }
    return true;
}
void main() {
    G = ivec2(uTDOutputInfo.res.zw);
    ivec2 c = ivec2(gl_FragCoord.xy);
    if (!isPeak(c)) { fragColor = vec4(0.0); return; }
    float best = 1e9; vec2 off = vec2(0.0);
    for (int y = -5; y <= 5; y++) for (int x = -5; x <= 5; x++) {
        if (x == 0 && y == 0) continue;
        float d = length(vec2(x, y) * vec2(1.0, 1.0));
        if (d < best && isPeak(c + ivec2(x, y))) { best = d; off = vec2(x, y); }
    }
    fragColor = vec4(score(c), off, 1.0);
}
#else
const vec3 ORANGE = vec3(1.0, 0.6, 0.18);
const vec3 BLUE = vec3(0.4, 0.65, 1.0);
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    ivec2 G = textureSize(sTD2DInputs[1], 0);
    vec2 cs = res / vec2(G);
    ivec2 me = ivec2(px / cs);
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 col = vec3(lum(src)) * 0.6;
    vec2 gq = abs(fract(px / cs + 0.5) - 0.5) * cs;
    if (length(gq) < 0.9) col = mix(col, BLUE, 0.45);
    float s = uLook.x;
    float inside = 0.0, edge = 0.0, link = 0.0, bar = 0.0, txt = 0.0, plt = 0.0;
    for (int y = -5; y <= 5; y++) for (int x = -5; x <= 5; x++) {
        ivec2 cc = me + ivec2(x, y);
        if (any(lessThan(cc, ivec2(0))) || any(greaterThanEqual(cc, G))) continue;
        vec4 pk = texelFetch(sTD2DInputs[1], cc, 0);
        if (pk.w < 0.5) continue;
        vec2 c = (vec2(cc) + 0.5) * cs;
        float sc = clamp(pk.x / (uP.x * 4.0), 0.0, 1.0);
        vec2 hs = cs * (0.55 + 1.6 * sc);
        vec2 d = abs(px - c) - hs;
        float m = max(d.x, d.y);
        if (m < 0.0) { inside = 1.0; if (m > -1.0) edge = 1.0; }
        if (pk.y != 0.0 || pk.z != 0.0) {
            vec2 c2 = c + pk.yz * cs;
            link = max(link, 1.0 - smoothstep(0.2, 1.0, segDist(px, c, c2)));
        }
        if (px.x > c.x + hs.x + 2.0 && px.x < c.x + hs.x + 4.0 && px.y > c.y - hs.y && px.y < c.y - hs.y + 2.0 * hs.y * sc) bar = 1.0;
        ivec2 gp;
        vec2 o = vec2(c.x - hs.x, c.y + hs.y + 2.0 * s);
        int ci = textCell(px, o, s, 6, gp);
        plt = max(plt, plate(px, o, s, 6));
        if (ci >= 0) {
            int g = ci == 0 ? 27 : ci == 1 ? digitOf(cc.y, 1) : ci == 2 ? digitOf(cc.y, 0)
                  : ci == 3 ? 12 : ci == 4 ? digitOf(cc.x, 1) : digitOf(cc.x, 0);    // R07C12
            txt = max(txt, glyphPix(g, gp));
        }
    }
    col = mix(col, vec3(lum(src)) * 1.15, inside);
    col = mix(col, BLUE, link * 0.85 * (1.0 - inside));
    col = mix(col, vec3(1.0), edge);
    col = mix(col, ORANGE, bar);
    col = mix(col, col * 0.15, plt * 0.85);
    col = mix(col, vec3(0.85, 0.92, 1.0), txt);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
#endif
