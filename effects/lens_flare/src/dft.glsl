// touchdesigner-effects (MIT), Lens Flare: the iris's Fourier transform along the columns of the row transform
// (dft_rows.glsl), squared: |F(u, v)|^2, the iris's far-field diffraction pattern (Fraunhofer) at one wavelength,
// over the open area squared, so the middle is 1.
// Input: 0 the row transform. Out: the pattern's power.
out vec4 fragColor;
void main() {
    ivec2 o = ivec2(gl_FragCoord.xy);
    int n = textureSize(sTD2DInputs[0], 0).y;
    int v = (o.y + n / 2) % n;
    vec2 sum = vec2(0.0);
    for (int y = 0; y < n; y++) {
        vec2 f = texelFetch(sTD2DInputs[0], ivec2(o.x, y), 0).rg;
        int k = (v * ((y + n / 2) % n)) % n;
        float ph = -6.2831853 * float(k) / float(n);
        vec2 w = vec2(cos(ph), sin(ph));
        sum += vec2(f.x * w.x - f.y * w.y, f.x * w.y + f.y * w.x);
    }
    // The open area: the row transform's middle frequency, summed down its column.
    float area = 0.0;
    for (int y = 0; y < n; y++) area += texelFetch(sTD2DInputs[0], ivec2(n / 2, y), 0).r;
    fragColor = vec4(dot(sum, sum) / max(area * area, 1e-9), 0.0, 0.0, 1.0);
}
