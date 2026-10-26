// Reaction-Diffusion (touchdesigner-effects, MIT): the pattern drawn at the picture's size. V is the ink. Lines draws
// the picture by the width of its lines: ink where V stands above 1 - the ink the picture asks for, so a dark area
// takes broad lines and a bright one thin ones, as an engraving does. Dots and Coral draw ink wherever V is, their
// kill rates already following the picture (seed.glsl). V comes up from the grid by a Catmull-Rom bicubic and
// its edge is smoothed over one output pixel (fwidth), so the lines stay crisp and smooth at any Size.
// Colors: Ink on Paper, Over the Picture (the ink over the picture itself), Light on Dark (light lines on black,
// following the picture's brightness: where.glsl flips the ink), Orange and Blue.
// The music ripples it: each beat's ring runs out from a point that turns round the middle (uR.x picture heights
// out) and reaches the farthest corner as uB.x reaches 1, a drop's from the middle, uR.y times as broad and uR.z
// times as deep. Across a ring's band the pattern is read from a little farther out, then a little farther in (one
// wave of a sine, Beat Kick cells at its deepest), so the stripes it passes slide out and back like a shock wave
// through glass. It moves the drawing, not the pattern, which keeps its order, and it keeps each area's share of ink,
// so it adds no flash.
// The pattern grows in from scattered seeds over a second or two after it starts (on load and Reset). Meanwhile the
// drawing shows the ink the picture asks for as an even tone, so the picture shows at once, and from uF.x seconds it
// crossfades into the pattern, grown in by then, over as long again. As the growth sweeps a place, spots appear and
// split, which swings it between light and dark: drawn as it grew, on blank paper or over the even tone, the growth
// counted as 1.5 to 2.5 flashes in its worst second on a still picture (dev/flash.py), from none.
// Inputs: 0 the picture, 1 the state (g V), 2 where (r where it may grow, g the ink asked for), 3 the seconds since
// the pattern started (b).
// Out: the picture.
uniform vec4 uL;   // x Pattern (0 Lines, 1 Dots, 2 Coral), y Colors (0-3), z V's low, w V's high (per Pattern)
uniform vec4 uB;   // a beat's ring: x how far across, 0 (none) to 1, y the angle its start lies at (radians),
                   // z how deep it ripples (grid cells), w its width (picture heights)
uniform vec4 uF;   // x when the crossfade from the even tone into the pattern starts (s after the start)
uniform vec4 uR;   // x how far out from the middle a beat's ring starts (picture heights), y and z how much broader
                   // and deeper a drop's is, w a drop's ring: how far across, 0 (none) to 1
out vec4 fragColor;

const vec3 PAPER = vec3(0.95, 0.93, 0.88), INK = vec3(0.06, 0.06, 0.08);
const vec3 ORANGE = vec3(0.98, 0.6, 0.18), BLUE = vec3(0.08, 0.2, 0.42);

// How far a ring from 'from' (picture heights from the middle) moves the reading here, at q, along the ring's radius,
// when it has gone 'progress' of the way to the farthest corner: one wave of a sine across its width, out then in.
vec2 ripple(vec2 q, vec2 from, float progress, float width, float aspect) {
    if (progress <= 0.0) return vec2(0.0);
    vec2 corner = vec2(0.5 * aspect, 0.5) + abs(from);
    vec2 d = q - from;
    float x = (length(d) - progress * length(corner)) / width;   // -0.5 to 0.5 across the band
    if (abs(x) >= 0.5) return vec2(0.0);
    return normalize(d + 1e-6) * sin(6.2831853 * x) * (0.5 + 0.5 * cos(6.2831853 * x));
}

void main() {
    vec2 uv = vUV.st;
    vec3 pic = texture(sTD2DInputs[0], uv).rgb;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    vec2 q = vec2((uv.x - 0.5) * aspect, uv.y - 0.5);
    vec2 push = uB.z * ripple(q, uR.x * vec2(cos(uB.y), sin(uB.y)), uB.x, uB.w, aspect)
              + uB.z * uR.z * ripple(q, vec2(0.0), uR.w, uB.w * uR.y, aspect);
    float v = clamp((sampleCR(1, uv + push * uTD2DInfos[1].res.xy).g - uL.z) / (uL.w - uL.z), 0.0, 1.0);
    // Kept inside 0-1, so where there is no pattern (V 0) there is no ink, even where all ink is asked for.
    vec2 w = texture(sTD2DInputs[2], uv).rg;
    float bar = uL.x < 0.5 ? clamp(1.0 - w.g, 0.03, 0.97) : 0.5;
    float e = max(fwidth(v), 1e-4);
    float ink = smoothstep(bar - e, bar + e, v);
    ink = mix(w.g * w.r, ink, smoothstep(uF.x, 2.0 * uF.x, texture(sTD2DInputs[3], vec2(0.5)).b));
    vec3 c;
    if (uL.y < 0.5) c = mix(PAPER, INK, ink);
    else if (uL.y < 1.5) c = mix(pic, INK, ink);
    else if (uL.y < 2.5) c = mix(vec3(0.0), vec3(1.0), ink);
    else c = mix(ORANGE, BLUE, ink);
    fragColor = vec4(c, 1.0);
}
