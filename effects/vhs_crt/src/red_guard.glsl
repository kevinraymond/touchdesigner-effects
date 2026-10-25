// VHS + CRT (touchdesigner-effects, MIT). The red guard, pasted in front of signal.glsl and screen.glsl.
// WCAG 2.3.1 counts a pixel as saturated red once red is 80% of its R + G + B in linear light, all or
// nothing, so tape noise, which changes every field, makes any red near that line flash however faint it
// is. Past RED_KNEE a red's share is eased toward RED_MAX, short of the line, by adding green and blue in
// the proportion the color has them (an orange stays orange, a little lighter). A share is linear, so no
// area of the picture can average past it either. signal.glsl guards the picture the TV decodes, screen.glsl
// each pixel it shows: the mask's red stripes over a warm color would cross the line by themselves.
#define RED_KNEE 0.73
#define RED_MAX 0.775

vec3 redGuard(vec3 lin) {
    float sum = lin.r + lin.g + lin.b, r = lin.r / max(sum, 1e-6);
    if (r > RED_KNEE) {
        float t = RED_KNEE + (RED_MAX - RED_KNEE) * (1.0 - exp(-(r - RED_KNEE) / (RED_MAX - RED_KNEE)));
        float gb = lin.g + lin.b, e = 0.01 * lin.r;
        lin.gb += (lin.r * (1.0 / t - 1.0) - gb) * (lin.gb + e) / (gb + 2.0 * e);
    }
    return lin;
}
