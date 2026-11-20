// Ferrofluid (touchdesigner-effects, MIT): the liquid's surface at the picture's size, each spike a cone. The height
// is read between the grid's cells by Catmull-Rom (lib common.glsl); near a peak it falls off as the square of the
// distance from the peak, so sqrt(1 - h / peak) goes as the distance itself, and 1 minus it is a cone whose tip is
// the peak. Raised to SHARP its flanks curve in, a sharp tip on a flared base, as the spikes of a magnetic fluid stand.
// Where the height lies below 0 there is no spike, only the flat liquid.
// Inputs: 0 the picture (only its size), 1 the height and its peaks (shape.glsl: r h, g peak).
// Out: r the surface's height, in units of the height field (a spike about 1 to 1.7), a 1.
out vec4 fragColor;

#define SHARP 2.0

void main() {
    vec2 uv = vUV.st;
    float h = sampleCR(1, uv).r;
    float peak = texture(sTD2DInputs[1], uv).g;
    float frac = clamp(h / max(peak, 1e-3), 0.0, 1.0);
    float z = max(peak, 0.0) * pow(1.0 - sqrt(1.0 - frac), SHARP);
    fragColor = vec4(z, 0.0, 0.0, 1.0);
}
