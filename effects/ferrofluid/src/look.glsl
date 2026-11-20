// Ferrofluid (touchdesigner-effects, MIT): the liquid drawn over the picture. The view leans a little (Tilt), so each
// spike's tip shows above its base and hides what lies behind it: seen straight on, cones read as beads
// (dev/protos/ferrofluid). Each pixel marches down from above the tallest spike toward the flat liquid, stepping back
// along the lean, and the first point whose surface reaches the ray is what it sees (steep parallax mapping:
// T. Kaneko et al., "Detailed shape representation with parallax mapping", ICAT 2001; M. McGuire and M. McGuire,
// "Steep Parallax Mapping", I3D 2005 poster). The liquid is a glossy mirror: it reflects more the more steeply it is
// seen (Schlick's approximation of Fresnel's equations, C. Schlick, Computer Graphics Forum 13(3), 1994), and what it
// reflects is the picture itself, slid along with the surface's slope as in a curved mirror, and a soft light hung
// above it, which lines the spikes' upper flanks. A lamp's highlight (Blinn-Phong) catches every tip.
//   Black: the liquid is black, as a magnetic fluid is; where it lies flat the picture shows through it (Picture).
//   Tinted: the liquid is the picture itself, lit from the upper left, and reflects less: the picture at full
//   brightness where it lies flat, its colors on the spikes (with Picture's dimming, it read as Black at a glance).
// Every pixel goes through the red guard (lib red_guard.glsl): the spikes' darks and highlights pulse with the bass
// over red flowers, and a red near WCAG's saturated-red line would flip across it.
// Inputs: 0 the picture (mipmapped: the reflection is a little soft), 1 the surface (surface.glsl: r height).
uniform vec4 uL;   // x Style (0 Black, 1 Tinted), y Picture 0-1, z a spike's height (the picture's pixels for a height of
                   // 1), w Tilt (how far a tip leans up for its height)
out vec4 fragColor;

#define STEPS 24
#define REFINE 5          // halvings of the step where the ray meets the surface (one linear step left bands)
#define ZTOP 1.8          // above the tallest spike (the height field saturates near 1.7)
#define F0 vec2(0.06, 0.04)    // how much the liquid reflects seen straight on: Black, Tinted
#define BOX vec2(1.5, 0.4)     // the soft light's brightness in the reflection: Black, Tinted
#define BEND 0.3          // how far the reflection slides for a slope of 1 (frame heights)
#define ENV_MIP 1.5       // the reflection's softness (mip level of the picture)
#define SPEC 1.0          // the highlight's brightness
#define SHINE 60.0        // how small the highlight is
#define LIGHT vec3(-0.4, 0.5, 0.77)    // the lamp: upper left, toward the camera
#define AMB 0.3           // Tinted: the light everywhere, and the lamp's
#define DIF 0.9

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

// Level 0 always: the inputs are mipmapped (for the reflection), and texture() would pick a level from how far the
// sample point jumps between neighboring pixels, which along a spike's edge is far, and read a blurred surface.
float Z(vec2 q) { return textureLod(sTD2DInputs[1], q, 0.0).r; }

void main() {
    vec2 uv = vUV.st;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    float tall = uL.z * uTD2DInfos[0].res.y;   // a spike's height in frame heights
    // the march: at height s (in surface units) the ray is above the point lean * s below uv
    float lean = tall * uL.w;
    vec2 at = uv;
    if (lean > 0.0) {
        float prevS = ZTOP;
        for (int k = 0; k <= STEPS; k++) {
            float s = ZTOP * (1.0 - float(k) / float(STEPS));
            vec2 q = uv - vec2(0.0, lean * s);
            float d = Z(q) - s;
            if (d >= 0.0) {
                // the ray met the surface between the last step above it and this one: halve that span a few times
                float hi = k == 0 ? s : prevS, lo = s;
                for (int i = 0; i < REFINE; i++) {
                    float mid = 0.5 * (hi + lo);
                    if (Z(uv - vec2(0.0, lean * mid)) - mid >= 0.0) lo = mid; else hi = mid;
                }
                at = uv - vec2(0.0, lean * lo);
                break;
            }
            prevS = s;
            at = q;
        }
    }
    vec2 px = uTD2DInfos[1].res.xy;
    float z = Z(at);
    // the slope, in frame heights of height per frame height across
    float sx = (Z(at + vec2(px.x, 0.0)) - Z(at - vec2(px.x, 0.0))) * tall / (2.0 * px.x * aspect);
    float sy = (Z(at + vec2(0.0, px.y)) - Z(at - vec2(0.0, px.y))) * tall / (2.0 * px.y);
    vec3 n = normalize(vec3(-sx, -sy, 1.0));
    int style = int(uL.x + 0.5);
    float f0 = F0[style];
    float fres = f0 + (1.0 - f0) * pow(1.0 - n.z, 5.0);
    vec3 env = toLinear(textureLod(sTD2DInputs[0], at + n.xy * BEND * vec2(1.0 / aspect, 1.0), ENV_MIP).rgb);
    env += BOX[style] * pow(clamp(n.y * 1.4 - 0.1, 0.0, 1.0), 2.0);
    vec3 l = normalize(LIGHT);
    vec3 hv = normalize(l + vec3(0.0, 0.0, 1.0));
    float spec = SPEC * pow(clamp(dot(n, hv), 0.0, 1.0), SHINE);
    vec3 pic = toLinear(textureLod(sTD2DInputs[0], at, 0.0).rgb);
    float spike = smoothstep(0.0, 0.25, z);
    spec *= spike;   // the flat liquid's share of the lamp, in linear light, lifted every dark to gray
    vec3 base;
    if (style == 0)
        base = pic * uL.y * (1.0 - spike);
    else
        base = pic * (AMB + DIF * clamp(dot(n, l), 0.0, 1.0));
    vec3 c = base * (1.0 - fres) + env * fres + spec;
    fragColor = vec4(toSRGB(redGuard(clamp(c, 0.0, 1.0))), 1.0);
}
