// touchdesigner-effects (MIT), Detail: one level of the output's Laplacian pyramid, and the levels below it added back
// (lib pyramid.glsl's expand(), after Burt and Adelson, 1983). The fast local Laplacian filter (Aubry et al., TOG 2014)
// takes each coefficient from the eight remapped copies (remap.glsl): the brightness's Gaussian pyramid gives g here,
// the two copies remapped around the values of g on either side of it give their bands (each copy's level minus its
// next level expanded), and the coefficient lies between those two as g lies between their values. The smallest level
// is the brightness's own, so the picture's overall light stays where it was. While Detail boosts, Noise Floor keeps
// the change off coefficients smaller than it, as Paris et al. keep differences under 1 to 2% from being boosted, and
// as coring keeps a sharpener off film grain (J. P. Rossi, "Digital Techniques for Reducing Television Noise", SMPTE
// Journal 87(3), 1978): the change is scaled by c^2 / (c^2 + floor^2) of the picture's own coefficient c, a gain soft
// enough that a coefficient just past the floor is boosted at most an eighth more than one far past it. With a depth map or mask on input 3,
// Depth Focus keeps the change to near things: far things take the picture's own band, level by level, which blends
// the two the way Burt and Adelson's multiresolution spline does, without a seam (1983).
// The last pass (LAST defined) runs at the picture's size and gives the picture: its brightness's change added to
// each channel, so the colors stay as they were (Paris et al. 2011, Fig. 9).
// Inputs (one more in front, the picture, in the last pass): 0 the brightness at this level, 1 at the next level,
// 2 and 3 copies 0-3 at this level and the next, 4 and 5 copies 4-7, 6 the levels below collapsed (the brightness at
// the smallest level under the smallest band), 7 nearness (lib depth_near.glsl: r 0 far to 1 near).
// Out: r the output's brightness down to this level, at this level's size; the picture in the last pass.
uniform vec4 uC;   // x Depth Focus (0 without input 3), y Noise Floor (0 while Detail with the music is 0 or less)
out vec4 fragColor;

#ifdef LAST
#define AT 1
#else
#define AT 0
#endif

void main() {
    vec2 uv = vUV.st;
    float g = texture(sTD2DInputs[AT], uv).r;
    float own = g - expand(sTD2DInputs[AT + 1], uv).r;
    vec4 a = texture(sTD2DInputs[AT + 2], uv) - expand(sTD2DInputs[AT + 3], uv);
    vec4 b = texture(sTD2DInputs[AT + 4], uv) - expand(sTD2DInputs[AT + 5], uv);
    float bands[8] = float[](a.x, a.y, a.z, a.w, b.x, b.y, b.z, b.w);
    float t = clamp(g, 0.0, 1.0) * 7.0;     // the copies' g: 0, 1/7 ... 1
    int j = min(int(t), 6);
    float band = mix(bands[j], bands[j + 1], t - float(j));
    float near = texture(sTD2DInputs[AT + 7], uv).r;
    float keep = own * own / (own * own + uC.y * uC.y + 1e-12);
    band = mix(own, band, keep * mix(1.0, near, uC.x));
    float y = band + expand(sTD2DInputs[AT + 6], uv).r;
#ifdef LAST
    vec4 c = texture(sTD2DInputs[0], uv);
    fragColor = vec4(clamp(c.rgb + (y - g), 0.0, 1.0), c.a);
#else
    fragColor = vec4(y);
#endif
}
