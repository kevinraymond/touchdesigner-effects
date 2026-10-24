// Particles (touchdesigner-effects, MIT). The exposure histogram's rows added up: how many sampled
// pixels of the whole frame fall in each bin (gain.glsl counts them row by row).
// Inputs: 0 the histogram by row (gain.glsl).
// Out: one pixel per bin; r its count.
out vec4 fragColor;

void main() {
    int bin = int(gl_FragCoord.x);
    int rows = textureSize(sTD2DInputs[0], 0).y;
    float n = 0.0;
    for (int y = 0; y < rows; y++)
        n += texelFetch(sTD2DInputs[0], ivec2(bin, y), 0).r;
    fragColor = vec4(n, 0.0, 0.0, 1.0);
}
