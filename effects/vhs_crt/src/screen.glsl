// VHS + CRT (touchdesigner-effects, MIT). The tube. Each of the Lines lines is drawn by an electron beam
// whose spot is a Gaussian: the brighter the line, the more current and the wider the spot, so dark lines
// leave black gaps between them and bright ones fill them in. Red, green and blue share the width of the
// brightest of them: then every pixel mixes whole line colors, and the red guard in signal.glsl holds.
// The beam keeps the line's light (the spot's area is the line's brightness), so scanlines darken nothing
// overall. The light then passes the phosphor mask: aperture grille stripes, a slot mask's staggered slots
// or a shadow mask's dot triads, Mask Size pixels a triad at 720 high, each color brighter on its own
// phosphor and darker on the others (mean 1). Glow spreads light inside the glass (halation): the
// picture blurred, mixed in. Curvature bows the face and rounds its corners. Light is linear in here.
// Inputs: 0 the picture (for the output's size), 1 the signal (R'G'B', one row a line), 2 the glow
// (linear light, blurred). With Screen off: the signal, stretched to the output. Last, the red guard
// (red_guard.glsl) on every pixel.
uniform vec4 uScr;    // x Screen on, y Mask (0 Aperture Grille, 1 Slot Mask, 2 Shadow Mask, 3 None), z Mask Size, w Scanlines
uniform vec4 uScr2;   // x Lines, y Curvature, z Glow
out vec4 fragColor;
#define PI 3.14159265
#define GAMMA 2.2
#define MASK 0.5      // each color's phosphor 1 + MASK bright, the others' 1 - MASK / 2

vec3 lineColor(float L, float u, float N) {
    vec3 c = texture(sTD2DInputs[1], vec2(u, 1.0 - (L + 0.5) / N)).rgb;
    return pow(max(c, 0.0), vec3(GAMMA));
}

void main() {
    if (uScr.x < 0.5) {
        vec3 c = redGuard(pow(max(texture(sTD2DInputs[1], vUV.st).rgb, 0.0), vec3(GAMMA)));
        fragColor = vec4(pow(c, vec3(1.0 / GAMMA)), 1.0);
        return;
    }
    vec2 res = uTD2DInfos[0].res.zw;
    float N = uScr2.x, curv = uScr2.y;

    // The face: bowed, its corners rounded, its edge soft over a pixel, darker toward the corners.
    vec2 c = vUV.st * 2.0 - 1.0;
    c *= 1.0 + c.yx * c.yx * curv * vec2(0.04 * res.y / res.x, 0.06);
    vec2 q = c * 0.5 + 0.5;
    vec2 e = (1.0 - abs(c)) * res * 0.5;                    // pixels to each edge
    float r = max((0.01 + 0.06 * curv) * res.y, 1.0);
    float inside = min(min(e.x, e.y), r - length(max(vec2(r) - e, 0.0)));
    float face = clamp(inside + 0.5, 0.0, 1.0) * (1.0 - 0.3 * curv * dot(c, c) * 0.5);

    // The beams of the four lines nearest.
    float yl = (1.0 - q.y) * N - 0.5, L0 = floor(yl);
    vec3 acc = vec3(0.0);
    for (int i = -1; i <= 2; i++) {
        float L = L0 + float(i);
        if (L < 0.0 || L > N - 1.0) continue;
        float d = yl - L;
        vec3 col = lineColor(L, q.x, N);
        float sg = mix(0.55, 0.16 + 0.3 * sqrt(max(col.r, max(col.g, col.b))), uScr.w);   // spot size, in line pitches
        acc += col * exp(-0.5 * d * d / (sg * sg)) / (sg * 2.5066);
    }

    // The mask, in output pixels.
    vec3 m = vec3(1.0);
    int mt = int(uScr.y + 0.5);
    if (mt < 3) {
        float P = max(uScr.z * res.y / 720.0, 2.0);
        vec2 fp = gl_FragCoord.xy;
        float vm = 1.0;
        if (mt == 1) {                                      // slot mask: slots 2 triads tall, every other column half down
            float H = 2.0 * P;
            float y = fp.y + mod(floor(fp.x / P), 2.0) * H * 0.5;
            vm = 1.0 + 0.35 * cos(2.0 * PI * y / H);
        } else if (mt == 2) {                               // shadow mask: rows of dot triads, every other row half over
            float H = P * 0.866;
            fp.x += mod(floor(fp.y / H), 2.0) * P * 0.5;
            vm = 1.0 + 0.35 * cos(2.0 * PI * fp.y / H);
        }
        m = (1.0 + MASK * cos(2.0 * PI * (fp.x / P - vec3(0.0, 1.0, 2.0) / 3.0))) * vm;
    }
    vec3 lin = mix(acc * m, texture(sTD2DInputs[2], q).rgb, 0.4 * uScr2.z) * face;
    fragColor = vec4(pow(redGuard(clamp(lin, 0.0, 1.0)), vec3(1.0 / GAMMA)), 1.0);
}
