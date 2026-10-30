// Schlieren (touchdesigner-effects, MIT): the picture seen through the warm air, as a schlieren camera shows it
// (G. S. Settles, "Schlieren and Shadowgraph Techniques", Springer 2001; the four looks after C. Brownlee, V. Pegoraro,
// S. Shankar, P. McCormick and C. Hansen, "Physically-Based Interactive Flow Visualization Based on Schlieren and
// Interferometry Experimental Techniques", IEEE TVCG 17(11), 2011). The picture behind is shifted a little by the
// bending, as heat haze shifts what is behind it. What stands out in front is opaque: the camera sees the air around it.
//   Knife Edge: a blade at the focus cuts off light bent one way and lets through light bent the other, so the air
//     shows as gray relief, lit from the side the blade faces; strong bending saturates, as a real cutoff does.
//   Rainbow: a color filter in place of the blade (Rheinberg's): the way the light bends picks the hue, from the
//     spectrum (C. Wyman, P.-P. Sloan, P. Shirley's fit of the CIE color matching functions, lib spectrum.glsl), and
//     how far it bends how much of it shows.
//   Shadowgraph: no blade at all; light gathers where the bending converges and leaves where it spreads, so the air's
//     sharpest folds show as bright and dark lines.
//   Interferogram: the light through the air meets light that went round it, in fringes. The reference beam's tilt
//     lays straight fringes across the frame, and the warm air, slowing the light through it, bends them (with no tilt,
//     the fringes are the heat's own contours).
// Backdrop at 0 is a schlieren photograph: an even gray field, the subject a dark silhouette, the air's relief on it.
// Inputs: 0 the picture (sets the size), 1 the bending (bend.glsl: rg deflection, b Laplacian, a heat; half size),
// 2 what warms and what is opaque (subject.glsl: g opaque; a quarter of the size).
uniform vec4 uL;   // x Style (0 Knife Edge, 1 Rainbow, 2 Shadowgraph, 3 Interferogram), y how strongly the bending shows,
                   // z Backdrop 0-1, w how far the picture behind shifts (frame heights at a deflection of 1)
uniform vec4 uE;   // xy the way the knife edge faces (a unit vector), z reference fringes a frame height
out vec4 fragColor;

#define SHIFT_MAX 1.0      // the picture behind shifts at most as much as a deflection of this size shifts it
#define GRAY 0.45          // a schlieren photograph's field, with the blade cutting off half the light
#define RELIEF 1.2         // how far the relief takes the picture toward black or white
#define SHADOW 0.45         // how far a shadowgraph line takes the picture toward black or white (0.6 swept cells between
                           // the two often enough to flash with Flashing Off)
#define FRINGE_HEAT 4.0    // fringes the warmest air adds
#define FRINGE_WIDTH 0.12  // a fringe's half-width, as a share of the spacing
#define FRINGE_LIGHT 0.45

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

// The color of light of one wavelength, at its brightest, in the picture's encoding.
vec3 spectral(float lam) {
    vec3 rgb = max(XYZ_TO_RGB * cmf(lam), 0.0);
    return toSRGB(rgb / max(max(rgb.r, rgb.g), max(rgb.b, 1e-6)));
}

// A wheel of spectral colors, red through violet over most of it and the purples (red and violet mixed) closing it.
vec3 wheel(float a) {
    if (a < 0.8) return spectral(640.0 - 200.0 * a / 0.8);
    return mix(spectral(440.0), 0.5 * (spectral(440.0) + spectral(640.0)), smoothstep(0.8, 1.0, a))
         * (1.0 - smoothstep(0.9, 1.0, a)) + spectral(640.0) * smoothstep(0.9, 1.0, a);
}

void main() {
    vec2 uv = vUV.st;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    vec4 b = sampleCR(1, uv);
    float opaque = smoothstep(0.3, 0.7, texture(sTD2DInputs[2], uv).g);   // already spread over a cell (subject.glsl)
    vec2 bend = b.rg * (1.0 - opaque);
    // At most SHIFT_MAX: the picture shimmers rather than slides, since a bright point slid back and forth flashes.
    vec2 shift = uL.w * SHIFT_MAX * tanh(bend / SHIFT_MAX) * vec2(1.0 / aspect, 1.0);
    vec3 seen = texture(sTD2DInputs[0], uv - shift).rgb;
    vec3 base = mix(vec3(GRAY) * (1.0 - opaque), seen, uL.z);
    float gray = dot(base, vec3(0.2126, 0.7152, 0.0722));
    int style = int(uL.x + 0.5);
    vec3 c;
    if (style == 0) {
        float s = uL.y * dot(bend, uE.xy);
        c = base + RELIEF * 0.5 * tanh(2.0 * s);
    } else if (style == 1) {
        float a = fract(atan(bend.y, bend.x) / 6.2831853 - atan(uE.y, uE.x) / 6.2831853);
        float m = clamp(2.0 * uL.y * length(bend), 0.0, 1.0);
        c = base * (1.0 - 0.6 * m) + m * wheel(a) * (0.35 + 0.65 * gray);
    } else if (style == 2) {
        c = base + SHADOW * (clamp(1.0 + 0.6 * uL.y * b.b * (1.0 - opaque), 0.0, 2.0) - 1.0);
    } else {
        float phase = uE.z * uv.x * aspect + FRINGE_HEAT * b.a;
        float d = abs(phase - floor(phase + 0.5));
        float line = pow(1.0 - clamp(d / FRINGE_WIDTH, 0.0, 1.0), 2.0);
        if (uE.z <= 0.0) line *= clamp(8.0 * b.a, 0.0, 1.0);
        line *= (1.0 - opaque) * clamp(uL.y / 1.5, 0.0, 1.0);
        c = base + FRINGE_LIGHT * line * (1.2 - base);
    }
    // Every pixel through the red guard (lib red_guard.glsl): the relief, the colors and the shimmer each move a red near
    // WCAG's saturated-red line back and forth across it (red flowers: 1.5 to 3 red flashes a second against the
    // clip's 1, unguarded).
    c = toSRGB(redGuard(toLinear(clamp(c, 0.0, 1.0))));
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
