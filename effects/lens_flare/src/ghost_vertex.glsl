// touchdesigner-effects (MIT), Lens Flare: one ghost of one light, from its instance number (light id / ghosts, ghost
// id % ghosts), on a quad just big enough to hold it. After Lee and Eisemann (EGSR 2013): a ghost is the iris's shape at
// a fixed multiple c of the light's offset from the middle (negative: across the middle), sized rho (negative: upside
// down), cut by the front element's circle, each color channel its own, since the glass bends each wavelength its own
// amount. The ghost table (ghost_tex, from optics.py when the effect is built) holds them at the lens's own f-number;
// Aperture scales them: a ghost's size goes with the iris's opening, the front element's circle (in the iris's units)
// and the ghost's brightness the other way.
// A light wider than a point blurs each of its ghosts by its spread times |c|; a ghost blurred wider than itself becomes
// a blob that wide, its light kept. A ghost much bigger than the picture would only gray it over, so ghosts past VEIL
// (half diagonals) fade with their area. A ghost too faint to see collapses to nothing.
// The ghost table's rows: 0 i, 1 j, then three each (red, green, blue) for c, rho, the front element's circle (its
// middle as a multiple of the light's offset, in the iris's units, and its radius), brightness, reflectance (bare,
// single, multi); one each for the coatings' normalization; the lens's f-number.
#define ROW_C 2
#define ROW_RHO 5
#define ROW_CLIPC 8
#define ROW_CLIPR 11
#define ROW_BRIGHT 14
#define ROW_REFL 17
#define ROW_NORM 26
#define ROW_FNUMBER 29
#define FAINTEST 0.001
#define VEIL 0.5
uniform vec4 uRes;    // x, y the picture's size (pixels), z ghosts in the table, w lights
uniform vec4 uLens;   // x Aperture (f-number), y coating (0 bare, 1 single, 2 multi), z gain (Amount, beat, swell)
uniform vec4 uIris;   // x blades, y angle (radians), z roundness
uniform sampler2D sLights;
uniform sampler2D sGhosts;

out vec2 vP;
flat out vec3 vQx;
flat out vec3 vQy;
flat out vec3 vRho;
flat out vec3 vBlur;
flat out vec3 vLevel;
flat out vec3 vClipX;
flat out vec3 vClipY;
flat out vec3 vClipR;

float cell(int row, int g) {
    return texelFetch(sGhosts, ivec2(g, row), 0).r;
}

vec3 cells(int row, int g) {
    return vec3(cell(row, g), cell(row + 1, g), cell(row + 2, g));
}

float least(vec3 v) {
    return min(min(v.r, v.g), v.b);
}

float most(vec3 v) {
    return max(max(v.r, v.g), v.b);
}

void main() {
    int ghosts = int(uRes.z);
    int id = TDInstanceID();
    int l = id / ghosts;
    int g = id - l * ghosts;
    vec4 light = texelFetch(sLights, ivec2(l, 0), 0);
    vec3 color = texelFetch(sLights, ivec2(l, 1), 0).rgb;
    float hd = 0.5 * length(uRes.xy);
    float n0 = cell(ROW_FNUMBER, g);
    float k = n0 / max(uLens.x, n0);
    int coat = int(uLens.y + 0.5);
    vec3 c = cells(ROW_C, g);
    vec3 rho = cells(ROW_RHO, g) * k;
    vec3 size = abs(rho);
    vec3 bright = cells(ROW_BRIGHT, g) / (k * k) * cells(ROW_REFL + 3 * coat, g) * cell(ROW_NORM + coat, g);
    vec3 blur = 2.0 / hd + abs(c) * light.w;   // at least a pixel of the half-size render
    vec3 r = max(size, blur);
    vec3 level = uLens.z * light.z * color * bright * (size / r) * (size / r) / iris_area(uIris.x, uIris.z);
    level /= 1.0 + (r / VEIL) * (r / VEIL);
    vec3 qx = c * light.x;
    vec3 qy = c * light.y;
    vec3 reach = r + blur;
    vec2 lo = vec2(least(qx - reach), least(qy - reach));
    vec2 hi = vec2(most(qx + reach), most(qy + reach));
    if (most(level) < FAINTEST) {
        lo = vec2(-4.0);
        hi = vec2(-4.0);
    }
    vP = mix(lo, hi, TDPos().xy + 0.5);
    gl_Position = vec4(vP * hd / (0.5 * uRes.xy), 0.0, 1.0);
    vQx = qx;
    vQy = qy;
    vRho = sign(rho) * r;
    vBlur = blur;
    vLevel = level;
    vec3 clip = cells(ROW_CLIPC, g) / k;
    vClipX = clip * light.x;
    vClipY = clip * light.y;
    vClipR = cells(ROW_CLIPR, g) / k;
}
