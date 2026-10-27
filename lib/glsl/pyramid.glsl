// touchdesigner-effects (MIT), shared by the effects that work on the picture's octaves of detail (lib/glsl,
// pyramid(): Video Vocoder, Detail), pasted in front of the shaders that call expand().
// expand(level, uv): a pyramid level read at the next larger level's pixel, smoothly, by the cubic B-spline, which
// stands in for Burt and Adelson's EXPAND (1983). A Laplacian band is a level minus the next level expanded, and the
// bands summed back up with the same expand() give the picture back exactly, whatever expand() is. The B-spline's 4 x 4
// taps are 2 x 2 bilinear reads, after C. Sigg and M. Hadwiger, "Fast Third-Order Texture Filtering" (GPU Gems 2,
// chapter 20, 2005).
vec4 expand(sampler2D level, vec2 uv) {
    vec2 size = vec2(textureSize(level, 0));
    vec2 p = uv * size - 0.5;
    vec2 i = floor(p), f = p - i;
    vec2 w0 = (1.0 - f) * (1.0 - f) * (1.0 - f) / 6.0;
    vec2 w1 = (4.0 - 6.0 * f * f + 3.0 * f * f * f) / 6.0;
    vec2 w2 = (1.0 + 3.0 * f + 3.0 * f * f - 3.0 * f * f * f) / 6.0;
    vec2 w3 = f * f * f / 6.0;
    vec2 g0 = w0 + w1, g1 = w2 + w3;
    vec2 h0 = (i - 0.5 + w1 / g0) / size;   // between pixels i - 1 and i (their centers at index + 0.5)
    vec2 h1 = (i + 1.5 + w3 / g1) / size;   // between pixels i + 1 and i + 2
    return g0.y * (g0.x * texture(level, h0) + g1.x * texture(level, vec2(h1.x, h0.y)))
         + g1.y * (g0.x * texture(level, vec2(h0.x, h1.y)) + g1.x * texture(level, h1));
}
