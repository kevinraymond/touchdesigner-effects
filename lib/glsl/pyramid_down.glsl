// touchdesigner-effects (MIT), shared by the effects that work on the picture's octaves of detail (lib/glsl,
// pyramid(): Video Vocoder, Detail): one level of the Gaussian pyramid, after P. J. Burt and E. H. Adelson,
// "The Laplacian Pyramid as a Compact Image Code" (IEEE Trans. Communications 31(4), 1983). This pass is half the size
// of its input, and each of its pixels is the input smoothed around it by the binomial filter [1 5 10 10 5 1] / 32 in
// each direction, Burt and Adelson's generating kernel in its even-length form, since a half-size pixel's center
// falls between two of the input's. Each pair of taps is one bilinear read between them, so 3 x 3 reads.
// Inputs: 0 the level above (twice the size). Out: this level.
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    const float far = 5.0 / 3.0;   // 1 at 2.5 and 5 at 1.5 pixels read as 6 at 5/3; 10 and 10 at 0.5 as 20 at 0
    float w[3] = float[](6.0, 20.0, 6.0);
    float d[3] = float[](-far, 0.0, far);
    vec4 acc = vec4(0.0);
    for (int j = 0; j < 3; j++)
    for (int i = 0; i < 3; i++)
        acc += w[i] * w[j] * texture(sTD2DInputs[0], vUV.st + vec2(d[i], d[j]) * px);
    fragColor = acc / 1024.0;
}
