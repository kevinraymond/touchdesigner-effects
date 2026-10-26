// touchdesigner-effects (MIT), Pencil: the drawing. Pasted after lib common.glsl (luma, ihash) and paper.glsl (paper).
// Lu, Xu and Jia (NPAR 2012) draw a picture in pencil as the product of two layers, R = S T (eq. 10): the stroke map
// S, lines along the edges (shape.glsl's S' turned over: 1 - S' times Lines' gain, so the strongest edges come out
// darkest), and the tone T, the picture's tone (tone.glsl's table, J) drawn with pencil strokes.
// Sketch draws the tone as the paper does: with a pencil pattern H whose strokes have no one direction (strokes.glsl's
// tonal pattern, short light strokes every way), drawn over itself beta times, T = H^beta (eq. 9), where H^beta = J
// would hold. The paper solves for a smooth beta by least squares (eq. 8); here beta = ln J / ln H_blur in closed form,
// with H blurred (a mipmap level of the pattern), so beta follows the tone while H keeps its strokes. H is about as
// dark as the darkest tone wanted, so beta stays near 1 or below: a light pattern needed beta near 4 for the darks,
// which turned the strokes black and the gaps white.
// Hatching draws it as Praun et al.'s tonal art maps do ("Real-Time Hatching", SIGGRAPH 2001): the two levels of
// strokes.glsl around the tone wanted, mixed between, each level's tone read from its mipmap. Their strokes
// follow surfaces by their curvature; a picture has no surface, so here they turn along its edges (lib
// structure_tensor's flow), and where the edges have no clear direction toward a hatch at uR.z. Turning a texture
// per pixel would tear it wherever the direction changes, so it is read at the eight directions 22.5 degrees apart,
// each one turned as a whole, and each pixel mixes the two around its direction. Lines leaves the tone out.
// Graphite catches on the paper's tooth, so each mark is thinned where the paper dips (lib paper.glsl, fixed to the
// frame, as paper is). Colored Pencil keeps the picture's colors, the drawing as their brightness (the paper's 3.4,
// in YUV); Light on Dark draws white pencil on black paper, its marks where the picture is light.
// Inputs: 0 the picture, 1 and 2 strokes.glsl's buffers (rgb hatching levels 1-3 and 4-6, 1's a Sketch's pattern;
// Input Extend Mode Repeat, Input Smoothness
// Mipmap: only wired inputs get mipmaps, not those the TOPs parameter adds), 3 the strokes' darkness S' (shape.glsl),
// 4 the tone table (tone.glsl, 256 x 1), 5 the flow (rg the edges' direction, b how clear it is, a how strong; a
// constant when Hatching isn't drawn), 6 nearness (r, input 3), 7 the strokes' two offsets (drift.glsl: rg, ba, UV).
uniform vec4 uS;   // x style (0 Sketch, 1 Hatching, 2 Lines), y colors (0 Graphite, 1 Colored Pencil, 2 Blue Pencil,
                   // 3 Light on Dark), z Texture (0-1), w Stroke Size
uniform vec4 uL;   // x the lines' gain (Lines, loudness), y the tone's power (loudness: above 1 darker), z Depth Fade
                   // (0 with nothing on input 3)
uniform vec4 uR;   // xy the strokes' offset (pixels; each redraw moves it), z the hatch where the edges have no
                   // clear direction (radians), w how far each stroke texture repeats (pixels)
uniform vec4 uM;   // x the first offset's age (0-1 of drift.glsl's period), y 1 when the strokes follow movement
out vec4 fragColor;

const float PI = 3.14159265;
const float SKETCH = PI / 12.0;
const vec3 PAPER = vec3(0.96, 0.95, 0.92);
const vec3 GRAPHITE = vec3(0.16, 0.16, 0.18);
const vec3 BLUE = vec3(0.17, 0.35, 0.72);
const vec3 CHALK = vec3(0.93, 0.93, 0.90);
const vec3 BLACK_PAPER = vec3(0.07, 0.07, 0.08);

vec2 turn(vec2 p, float a) {
    float c = cos(a), s = sin(a);
    return vec2(c * p.x + s * p.y, -s * p.x + c * p.y);
}

vec2 Q0, Q1;          // where this pixel reads the strokes: carried along by each of drift.glsl's two offsets
float W1;              // how much the second offset counts (0 when the strokes don't follow movement)

// Both buffers of strokes at the pixel, turned to the direction a: read at both offsets and faded between them, so neither's
// fresh start shows.
void levels(float a, out vec4 lo, out vec4 hi) {
    vec2 t = turn(Q0, a) / uR.w;
    lo = textureLod(sTD2DInputs[1], t, 0.0);
    hi = textureLod(sTD2DInputs[2], t, 0.0);
    if (W1 > 0.0) {
        t = turn(Q1, a) / uR.w;
        lo = mix(lo, textureLod(sTD2DInputs[1], t, 0.0), W1);
        hi = mix(hi, textureLod(sTD2DInputs[2], t, 0.0), W1);
    }
}

float pick(vec4 lo, vec4 hi, int n) {
    return n < 3 ? lo[n] : hi[n - 3];
}

void main() {
    vec2 uv = vUV.st;
    vec2 res = uTD2DInfos[0].res.zw;
    float k720 = res.y / 720.0;
    vec2 p = uv * res / k720;                      // pixels at 720 high: the strokes and paper keep their size
    vec3 src = textureLod(sTD2DInputs[0], uv, 0.0).rgb;
    float l = luma(src);
    int style = int(uS.x + 0.5), colors = int(uS.y + 0.5);
    bool light = colors == 3;
    float J = textureLod(sTD2DInputs[4], vec2(((light ? 1.0 - l : l) * 255.0 + 0.5) / 256.0, 0.5), 0.0).r;
    J = pow(clamp(J, 0.0, 1.0), uL.y);
    float S = 1.0 - clamp(textureLod(sTD2DInputs[3], uv, 0.0).r * uL.x, 0.0, 1.0);
    float fade = uL.z * (1.0 - textureLod(sTD2DInputs[6], uv, 0.0).r);
    J = mix(J, 1.0, fade);
    S = mix(S, 1.0, fade);

    // The strokes in pixels at 720 high, scaled by Stroke Size and moved by each redraw; carried along with the
    // picture by drift.glsl's offsets (UV), the first counting most in the middle of its period, the second in
    // between. The paper's grain stays put.
    vec4 dr = textureLod(sTD2DInputs[7], uv, 0.0);
    float age = uM.x;
    W1 = uM.y > 0.5 ? abs(2.0 * age - 1.0) : 0.0;
    Q0 = (uv - dr.rg) * res / k720 / uS.w + uR.xy;
    Q1 = (uv - dr.ba) * res / k720 / uS.w + uR.xy;
    float T = 1.0;
    if (style == 0) {
        // The pattern turned by SKETCH, so its three families lie at 15, 60 and 150 degrees, none of them square to
        // the frame.
        vec4 a, b;
        levels(SKETCH, a, b);
        float H = min(a.a, 0.985);
        // The pattern's local mean, from mipmap level 3 (8 pixels across).
        float Hb = textureLod(sTD2DInputs[1], turn(Q0, SKETCH) / uR.w, 3.0).a;
        float beta = log(max(J, 1e-3)) / min(log(Hb), -1e-3);
        T = pow(H, beta);
    } else if (style == 1) {
        vec4 f = textureLod(sTD2DInputs[5], uv, 0.0);
        float clear = smoothstep(0.15, 0.5, f.b) * smoothstep(1e-5, 1e-4, f.a);
        // Directions at twice their angle, so a line's two ends agree; mixed toward the plain hatch where unclear.
        vec2 d2 = mix(vec2(cos(2.0 * uR.z), sin(2.0 * uR.z)), vec2(f.r * f.r - f.g * f.g, 2.0 * f.r * f.g), clear);
        float k = mod(0.5 * atan(d2.y, d2.x), PI) / (PI / 8.0);
        float k0 = floor(k), w = k - k0;
        vec4 a, b, c, d;
        levels(k0 * PI / 8.0, a, b);
        // The last direction's neighbor is the first again: the same strokes, not the texture turned half round.
        levels(mod(k0 + 1.0, 8.0) * PI / 8.0, c, d);
        vec4 lo = mix(a, c, w), hi = mix(b, d, w);
        // Each level's tone: the mipmap's 2 x 2 level read at its middle, where the filter averages all four. The 1 x 1
        // level above it reads black (2025.33230 on the M2), and so does any level asked for past it.
        float top = float(textureQueryLevels(sTD2DInputs[1]) - 2);
        vec4 mlo = textureLod(sTD2DInputs[1], vec2(0.5), top), mhi = textureLod(sTD2DInputs[2], vec2(0.5), top);
        // From the paper (tone 1, no strokes) through the six levels: the two around J, mixed by where J sits.
        float above = 1.0, last = 1.0;
        T = -1.0;
        for (int n = 0; n < 6; n++) {
            float m = pick(mlo, mhi, n), v = pick(lo, hi, n);
            if (T < 0.0 && J >= m) T = mix(v, last, (J - m) / max(above - m, 1e-4));
            above = m;
            last = v;
        }
        // Darker than the darkest level: its strokes pressed harder.
        if (T < 0.0) T = last * J / max(above, 1e-4);
    }
    float R = S * T;
    float tooth = clamp(0.5 + 1.2 * (paper(p * 1.3) - 0.5), 0.0, 1.0);
    R = 1.0 - clamp((1.0 - R) * mix(1.0, 2.0 * tooth, uS.z), 0.0, 1.0);

    vec3 col;
    if (colors == 1) col = clamp(vec3(mix(0.14, 0.96, R)) + (src - l), 0.0, 1.0);
    else if (colors == 2) col = mix(BLUE, PAPER, R);
    else if (light) col = mix(CHALK, BLACK_PAPER, R);
    else col = mix(GRAPHITE, PAPER, R);
    fragColor = vec4(col, 1.0);
}
