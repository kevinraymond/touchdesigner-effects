// DEV ONLY (blob round 1, variant D "beat"): blue/orange duotone; orange boxes; each label a
// word that is redrawn on every beat; a line from each blob to a partner that changes on every
// beat, bright on the beat and faint between; on a beat (rate-limited by the Trigger CHOP's
// Re-Trigger Delay = the Flashing setting) the boxes fill with their inverted contents.
// Inputs: 0 picture, 1 blob table (unpack.glsl). The builder prepends WORDS / NWORDS.
uniform float uTime;
uniform vec4 uBeat;   // x flash envelope 0-1, y beat count, z bass level 0-1, w flashing allowed 0/1
uniform vec4 uLook;   // x label scale, y link floor opacity
out vec4 fragColor;

const vec3 ORANGE = vec3(1.0, 0.6, 0.18);
const vec3 DEEP = vec3(0.02, 0.06, 0.2);
const vec3 WARM = vec3(1.0, 0.86, 0.66);

float linkInk(vec2 px, vec2 a, vec2 b) {
    vec2 lo = min(a, b) - 2.0, hi = max(a, b) + 2.0;
    if (any(lessThan(px, lo)) || any(greaterThan(px, hi))) return 0.0;
    return 1.0 - smoothstep(0.2, 1.1, segDist(px, a, b));
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    vec3 src = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 col = mix(DEEP, WARM, smoothstep(0.04, 0.9, lum(src)));
    int n = nPacked();
    int beat = int(uBeat.y + 0.5);
    float env = uBeat.x * uBeat.w;
    float s = uLook.x;
    float lw = 1.0 + step(0.6, uBeat.z);
    float inside = 0.0, edge = 0.0, link = 0.0, word = 0.0, plt = 0.0;
    for (int i = 0; i < n; i++) {
        vec4 b = P(i, 0), m1 = P(i, 1);
        vec2 c = b.xy * res;
        vec2 hs = max(b.zw * res * 0.5, vec2(4.0));
        vec2 d = abs(px - c) - hs;
        float m = max(d.x, d.y);
        if (m < 0.0) { inside = 1.0; if (m > -lw) edge = 1.0; }
        int id = int(m1.x + 0.5);
        // A quarter of the blobs get a partner line, redrawn on every beat.
        int j = (n > 1 && (ihash(id * 17 + beat) & 3) == 0) ? ihash(id * 31 + beat * 7919) % n : -1;
        if (j >= 0 && j != i) link = max(link, linkInk(px, c, P(j, 0).xy * res) * mix(uLook.y, 1.0, uBeat.x));
        if (m1.y >= 0.0) link = max(link, linkInk(px, c, P(int(m1.y), 0).xy * res) * uLook.y);
        if (abs(px.y - c.y) > hs.y + 12.0 * s || px.x < c.x - hs.x - 2.0 || px.x > c.x - hs.x + 44.0 * s) continue;
        ivec2 gp;
        vec2 o = vec2(c.x - hs.x, c.y + hs.y + 2.0 * s);
        int ci = textCell(px, o, s, 4, gp);
        plt = max(plt, plate(px, o, s, 4));
        int w = (ihash(id * 131 + beat) >> 8) % NWORDS;
        if (ci >= 0) word = max(word, glyphPix(WORDS[w * 4 + ci], gp));
    }
    col = mix(col, 1.0 - col, inside * env);
    col = mix(col, WARM, link * (1.0 - inside));
    col = mix(col, ORANGE, edge);
    col = mix(col, DEEP * 0.5, plt * 0.85);
    col = mix(col, vec3(1.0), word);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
