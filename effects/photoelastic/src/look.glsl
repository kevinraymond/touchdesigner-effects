// Photoelastic (touchdesigner-effects, MIT): the picture as clear plastic between polarizers. The stress (stress.glsl)
// gives each pixel a fringe order, how many waves of 550 nm one of its two polarized waves falls behind the other, and
// the angle of its first principal direction; the chart (chart.glsl) says what color white light comes out at that
// order and that angle to the polarizers, in the Style's polariscope. The light behind the plastic is the picture,
// evened toward a plain white light by Backlight, so the colors show in the picture's dark parts too; Backdrop lets
// some of the picture through as it is, as polarizers short of perfect do. The retardation grows with the plastic's
// thickness as well as its stress, and Cast makes the plastic thick where the picture warms it and thin elsewhere: an
// even sheet shows the stress wherever it reaches, which a large warm patch spreads over the whole frame as a wash of
// first-order grays. The stress itself is worked out for an even sheet.
// The orders saturate toward a cap, so the fringes stop crowding past where they read (and alias).
// Inputs: 0 the picture (sets the size), 1 the stress (stress.glsl: r a, g b; a quarter of the size), 2 the chart,
// 3 the warmth at 1/16 of the size (lib pyramid(): r), for the thickness.
uniform vec4 uL;   // x Style (0 Dark Field, 1 Light Field, 2 Plane, 3 Tint Plate), y fringe orders per unit of stress
                   // (Stress, the load), z the cap on the orders, w the order at the chart's right edge
uniform vec4 uP;   // x Backdrop 0-1, y Backlight 0-1, z the polarizers' angle (radians), w Cast 0-1
out vec4 fragColor;

#define EVEN 0.55     // the plain white light's brightness, in linear light
#define BRIGHT 1.0    // the light through the polariscope
#define PI 3.14159265

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void main() {
    vec2 uv = vUV.st;
    vec2 ab = sampleCR(1, uv).rg;
    float thick = mix(1.0, clamp(2.0 * texture(sTD2DInputs[3], uv).r, 0.0, 1.0), uP.w);
    float n = 2.0 * length(ab) * uL.y * thick;
    n = uL.z * tanh(n / uL.z);
    float th = mod(0.5 * atan(ab.y, ab.x) - uP.z, PI);
    vec2 cres = uTD2DInfos[2].res.zw;
    vec2 cuv = vec2((0.5 + n / uL.w * (cres.x - 1.0)) / cres.x, th / PI);
    vec3 t = max(texture(sTD2DInputs[2], cuv).rgb, 0.0);
    vec3 pic = toLinear(clamp(texture(sTD2DInputs[0], uv).rgb, 0.0, 1.0));
    vec3 back = mix(pic, vec3(EVEN), uP.y);
    vec3 c = BRIGHT * back * t + uP.x * pic * (int(uL.x + 0.5) == 1 ? 0.0 : 1.0);
    // Every pixel through the red guard (lib red_guard.glsl): the interference colors pass near and through WCAG's
    // saturated red as the orders change (the first order's red and the second's).
    c = toSRGB(redGuard(clamp(c, 0.0, 1.0)));
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
