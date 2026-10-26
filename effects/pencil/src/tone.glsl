// touchdesigner-effects (MIT), Pencil: the tone map, as a table of 256 levels. Lu, Xu and Jia (NPAR 2012, 3.2)
// observe that a pencil drawing's tones follow a pattern a photograph's don't: mostly white paper, a broad band of
// mild strokes, and a few dark accents. They model it as three layers (eqs. 4-7), on values 0-255:
//     bright  p1(v) = exp(-(255 - v) / sb) / sb                   a Laplacian at the paper's white, sb = 9
//     mild    p2(v) = 1 / (ub - ua) for ua <= v <= ub            uniform, ua = 105, ub = 225
//     dark    p3(v) = exp(-(v - md)^2 / (2 sd^2)) / (sqrt(2 pi) sd)    a Gaussian, md = 90, sd = 11
// weighted by w (Table 1 gives 11 : 37 : 52, which its Figures 9 and 11 show as dark : mild : bright; the figure's
// 29 : 29 : 42 draws darker and 2 : 22 : 76 lighter, and Shading moves between the three), and match the picture's
// histogram to that mix. Here each layer is normalized as a distribution over 0-255, so a weight is its layer's share
// of the pixels, as the paper estimates them.
// Each pixel of this pass is a level b: the share of the picture darker than b (histogram.glsl's capped histogram
// summed up to b, with what the cap took off spread evenly over every level), then the tone whose share of the model
// is the same, found by bisection: J = F_model^-1(F_picture(b)). The cap keeps the table from climbing more steeply
// than a few times the model's own slope anywhere. It is eased over uE.y seconds, so a bright thing walking in doesn't
// swing the whole drawing's tone at once.
// Inputs: 0 the capped histogram (histogram.glsl: r the share at each level, g what the cap took off), 1 this pass
// last frame (read by UV; a 1 once set, so the first frame takes its tones at once instead of easing up from black).
// Out: r the tone (0 dark, 1 the paper) for the level at this pixel's place along x (0-255), a 1.
uniform vec4 uW;   // x, y, z the dark, mild and bright layers' weights (summing to 1)
uniform vec4 uE;   // x the frame step (s), y how long the easing takes (s)
out vec4 fragColor;

const float SB = 9.0 / 255.0, UA = 105.0 / 255.0, UB = 225.0 / 255.0, MD = 90.0 / 255.0, SD = 11.0 / 255.0;

// erf by Abramowitz and Stegun's 7.1.26 (|error| < 1.5e-7).
float erf_(float x) {
    float s = sign(x), a = abs(x);
    float t = 1.0 / (1.0 + 0.3275911 * a);
    float y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592)
                    * t * exp(-a * a);
    return s * y;
}

float phi(float z) {
    return 0.5 * (1.0 + erf_(z * 0.70710678));
}

// The model's share of tones darker than v, each layer cut to 0-1 and normalized there.
float model(float v) {
    float e0 = exp(-1.0 / SB);
    float bright = (exp(-(1.0 - v) / SB) - e0) / (1.0 - e0);
    float mild = clamp((v - UA) / (UB - UA), 0.0, 1.0);
    float d0 = phi(-MD / SD), d1 = phi((1.0 - MD) / SD);
    float dark = (phi((v - MD) / SD) - d0) / (d1 - d0);
    return uW.x * dark + uW.y * mild + uW.z * bright;
}

void main() {
    int b = int(floor(gl_FragCoord.x));
    float below = 0.0, total = 0.0, cut = 0.0;
    for (int k = 0; k < 256; k++) {
        vec2 h = texelFetch(sTD2DInputs[0], ivec2(k, 0), 0).rg;
        below += k < b ? h.r : (k == b ? 0.5 * h.r : 0.0);
        total += h.r;
        cut += h.g;
    }
    float share = (below + cut * (float(b) + 0.5) / 256.0) / max(total + cut, 1e-6);
    share = clamp(share, 0.001, 0.999);
    float lo = 0.0, hi = 1.0;
    for (int i = 0; i < 20; i++) {
        float m = 0.5 * (lo + hi);
        if (model(m) < share) lo = m; else hi = m;
    }
    float tone = 0.5 * (lo + hi);
    vec4 last = texture(sTD2DInputs[1], vec2(vUV.s, 0.5));
    float t = last.a > 0.5 ? mix(last.r, tone, 1.0 - exp(-uE.x / uE.y)) : tone;
    fragColor = vec4(t, 0.0, 0.0, 1.0);
}
