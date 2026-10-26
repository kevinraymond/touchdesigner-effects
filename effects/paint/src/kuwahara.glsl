// touchdesigner-effects (MIT), Paint: the anisotropic Kuwahara filter of Kyprianidis, Kang and Doellner ("Image
// and Video Abstraction by Anisotropic Kuwahara Filtering", Pacific Graphics 2009) with the polynomial weights of
// Kyprianidis, Semmo, Kang and Doellner ("Anisotropic Kuwahara Filtering with Polynomial Weighting Functions", EG UK
// TPCG 2010), written from the papers.
//
// Around each pixel lies an ellipse, long along the flow and short across it where the picture has a clear
// direction, round where it has none: with the anisotropy A, its half-axes are a = r (alpha + A) / alpha along the
// flow and b = r alpha / (alpha + A) across. v = (d along the flow / a, d across / b) maps the ellipse onto the unit
// disc, which 8 overlapping sectors share. Sector 0 (pointing up the disc) weights a point by
//     k0(x, y) = max(0, (y + zeta) - eta x^2)^2,
// the others by the same turned through multiples of 45 degrees; each weight is divided by their sum and multiplied
// by a Gaussian of sigma 0.4 (exp(-3.125 |v|^2)). zeta = 2 / r makes every sector reach the center, and eta =
// (zeta + cos g) / sin^2 g with g = 3 pi / 16, the paper's choice for 8 sectors, makes neighbors overlap without a
// third joining them on a side. Each sector gives a weighted mean m_i and standard deviation s_i, and the pixel
// becomes
//     sum alpha_i m_i / sum alpha_i,   alpha_i = 1 / (1 + |s_i|^q),
// with |s_i| in 8-bit steps as in the paper: the evenest sectors win, so a region goes flat while its edges stay
// sharp, and strokes run along the edges. As the paper's Listing 1 does, the 8 weights come from two sets of 4:
// turning by a multiple of 90 degrees only swaps and negates coordinates, so v and v turned 45 degrees give them all.
//
// Passes > 1 runs it again on its own output (the flow stays the input's), which flattens the regions further.
// Inputs: 0 the picture (or the previous pass), 1 the flow (lib tensor_flow.glsl: rg direction, b anisotropy),
// 2 the brush scale per pixel (r: multiplies the radius; depth and the music set it).
uniform vec4 uK;   // x: radius in pixels at 720 high, y: q, z: alpha, w: the largest radius in pixels (a bound)
uniform vec4 uQ;   // x: samples along a radius, at most
out vec4 fragColor;

const float G = 0.58904862;   // 3 pi / 16

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    vec4 fl = texture(sTD2DInputs[1], uv);
    vec2 t = fl.rg, n = vec2(-t.y, t.x);
    float A = fl.b;
    float r = clamp(uK.x * texture(sTD2DInputs[2], uv).r * uTD2DInfos[0].res.w / 720.0, 1.0, uK.w);
    float alpha = uK.z;
    float a = r * (alpha + A) / alpha, b = r * alpha / (alpha + A);
    // Samples h pixels apart on a grid turned with the ellipse, at most uQ.x of them along a radius, each read from
    // the mipmap level that averages h x h pixels: about pi uQ.x^2 samples whatever the radius (a b = r^2), where
    // every pixel of the bounding box cost the radius squared. zeta = 2 / r reaches one pixel past the center at the
    // ellipse's narrowest; a sample h pixels away needs 2 h / r.
    float h = max(1.0, r / uQ.x), lod = log2(h);
    float zeta = 2.0 * h / r;
    float eta = (zeta + cos(G)) / (sin(G) * sin(G));

    // m: each sector's weighted sum of colors (rgb) and of weights (w). s: its weighted sum of |c|^2, which is
    // all the variance needs: summed over R, G and B, E[c^2] - E[c]^2 is E[|c|^2] - |E[c]|^2.
    vec4 m[8];
    float s[8];
    // The center weighs the same in every sector (each weight is zeta^2, so each gets 1/8 of its Gaussian's 1).
    vec3 c0 = textureLod(sTD2DInputs[0], uv, lod).rgb;
    for (int k = 0; k < 8; k++) {
        m[k] = vec4(0.125 * c0, 0.125);
        s[k] = 0.125 * dot(c0, c0);
    }
    // The rest in pairs, d and -d: turning a point half a circle turns each sector into the opposite one, so the
    // weights at -d are those at d with sector k and k + 4 swapped, and one set of weights serves both samples.
    int nb = int(floor(b / h));
    for (int j = 0; j <= nb; j++) {
        float y = float(j) * h, vy = y / b;
        int na = int(floor(a * sqrt(max(0.0, 1.0 - vy * vy)) / h));
        for (int i = (j == 0 ? 1 : -na); i <= na; i++) {
            float x = float(i) * h;
            vec2 v = vec2(x / a, vy);
            vec2 d = (x * t + y * n) * px;
            vec3 c = textureLod(sTD2DInputs[0], uv + d, lod).rgb;
            vec3 o = textureLod(sTD2DInputs[0], uv - d, lod).rgb;
            float cc = dot(c, c), oo = dot(o, o);
            float w[8];
            float sx = zeta - eta * v.x * v.x, sy = zeta - eta * v.y * v.y, z;
            z = max(0.0, v.y + sx);  w[0] = z * z;
            z = max(0.0, -v.x + sy); w[2] = z * z;
            z = max(0.0, -v.y + sx); w[4] = z * z;
            z = max(0.0, v.x + sy);  w[6] = z * z;
            vec2 u = 0.70710678 * vec2(v.x - v.y, v.x + v.y);
            sx = zeta - eta * u.x * u.x;
            sy = zeta - eta * u.y * u.y;
            z = max(0.0, u.y + sx);  w[1] = z * z;
            z = max(0.0, -u.x + sy); w[3] = z * z;
            z = max(0.0, -u.y + sx); w[5] = z * z;
            z = max(0.0, u.x + sy);  w[7] = z * z;
            float sum = 0.0;
            for (int k = 0; k < 8; k++) sum += w[k];
            float g = exp(-3.125 * dot(v, v)) / max(sum, 1e-8);
            for (int k = 0; k < 8; k++) {
                float wk = w[k] * g, wo = w[(k + 4) & 7] * g;
                m[k] += vec4(c * wk + o * wo, wk + wo);
                s[k] += cc * wk + oo * wo;
            }
        }
    }
    vec3 acc = vec3(0.0);
    float asum = 0.0;
    for (int k = 0; k < 8; k++) {
        if (m[k].w <= 0.0) continue;
        vec3 mk = m[k].rgb / m[k].w;
        // |s_i| in 8-bit steps: at most 441 (255 sqrt 3), and q at most 12: 441^12 fits a 32-bit float.
        float sd = 255.0 * sqrt(abs(s[k] / m[k].w - dot(mk, mk)));
        float ak = 1.0 / (1.0 + pow(sd, uK.y));
        acc += ak * mk;
        asum += ak;
    }
    fragColor = vec4(asum > 0.0 ? acc / asum : texture(sTD2DInputs[0], uv).rgb, 1.0);
}
