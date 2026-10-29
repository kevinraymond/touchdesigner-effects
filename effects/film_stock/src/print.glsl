// Film Stock (touchdesigner-effects, MIT). The print, or the reversal film itself, seen on screen. The scanner (or the
// printer's optics) reads the negative a little soft, a Gaussian under a pixel, which the grain's specks need to read
// as grain rather than as single pixels, and its color softer still (a scanner's and a print's color resolution is
// below their brightness resolution, so film's grain is mostly a brightness grain with color only in its larger
// clumps); then each layer's actual density, from the transmittance its grains left. A negative is printed: the print stock's own curve, a steep S (its gamma about 2.8 against the
// negative's 0.6, so the system comes out at about 1.7, as cinema prints do), turns the negative's density back into
// light, dense negative to bright screen. A reversal stock is itself the positive, and the screen's light is simply
// what gets through it. Either way the dyes aren't pure (cyan absorbs some green and blue, magenta some blue), so each
// channel's density mixes a little of the others', which tames the colors as film does; then the stock's character,
// a tint in the shadows and another in the highlights, and its saturation, applied to the log of the light; and
// Contrast and Saturation from the page.
// Inputs: 0 the negative (each layer's transmittance). Out: the screen's light, linear, 16-bit float.
uniform vec4 uP;      // x stock index, y Contrast, z Saturation, w scanner sigma (pixels; its color twice that)
out vec4 fragColor;
#define PRINT_GAMMA 2.8
#define PRINT_RANGE 3.4
#define PRINT_DMIN 0.05

float printed(float D, vec4 curve) {
    // The negative's density at a mid gray, and the print's logistic placed so a mid gray prints at 0.18.
    float dmid = curve.y + curve.z * logistic(-4.0 * curve.x * 0.30103 / curve.z * curve.w);
    float kp = 4.0 * PRINT_GAMMA / PRINT_RANGE;
    float z0 = log(0.219 / 0.781);
    float Dp = PRINT_RANGE * logistic(-kp * (D - dmid) + z0);
    return pow(10.0, -Dp);                                   // 1 where the print is clear
}

void main() {
    int st = int(uP.x + 0.5);
    vec2 px = 1.0 / uTD2DInfos[0].res.zw;
    float sg = uP.w;
    vec3 t = vec3(0.0), tc = vec3(0.0);
    float w = 0.0, wc = 0.0, sc = 2.0 * sg;
    for (int j = -3; j <= 3; j++)
    for (int i = -3; i <= 3; i++) {
        float g = exp(-0.5 * float(i * i + j * j) / (sg * sg)), gc = exp(-0.5 * float(i * i + j * j) / (sc * sc));
        vec3 s = texture(sTD2DInputs[0], vUV.st + vec2(float(i), float(j)) * px).rgb;
        t += g * s; w += g;
        tc += gc * s; wc += gc;
    }
    t = clamp(t / w, 1e-4, 1.0);
    tc = clamp(tc / wc, 1e-4, 1.0);
    vec3 D = -log(t) / LN10, Dc = -log(tc) / LN10;          // each layer's density, fine and soft
    vec4 curve = STOCK_CURVE[st];
    float rev = STOCK_LOOK[st].y, layers = STOCK_LOOK[st].x;
    vec3 L, Lc;
    if (rev > 0.5) {
        L = pow(vec3(10.0), -(D - curve.y));                 // clear base: 1
        Lc = pow(vec3(10.0), -(Dc - curve.y));
    } else {
        L = vec3(printed(D.r, curve), printed(D.g, curve), printed(D.b, curve));
        Lc = vec3(printed(Dc.r, curve), printed(Dc.g, curve), printed(Dc.b, curve));
    }
    if (layers > 2.0) {                                      // the color from the soft read, the brightness from the fine
        float y = dot(L, vec3(0.2126, 0.7152, 0.0722)), yc = dot(Lc, vec3(0.2126, 0.7152, 0.0722));
        L = Lc * (y / max(yc, 1e-5));
    }
    // The dyes' unwanted absorptions, mixing each channel's density with the others'.
    if (layers > 2.0) {
        float p = STOCK_DYES[st].x;
        vec3 Ds = -log(max(L, 1e-5)) / LN10;
        mat3 M = mat3(1.0, 0.12 * p, 0.05 * p,   0.07 * p, 1.0, 0.2 * p,   0.02 * p, 0.08 * p, 1.0);   // columns: cyan, magenta, yellow
        Ds = M * Ds;
        L = pow(vec3(10.0), -Ds);
    }
    // The stock's character and the page's Contrast and Saturation, in log light around a mid gray.
    vec3 lg = log(max(L, 1e-5) / 0.18) / LN10;
    float g = dot(lg, vec3(1.0 / 3.0));
    float sat = uP.z * STOCK_DYES[st].y;
    lg = g + (lg - g) * (layers > 2.0 ? sat : 0.0);
    float wh = smoothstep(-1.2, 0.8, g);                      // 0 in the shadows, 1 in the highlights
    lg += mix(STOCK_SHADOW[st].rgb, STOCK_HIGH[st].rgb, wh);
    lg *= uP.y;
    L = 0.18 * pow(vec3(10.0), lg);
    fragColor = vec4(L, 1.0);
}
