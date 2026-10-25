// Pixel Sort (touchdesigner-effects, MIT). Which pixels sort, and by what: for each pixel the value the sort orders
// by (r, 0-1), whether it lies in a span (g) and whether its line is cut there (b). sort.glsl then sorts each line's
// spans. Spans follow satyarth's pixelsort intervals (MIT): Brightness between Low and High, away from Edges, or the
// whole line, with random cuts. Followed, not copied.
// Inputs: 0 the picture, 1 this pass's last frame (key_fb, from a 1 x 1 black: was each pixel in a span), 2 the
// depth or mask (input 3, else the brightness).
uniform vec4 uSpan;  // x Spans (0 Brightness, 1 Edges, 2 Depth or Mask, 3 Whole Lines), y Low, z High, w Edge
uniform vec4 uSort;  // x Sort By (0 Brightness, 1 Hue, 2 Saturation), y Cut Every (pixels at 720 high; 0 no cuts),
                     // z how much wider the spans are now (loudness, a build: -0.5 to 0.6, below 0 narrower),
                     // w hysteresis
out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

// HSV hue and saturation, 0-1, by the usual hexcone formulas.
vec2 hueSat(vec3 c) {
    float mx = max(c.r, max(c.g, c.b)), d = mx - min(c.r, min(c.g, c.b));
    float h = 0.0;
    if (d > 1e-5) {
        if (mx == c.r) h = mod((c.g - c.b) / d, 6.0);
        else if (mx == c.g) h = (c.b - c.r) / d + 2.0;
        else h = (c.r - c.g) / d + 4.0;
    }
    return vec2(h / 6.0, mx > 1e-5 ? d / mx : 0.0);
}

// Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
uint ihash(uint x) {
    x ^= x >> 16; x *= 0x7feb352du;
    x ^= x >> 15; x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 sz = ivec2(uTDOutputInfo.res.zw);
    float l[9];
    for (int j = 0; j < 9; j++)
        l[j] = luma(texelFetch(sTD2DInputs[0], clamp(p + ivec2(j % 3 - 1, j / 3 - 1), ivec2(0), sz - 1), 0).rgb);
    vec3 c = texelFetch(sTD2DInputs[0], p, 0).rgb;
    int kind = int(uSpan.x + 0.5);
    float wide = uSort.z;
    // Hysteresis: a pixel in a span last frame leaves it only once h outside the range, and one outside joins only
    // once h inside, so noise in the picture doesn't make span ends flicker from frame to frame.
    bool was = texture(sTD2DInputs[1], vUV.st).g > 0.5;   // by UV: it starts as a 1 x 1 black (start)
    bool inSpan = true;
    if (kind == 0 || kind == 2) {
        // Brightness smoothed over 3 x 3, for the same reason.
        float v = kind == 0 ? (4.0 * l[4] + 2.0 * (l[1] + l[3] + l[5] + l[7]) + l[0] + l[2] + l[6] + l[8]) / 16.0
                            : texture(sTD2DInputs[2], vUV.st).r;
        // Wider (loudness, a build) moves Low toward black and High toward white, by that share of the way; narrower
        // moves both toward their middle. Neither ever reaches the end, so the darkest and brightest stay out.
        float mid = 0.5 * (uSpan.y + uSpan.z);
        float lo = wide >= 0.0 ? mix(uSpan.y, 0.0, wide) : mix(uSpan.y, mid, -wide);
        float hi = wide >= 0.0 ? mix(uSpan.z, 1.0, wide) : mix(uSpan.z, mid, -wide);
        float m = was ? -uSort.w : uSort.w;
        inSpan = v >= lo + m && v <= hi - m;
    } else if (kind == 1) {
        // Sobel, a quarter of its sum: 1 across a black-to-white step.
        float gx = (l[2] + 2.0 * l[5] + l[8] - l[0] - 2.0 * l[3] - l[6]) / 4.0;
        float gy = (l[6] + 2.0 * l[7] + l[8] - l[0] - 2.0 * l[1] - l[2]) / 4.0;
        float edge = uSpan.w * (1.0 + wide);
        inSpan = length(vec2(gx, gy)) < edge * (was ? 1.3 : 0.7);
    }
    // Cuts are fixed to the picture's pixels, so they stay put whatever the angle and from frame to frame.
    float chance = uSort.y > 0.0 ? 720.0 / (uSort.y * float(sz.y)) * (1.0 - wide) : 0.0;
    bool cut = float(ihash(uint(p.x) ^ ihash(uint(p.y) + 0x9e3779b9u))) / 4294967296.0 < chance;
    int by = int(uSort.x + 0.5);
    float value = by == 0 ? luma(c) : (by == 1 ? hueSat(c).x : hueSat(c).y);
    fragColor = vec4(value, inSpan ? 1.0 : 0.0, cut ? 1.0 : 0.0, 1.0);
}
