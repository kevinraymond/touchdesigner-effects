// touchdesigner-effects (MIT), Paint: the finished picture in the chosen style, from the painting (kuwahara.glsl)
// and the two blurs smoothed along the flow (lic.glsl). Pasted after lib common.glsl and paper.glsl.
//
// Ink lines and Ink use XDoG's soft threshold (Winnemoeller, Kyprianidis and Olsen 2012, eq. 5)
//     T(u) = 1 where u >= eps, else 1 + tanh(phi (u - eps)),
// 1 on the paper, falling smoothly to 0 in the ink. Lines darken where the plain difference of the two blurs,
// g_sigma - g_k sigma (eq. 4, tau = 1), dips below -eps: the dark side of every edge. Ink thresholds the sharpened
// brightness S = (1 + p) g_sigma - p g_k sigma (eq. 7) at eps near the picture's mean brightness, as the paper
// advises, so dark areas fill with ink and edges sharpen into lines: a woodcut.
//
// Watercolor follows Bousseau, Kaplan, Thollot and Sillion ("Interactive Watercolor Rendering with Temporal
// Coherence and Abstraction", NPAR 2006, 4.1): the painting is the abstraction; it wobbles along the paper's grain
// (offset by the gradient of the paper, coarsened); its edges darken by its symmetric gradient
// |p(x-1) - p(x+1)| + |p(y-1) - p(y+1)| averaged over R, G and B; and three gray layers T (turbulent flow: low
// gradient noise; pigment dispersion: noise at several fine scales; the paper) each change the pigment's density
// to d = 1 + beta (T - 0.5), which changes a color C to
//     C' = C (1 - (1 - C)(d - 1))      (their eq. 1: d = 2 is a second layer of the same pigment, d < 1 thinner).
// Oil changes its density the same way by a canvas weave, and Ink by the paper's grain, so all three sit on a
// surface. The paper and the pigment's layers are fixed to the frame, as paper is: the picture moves over them.
// The noise and the paper (gnoise, paper) are lib paper.glsl's, shared with Pencil.
//
// Inputs: 0 the painting, 1 the two blurs (rg), 2 the picture's mean color (1 x 1).
uniform vec4 uS;   // x: style (0 Oil, 1 Watercolor, 2 Ink), y: lines 0-1, z: eps (lines), w: phi (lines)
uniform vec4 uI;   // x: p, y: ink level (0-1, 0.5 = the picture's mean brightness), z: phi (ink), w: texture 0-1
out vec4 fragColor;

const vec3 PAPER = vec3(0.95, 0.93, 0.87);
const vec3 INK = vec3(0.07, 0.06, 0.07);

float soft(float u, float eps, float phi) {
    return u >= eps ? 1.0 : 1.0 + tanh(phi * (u - eps));
}

vec3 density(vec3 c, float t, float beta) {
    float d = 1.0 + beta * (t - 0.5);
    return c * (1.0 - (1.0 - c) * (d - 1.0));
}

void main() {
    vec2 uv = vUV.st;
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 px = uTD2DInfos[0].res.xy;
    float k720 = res.y / 720.0;
    vec2 p = uv * res / k720;                // pixels at 720 high: the paper keeps its scale at any size
    float tex = uI.w;
    int style = int(uS.x + 0.5);
    vec3 col;
    if (style == 1) {
        // Wobble: the painting read off the gradient of a coarsened paper, up to a couple of pixels.
        vec2 q = p / 6.0;
        vec2 wob = vec2(gnoise(q + vec2(0.5, 0.0)) - gnoise(q - vec2(0.5, 0.0)),
                        gnoise(q + vec2(0.0, 0.5)) - gnoise(q - vec2(0.0, 0.5)));
        vec2 at = uv + 2.5 * tex * wob * k720 * px;
        col = texture(sTD2DInputs[0], at).rgb;
        vec2 e = 1.5 * k720 * px;
        vec2 ex = vec2(e.x, 0.0), ey = vec2(0.0, e.y);
        vec3 gx = abs(texture(sTD2DInputs[0], at - ex).rgb - texture(sTD2DInputs[0], at + ex).rgb);
        vec3 gy = abs(texture(sTD2DInputs[0], at - ey).rgb - texture(sTD2DInputs[0], at + ey).rgb);
        float edge = dot(gx + gy, vec3(1.0 / 3.0));
        // A wash is thinner than the paint it stands for: lighter, the paper showing through.
        col = 1.0 - 0.88 * (1.0 - col);
        col = density(col, 0.5 + 5.0 * edge, 2.0 * tex);
        float turb = 0.5 + 0.7 * gnoise(p / 120.0) + 0.35 * gnoise(p / 50.0);
        float disp = 0.5 + 0.5 * gnoise(p / 6.0) + 0.35 * gnoise(p / 14.0);
        col = density(col, turb, 1.6 * tex);
        col = density(col, disp, 0.35 * tex);
        col = density(col, paper(p), 0.7 * tex);
    } else {
        col = texture(sTD2DInputs[0], uv).rgb;
    }
    vec2 g = texture(sTD2DInputs[1], uv).rg;
    if (style == 2) {
        vec3 mean = texelFetch(sTD2DInputs[2], ivec2(0), 0).rgb;
        float level = clamp(dot(mean, vec3(0.2126, 0.7152, 0.0722)) + (uI.y - 0.5), 0.02, 0.98);
        float s = (1.0 + uI.x) * g.r - uI.x * g.g;
        col = mix(INK, PAPER, soft(s, level, uI.z));
        col = density(col, paper(p), 0.5 * tex);
    } else {
        float line = 1.0 - soft(g.r - g.g, -uS.z, uS.w);
        col *= 1.0 - uS.y * line;
        if (style == 0) {
            // Canvas: a plain weave about 4 pixels a thread at 720 high, its threads uneven.
            float wx = sin(3.14159 * p.x / 2.0), wy = sin(3.14159 * p.y / 2.0);
            float weave = 0.5 + 0.25 * wx * wy + 0.15 * gnoise(p / 3.0) + 0.1 * gnoise(vec2(p.x / 40.0, p.y / 2.0));
            col = density(col, weave, 0.5 * tex);
        }
    }
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
