// touchdesigner-effects (MIT), Pixel Art: shared by its shaders (pasted in front of each).
// The art's grid: each art pixel covers S x S of the picture's pixels (Pixel Size), so the grid is the picture's size
// divided by S, rounded up. The grid's textures are allocated G x G (G = 1280 / Pixel Size, rounded up: the free
// license's largest picture), and a bigger picture makes S bigger rather than run off the grid.
// Colors are CIE L*a*b* (D65, sRGB primaries): L 0-100, a and b about -128 to 127, distances in it roughly as the eye
// sees them, as Gerstner et al. measure every color distance.

int cell_size(ivec2 res, float pixel, float grid) {
    int g = int(grid);
    return max(int(pixel), (max(res.x, res.y) + g - 1) / g);
}

ivec2 grid_size(ivec2 res, int s) {
    return (res + s - 1) / s;
}

vec3 srgb_to_linear(vec3 c) {
    return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}

vec3 linear_to_srgb(vec3 c) {
    return mix(c * 12.92, 1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}

const vec3 WHITE = vec3(0.95047, 1.0, 1.08883);
const mat3 RGB_TO_XYZ = mat3(0.4124564, 0.2126729, 0.0193339,
                             0.3575761, 0.7151522, 0.1191920,
                             0.1804375, 0.0721750, 0.9503041);
const mat3 XYZ_TO_RGB = mat3(3.2404542, -0.9692660, 0.0556434,
                             -1.5371385, 1.8760108, -0.2040259,
                             -0.4985314, 0.0415560, 1.0572252);

vec3 linear_to_lab(vec3 lin) {
    vec3 t = RGB_TO_XYZ * lin / WHITE;
    vec3 f = mix(t * 7.787 + 16.0 / 116.0, pow(max(t, vec3(0.0)), vec3(1.0 / 3.0)), step(vec3(0.008856), t));
    return vec3(116.0 * f.y - 16.0, 500.0 * (f.x - f.y), 200.0 * (f.y - f.z));
}

vec3 rgb_to_lab(vec3 c) {
    return linear_to_lab(srgb_to_linear(clamp(c, 0.0, 1.0)));
}

vec3 lab_to_linear(vec3 lab) {
    float fy = (lab.x + 16.0) / 116.0;
    vec3 f = vec3(fy + lab.y / 500.0, fy, fy - lab.z / 200.0);
    vec3 t = mix((f - 16.0 / 116.0) / 7.787, f * f * f, step(vec3(0.206893), f));
    return clamp(XYZ_TO_RGB * (t * WHITE), 0.0, 1.0);
}

// The palette's state (palette.glsl), 64 x 4: row 0 its entries (two a color while it is still splitting: Lab, and
// how much of the picture each holds, 0 for none), row 1 its colors as the art shows them, row 2's first pixel the
// annealing (temperature, phase, seconds at this temperature, how many colors), row 3 its colors (Lab, how much of
// the picture each holds, 0 for none).
// Phase 0: not started; 1: splitting as it cools; 2: all its colors, following the picture.
const int ENTRIES = 64;
const int COLORS = 32;

// A Feedback TOP gives its 1 x 1 start before its first frame, and a grid of another size after Pixel Size changes:
// state of the wrong size counts as none.
#define PALETTE_OK(u) (textureSize(sTD2DInputs[u], 0) == ivec2(ENTRIES, 4))
#define PALETTE_STATE(u) (PALETTE_OK(u) ? texelFetch(sTD2DInputs[u], ivec2(0, 2), 0) : vec4(0.0))
#define GRID_OK(u, g) (textureSize(sTD2DInputs[u], 0) == ivec2(int(g)))
