// Particles (touchdesigner-effects, MIT). The camera's exposure drift since Capture Background: the
// tallest bin of gain.glsl's histogram (each bin counted with half of each neighbor, so a peak split
// across two bins still wins), as a log brightness ratio.
// Inputs: 0 the histogram (gain_sum.glsl).
// Out: r log(brightness now / in the empty room) for the room, g the share of samples in its bins.
#define BINS 64
#define RANGE 2.0
out vec4 fragColor;

void main() {
    float best = -1.0, total = 0.0;
    int at = BINS / 2;
    for (int i = 0; i < BINS; i++) {
        float c = texelFetch(sTD2DInputs[0], ivec2(i, 0), 0).r;
        total += c;
        float l = i > 0 ? texelFetch(sTD2DInputs[0], ivec2(i - 1, 0), 0).r : 0.0;
        float r = i < BINS - 1 ? texelFetch(sTD2DInputs[0], ivec2(i + 1, 0), 0).r : 0.0;
        float s = c + 0.5 * (l + r);
        if (s > best) {
            best = s;
            at = i;
        }
    }
    float ratio = ((float(at) + 0.5) / float(BINS) * 2.0 - 1.0) * RANGE;
    fragColor = vec4(total > 0.0 ? ratio : 0.0, total > 0.0 ? best / total : 0.0, 0.0, 1.0);
}
