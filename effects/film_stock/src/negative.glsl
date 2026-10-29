// Film Stock (touchdesigner-effects, MIT). The negative: the exposure becomes density, and the density is made of
// grains. Each layer of the emulsion (one in black and white, three in color: the cyan-forming layer sees red, the
// magenta green, the yellow blue) answers its light by its characteristic curve (Hurter and Driffield, 1890), an S in
// log exposure from the base's fog (dmin) up through the straight part at the stock's gamma to the shoulder; a
// reversal stock's runs the other way, dense where it saw little light, and steeper. Density is made of developed
// silver grains (dye clouds, in color), opaque specks: the Boolean model of stochastic geometry (Matheron 1967), as
// Newson, Delon and Galerne used it for film (CGF 2017): disks whose centers fall as a Poisson process with a density
// chosen so that a point is covered with probability u = 1 - 10^-D, with log-normal radii. The grain's size comes from
// the stock's published rms granularity by Nutting's formula (sigma_D^2 = 0.434 D a / A: a the grain's area), and
// what it covers on screen from how many micrometers of film a pixel holds (Gauge): a Super 8 frame is four times
// smaller than a 35 mm one, so its grains are four times bigger on screen.
// The model is simulated, not summarized: for each pixel and layer the number of grains in the pixel is drawn from
// its Poisson law (the shot noise of the grains, which is the grain), and the pixel's coverage follows, 1 - (1 - a)^N
// for N grains each of area a (their places inside the pixel marginalized; dev/protos/film_stock/grain_check.py checks
// it against the model rasterized). Once the grains are big enough to see (a radius over SWITCH pixels), each grain is
// drawn: its cell's count from the Poisson law, its place and radius from dice, and the pixel's coverage by it the
// area of the lens where it meets the pixel's disk, the pixel taken as a disk of the same area; the union of the
// grains is 1 - the product of what each leaves uncovered. Both give the model's mean exactly, and its standard
// deviation within about 15%. Nothing here derives the grain's statistics or scales noise by them (Northwestern's US
// 12,705,810, which claims the paper this effect was planned from, Zhang et al. 2023; see the docs page).
// The film's own softness (its resolving power) blurs the exposure first, and the halo from glare.glsl exposes the red
// layer most, the green a little, the blue least (the light comes back up from the base through the layers).
// Inputs: 0 the exposure (linear), 1 the halo (an eighth of the size, blurred). Out: each layer's transmittance
// (1 - its coverage), 16-bit float, the blue layer in b for a color stock, all three the same for black and white.
uniform vec4 uS;      // x stock index, y Halation 0-1, z unused, w the radius in pixels at which grains are drawn one
                      // by one (SWITCH)
out vec4 fragColor;
#define PIX_R 0.5641896   // a disk of a pixel's area
#define U_MAX 0.99        // coverage never above this: density 2 and up is all grain, where single grains don't show
#define U_FINE 0.9        // above this the pixel's count alone does, whatever the grains' size: the grains
                          // overlap so much there that none shows on its own

// One Poisson draw of mean mu from a seed: the inverse law up to mean 10, a rounded normal above.
float poisson(float mu, uint seed) {
    uint h = ihash(seed ^ 0x27d4eb2fu);
    vec2 e = vec2(float(h & 0xffffu), float(h >> 16)) / 65536.0;
    if (mu > 10.0)
        return max(floor(mu + sqrt(mu) * sqrt(-2.0 * log(max(e.x, 1e-6))) * cos(2.0 * PI * e.y) + 0.5), 0.0);
    float u = e.x, p = exp(-mu), s = p, k = 0.0;
    for (int i = 0; i < 40; i++) {
        if (u <= s) break;
        k += 1.0;
        p *= mu / k;
        s += p;
    }
    return k;
}
// The area of the lens where a disk of radius r at distance d meets the pixel's disk (radius PIX_R, area 1).
float lens(float d, float r) {
    float R = PIX_R;
    if (d >= r + R) return 0.0;
    if (d <= abs(r - R)) return r >= R ? 1.0 : PI * r * r;
    float x1 = clamp((d * d + r * r - R * R) / (2.0 * d * r), -1.0, 1.0);
    float x2 = clamp((d * d + R * R - r * r) / (2.0 * d * R), -1.0, 1.0);
    float k = max((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R), 0.0);
    return r * r * acos(x1) + R * R * acos(x2) - 0.5 * sqrt(k);
}
// The pixel's coverage by a layer whose grains have mean radius mr (pixels) and log-normal spread s, at exposure u.
float coverage(float u, float mr, float s, uint layer, vec2 p) {
    uint f = frameSeed();
    float ea = PI * mr * mr * exp(s * s);                    // E[pi r^2]
    uint px = uint(p.x), py = uint(p.y);
    uint hp = ihash((px * 4096u + py) * 0x9E3779B9u ^ ihash((layer + 1u) * 0x85ebca6bu ^ ihash(f)));   // this pixel's seed
    bool one_by_one = mr >= uS.w && u < U_FINE;
    if (mr > 0.8 * uS.w && mr < uS.w && u < U_FINE)         // a soft handoff: the models mixed pixel by pixel
        one_by_one = float(ihash(hp ^ 0x7f4a7c15u)) / 4294967296.0 < (mr - 0.8 * uS.w) / (0.2 * uS.w);
    if (!one_by_one) {
        // The count alone. A grain near the pixel's edge covers less of it than its area says, which the count
        // alone can't see, so from a fifth of a pixel up the grain's area counts for less (and the density for more,
        // which keeps the mean exact): a fit to the model rasterized, dev/protos/film_stock/grain_check.py.
        float k = clamp(1.0 - 0.9 * (mr - 0.2), 0.7, 1.0);
        float ae = min(ea * k * k, 0.5), lam = log(1.0 / (1.0 - u)) / ae;
        return 1.0 - pow(1.0 - ae, poisson(lam, hp));
    }
    float lam = log(1.0 / (1.0 - u)) / ea;                   // grains per square pixel
    // Each grain whose center lies within rmax + PIX_R of the pixel's center can touch it: cells of half that, so the
    // 5 x 5 block around the pixel's cell holds them all and about twice as many besides.
    float rmax = mr * exp(2.0 * s - 0.5 * s * s), reach = rmax + PIX_R, c = 0.5 * reach;
    ivec2 cell = ivec2(floor(p / c));
    float mu = lam * c * c, left = 1.0;
    uint hl = ihash((layer + 1u) * 0x85ebca6bu ^ ihash(f));  // this layer's seed this frame
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        ivec2 q = cell + ivec2(i, j);
        uint hc = ihash((uint(q.x + 65536) * 131072u + uint(q.y + 65536)) * 0x9E3779B9u ^ hl);   // the cell's seed
        int n = int(poisson(mu, hc));
        for (int g = 0; g < n; g++) {
            uint hg = ihash(hc + uint(g) * 0x9E3779B9u);     // the grain's place
            vec2 x = (vec2(q) + vec2(float(hg & 0xffffu), float(hg >> 16)) / 65536.0) * c;
            float d = distance(x, p);
            if (d >= reach) continue;
            uint hr = ihash(hg ^ 0x68E31DA4u);               // and its size
            vec2 e = vec2(float(hr & 0xffffu), float(hr >> 16)) / 65536.0;
            float z = clamp(sqrt(-2.0 * log(max(e.x, 1e-6))) * cos(2.0 * PI * e.y), -2.0, 2.0);
            float r = mr * exp(s * z - 0.5 * s * s);
            left *= 1.0 - lens(d, r);
        }
    }
    return 1.0 - left;
}

void main() {
    int st = int(uS.x + 0.5);
    vec2 res = uTD2DInfos[0].res.zw, px = 1.0 / res;
    float h = res.y, scale = um(h);
    // The exposure, through the film's own softness: a small Gaussian, its sigma from the stock's resolving power
    // (lines a millimeter) and how many micrometers a pixel holds.
    vec3 E = vec3(0.0);
    float sg = (300.0 / STOCK_LOOK[st].z) / scale;
    if (sg < 0.15) {
        E = texture(sTD2DInputs[0], vUV.st).rgb;
    } else {
        float w = 0.0;
        int K = sg < 0.7 ? 1 : 2;
        for (int j = -K; j <= K; j++)
        for (int i = -K; i <= K; i++) {
            float g = exp(-0.5 * float(i * i + j * j) / (sg * sg));
            E += g * texture(sTD2DInputs[0], vUV.st + vec2(float(i), float(j)) * px).rgb;
            w += g;
        }
        E /= w;
    }
    E = max(E, 0.0);
    // Halation: the light back off the base, into the red layer most.
    vec3 halo = texture(sTD2DInputs[1], vUV.st).rgb;
    float hal = uS.y * STOCK_LOOK[st].w;
    E += hal * dot(halo, vec3(0.3, 0.5, 0.2)) * vec3(1.0, 0.35, 0.12);
    // Each layer's density and its grain.
    vec4 curve = STOCK_CURVE[st];                            // x gamma (density per log10 exposure), y dmin, z range, w x0 (stops)
    vec4 grain = STOCK_GRAIN[st];                            // xyz the layers' grain radius (um), w the log-normal spread
    float layers = STOCK_LOOK[st].x, rev = STOCK_LOOK[st].y;
    vec3 t = vec3(1.0);
    for (int l = 0; l < 3; l++) {
        if (l > 0 && layers < 2.0) { t = vec3(t.r); break; }
        float e = layers < 2.0 ? dot(E, vec3(0.30, 0.59, 0.11)) : E[l];
        float x = log2(max(e, 1e-6) / 0.18);                 // stops from a mid gray
        float k = 4.0 * curve.x * 0.30103 / curve.z;         // the logistic's slope for that gamma
        float D = curve.y + curve.z * logistic((rev > 0.5 ? -1.0 : 1.0) * k * (x - curve.w));
        float u = min(1.0 - pow(10.0, -D), U_MAX);
        float mr = grain[l] * uF.z / scale;                  // the grain's mean radius in pixels
        float cov = mr > 0.0 ? coverage(u, mr, grain.w, uint(l), gl_FragCoord.xy) : u;
        t[l] = 1.0 - cov;
    }
    fragColor = vec4(t, 1.0);
}
