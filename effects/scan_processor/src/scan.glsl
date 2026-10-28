// touchdesigner-effects (MIT), Scan Processor: the raster as the beam draws it. The picture is scanned in Lines lines,
// each carrying the picture averaged over its band of rows, and the beam draws each line where the yokes put it, a
// Gaussian spot Beam x the line spacing wide. A pixel adds up the lines whose spot reaches it, so where lines bunch
// together the light piles up, and where they spread the dark between them shows, as on a CRT, whose beam spends the same
// energy on every line. Along a line the same holds: where the beam slows (FM's pleats) or a line is squeezed narrower
// (Scanimate's twist) it glows brighter, up to a cap.
//   Wobbulator  line i at its rest row plus the vertical yoke, its picture shifted sideways (mirrored past the edges).
//   Scanimate   line i narrowed about the middle by its twist's cosine, mirrored where negative (the ribbon's back,
//               a little darker), nothing beyond its ends; every line bent the same way by Bend, curving down toward
//               the sides (or up).
//   FM          the beam's sweep along line i frequency-modulated, x' = x + beta / (2 pi m) sin(2 pi (m x + phase)), m
//               pleats across, beta under 1 so the beam never runs backward; Newton's method finds the x that lands
//               on this pixel, and the light there is 1 / (1 + beta cos(...)), the beam's slowness.
// Inputs: 0 the picture, 1 the yokes (yokes.glsl, Lines x 1).
// Out: the raster, its light eased past white rather than clipped.
uniform vec4 uR;    // Lines, Beam (the spot's width as a share of the line spacing), Scan (0, 1, 2), the vertical
                    // yoke's reach in line spacings (Wobbulator)
uniform vec4 uB;    // Scanimate's bend (a share of the height at the sides), FM's beta, FM's pleats, 0
out vec4 fragColor;

#define PI 3.14159265
#define GLOW 4.0   // the most the beam's slowing or a line's squeezing brightens it

float mirror(float x) {
    x = mod(abs(x), 2.0);
    return x > 1.0 ? 2.0 - x : x;
}

// The picture along line i (of n) at x (0-1): its band of rows averaged, a tap a row or so.
vec3 line(int i, float n, float x) {
    float rows = uTD2DInfos[0].res.w / n;
    int taps = clamp(int(rows + 0.5), 1, 6);
    vec3 c = vec3(0.0);
    for (int k = 0; k < taps; k++) {
        float v = 1.0 - (float(i) + (float(k) + 0.5) / float(taps)) / n;   // TouchDesigner's v runs up
        c += texture(sTD2DInputs[0], vec2(x, v)).rgb;
    }
    return c / float(taps);
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    float n = uR.x;
    float sp = res.y / n;
    float s = max(uR.y * sp * 0.5, 0.35);
    float reach = 3.0 * s;
    int mode = int(uR.z + 0.5);
    float x = vUV.s;
    float y = (1.0 - vUV.t) * res.y;                     // pixels from the top
    float bend = mode == 1 ? uB.x * res.y * (2.0 * x - 1.0) * (2.0 * x - 1.0) : 0.0;
    float spread = reach / sp + 1.0 + (mode == 0 ? uR.w : 0.0);
    float mid = (y - bend) / sp - 0.5;
    int lo = max(int(floor(mid - spread)), 0);
    int hi = min(int(ceil(mid + spread)), int(n) - 1);
    float norm = sp / (s * 2.5066283);
    vec3 acc = vec3(0.0);
    for (int i = lo; i <= hi; i++) {
        vec4 yoke = texelFetch(sTD2DInputs[1], ivec2(i, 0), 0);
        float d = y - ((float(i) + 0.5 + yoke.g) * sp + bend);
        if (abs(d) > reach)
            continue;
        float src = x, gain = 1.0;
        if (mode == 0) {
            src = mirror(x - yoke.r);
        } else if (mode == 1) {
            float k = abs(yoke.b) < 1e-3 ? 1e-3 : yoke.b;
            src = 0.5 + (x - 0.5 - yoke.r) / k;
            if (src < 0.0 || src > 1.0)
                continue;
            gain = min(1.0 / abs(k), 2.0) * (k < 0.0 ? 0.75 : 1.0);
        } else {
            float m = uB.z, beta = uB.y;
            for (int it = 0; it < 4; it++) {
                float a = 2.0 * PI * (m * src + yoke.r);
                src -= (src + beta / (2.0 * PI * m) * sin(a) - x) / (1.0 + beta * cos(a));
            }
            gain = min(1.0 / (1.0 + beta * cos(2.0 * PI * (m * src + yoke.r))), GLOW);
            src = mirror(src);
        }
        acc += line(i, n, src) * gain * norm * exp(-0.5 * d * d / (s * s));
    }
    // Past 0.9 the light eases toward 1: a bright bunch of lines blooms rather than clips.
    vec3 over = max(acc - 0.9, 0.0);
    fragColor = vec4(min(acc, 0.9) + 0.1 * (1.0 - exp(-over / 0.1)), 1.0);
}
