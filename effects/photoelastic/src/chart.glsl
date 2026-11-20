// Photoelastic (touchdesigner-effects, MIT): what the polariscope lets through, as a chart the look reads: across, the
// stress's fringe order N (its retardation in waves of 550 nm, 0 at the left texel's center to uC.y at the right's);
// down, the angle from the polarizer to the stress's first principal direction (0 to 180 degrees). Stressed plastic is
// birefringent (D. Brewster, 1816): light polarized along one principal direction travels slower than along the other,
// by a retardation in proportion to their difference (Maxwell's stress-optic law, 1853). Between polarizers the two
// waves interfere, and white light comes out in Michel-Levy's interference colors (1888), as B. E. Sorensen computes
// them from first principles ("A revised Michel-Levy interference colour chart based on first-principles
// calculations", Eur. J. Mineral. 25, 2013): each wavelength's transmission summed through the CIE 1931 color
// matching functions (C. Wyman, P.-P. Sloan and P. Shirley's fit, lib spectrum.glsl), under equal-energy white, each
// channel scaled so white light through clear glass is white.
//   Dark Field: a circular polariscope, crossed: sin^2(pi N 550 / lambda). Black where unstressed.
//   Light Field: the same, parallel: 1 - that. The light passes where unstressed.
//   Plane: crossed linear polarizers: sin^2(2 angle) times the dark field, so where a principal direction lies along a
//     polarizer the plastic is dark whatever its stress (the isoclinics).
//   Tint Plate: crossed linear polarizers with a full-wave plate (a retardation of 550 nm) at 45 degrees after the
//     plastic, the sensitive tint: unstressed plastic shows the plate's magenta, and stress turns it blue where its
//     slow direction lies along the plate's and yellow across it. Worked out by Jones calculus.
uniform vec4 uC;   // x Style (0 Dark Field, 1 Light Field, 2 Plane, 3 Tint Plate), y the order at the chart's right
                   // edge, z the tint plate's retardation in orders
out vec4 fragColor;

#define SAMPLES 48
#define PI 3.14159265

vec2 cmul(vec2 a, vec2 b) { return vec2(a.x * b.x - a.y * b.y, a.x * b.y + a.y * b.x); }
vec2 cexp(float t) { return vec2(cos(t), sin(t)); }

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    float N = (gl_FragCoord.x - 0.5) / (res.x - 1.0) * uC.y;
    float th = (gl_FragCoord.y - 0.5) / res.y * PI;
    float c = cos(th), s = sin(th);
    int style = int(uC.x + 0.5);
    vec3 acc = vec3(0.0), white = vec3(0.0);
    for (int i = 0; i < SAMPLES; i++) {
        float lam = 380.0 + 400.0 * (float(i) + 0.5) / float(SAMPLES);
        vec3 rgb = XYZ_TO_RGB * cmf(lam);
        float phi = 2.0 * PI * N * 550.0 / lam;
        float dark = pow(sin(0.5 * phi), 2.0);
        float t;
        if (style == 0) t = dark;
        else if (style == 1) t = 1.0 - dark;
        else if (style == 2) t = pow(sin(2.0 * th), 2.0) * dark;
        else {
            // Polarized along x, through the plastic (its fast direction at th, retardance phi), then the plate at 45
            // degrees (retardance p), then the analyzer along y.
            vec2 e = cexp(phi);
            vec2 ex = vec2(c * c, 0.0) + s * s * e;
            vec2 ey = c * s * (vec2(1.0, 0.0) - e);
            vec2 p = cexp(2.0 * PI * uC.z * 550.0 / lam);
            vec2 fy = 0.5 * (cmul(vec2(1.0, 0.0) - p, ex) + cmul(vec2(1.0, 0.0) + p, ey));
            t = dot(fy, fy);
        }
        acc += t * rgb;
        white += rgb;
    }
    fragColor = vec4(acc / white, 1.0);
}
