// touchdesigner-effects (MIT), Lens Flare: the iris's Fourier transform, along each row first:
// F(u, y) = sum over x of a(x, y) e^(-2 pi i (u - N/2)(x - N/2) / N), the middle frequency at the middle. A 2D
// transform is one along the rows, then one along the columns (dft.glsl). Plain sums, N terms a pixel: they cook only
// when the iris changes.
// Input: 0 the iris (aperture.glsl). Out: (real, imaginary).
out vec4 fragColor;
void main() {
    ivec2 o = ivec2(gl_FragCoord.xy);
    int n = textureSize(sTD2DInputs[0], 0).x;
    int u = (o.x + n / 2) % n;   // the frequency o.x - n/2, as 0..n-1 (GLSL's % is undefined below 0)
    vec2 sum = vec2(0.0);
    for (int x = 0; x < n; x++) {
        float a = texelFetch(sTD2DInputs[0], ivec2(x, o.y), 0).r;
        // The phase's whole turns dropped in integers, so it stays exact.
        int k = (u * ((x + n / 2) % n)) % n;
        float ph = -6.2831853 * float(k) / float(n);
        sum += a * vec2(cos(ph), sin(ph));
    }
    fragColor = vec4(sum, 0.0, 1.0);
}
