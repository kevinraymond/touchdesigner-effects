// DEV ONLY (blob round 1, variant A "trace"): the classic look in one pass. Gray picture, thin
// white boxes with inverted insides, links to each blob's two nearest neighbors, an ID label
// above each box and its coordinates below.
// Inputs: 0 picture, 1 blob table (unpack.glsl).
uniform float uTime;
uniform vec4 uLook;   // x outline width px, y label scale, z inside invert 0-1, w link opacity
uniform vec4 uLook2;  // x min box size (px) for the coordinate label
out vec4 fragColor;

const vec3 ORANGE = vec3(1.0, 0.6, 0.18);

int coordChar(int ci, vec2 uv) {
    int ux = int(uv.x * 100.0), vy = int(uv.y * 100.0);
    if (ci == 0) return CH_X;
    if (ci == 1) return digitOf(ux, 1);
    if (ci == 2) return digitOf(ux, 0);
    if (ci == 3) return CH_SP;
    if (ci == 4) return CH_Y;
    if (ci == 5) return digitOf(vy, 1);
    return digitOf(vy, 0);
}

float linkInk(vec2 px, vec2 a, vec2 b) {
    vec2 lo = min(a, b) - 2.0, hi = max(a, b) + 2.0;
    if (any(lessThan(px, lo)) || any(greaterThan(px, hi))) return 0.0;
    return 1.0 - smoothstep(0.2, 1.0, segDist(px, a, b));
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 base = vec3(smoothstep(0.02, 0.9, lum(src)));
    int n = nPacked();
    float lw = uLook.x, s = uLook.y;
    float inside = 0.0, edge = 0.0, link = 0.0, idInk = 0.0, xyInk = 0.0, plt = 0.0;
    for (int i = 0; i < n; i++) {
        vec4 b = P(i, 0), m1 = P(i, 1);
        vec2 c = b.xy * res, sz = b.zw * res;
        int id = int(m1.x + 0.5);
        vec2 hs = max(sz * 0.5, vec2(3.0));
        vec2 d = abs(px - c) - hs;
        float m = max(d.x, d.y);
        if (m < 0.0) {
            inside = 1.0;
            if (m > -lw) edge = 1.0;
        }
        if (m1.y >= 0.0) link = max(link, linkInk(px, c, P(int(m1.y), 0).xy * res));
        if (m1.z >= 0.0) link = max(link, linkInk(px, c, P(int(m1.z), 0).xy * res));
        // Labels only near the box: skip the text math elsewhere.
        if (abs(px.y - c.y) > hs.y + 12.0 * s || px.x < c.x - hs.x - 2.0 || px.x > c.x - hs.x + 44.0 * s) continue;
        ivec2 gp;
        vec2 o = vec2(c.x - hs.x, c.y + hs.y + 2.0 * s);
        int ci = textCell(px, o, s, 5, gp);
        plt = max(plt, plate(px, o, s, 5));
        if (ci >= 0) idInk = max(idInk, glyphPix(ci == 0 ? CH_HASH : digitOf(id, 4 - ci), gp));
        if (min(sz.x, sz.y) >= uLook2.x) {
            vec2 o2 = vec2(c.x - hs.x, c.y - hs.y - 9.0 * s);
            ci = textCell(px, o2, s, 7, gp);
            if (ci >= 0) xyInk = max(xyInk, glyphPix(coordChar(ci, b.xy), gp));
        }
    }
    vec3 col = mix(base, 1.0 - base, inside * uLook.z);
    col = mix(col, vec3(1.0), link * uLook.w * (1.0 - inside));
    col = mix(col, vec3(1.0), edge);
    col = mix(col, col * 0.2, plt * 0.85);
    col = mix(col, ORANGE, idInk);
    col = mix(col, vec3(0.9), xyInk);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
