// touchdesigner-effects (MIT), Lens Flare: the iris as the starburst sees it, N x N: open (1) inside Blades, Roundness
// and Blade Angle, its corners N / 4 from the middle, with specks of dust on the glass in front of it (Hullin et al.
// 2011 add dust and scratches to the aperture for the starburst's fine streaks). Cooks only when the iris changes.
uniform vec4 uIris;   // x blades, y angle (radians), z roundness, w how much dust (0-1)

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

out vec4 fragColor;
void main() {
    float r = 0.25 * uTDOutputInfo.res.z;
    float d = iris((gl_FragCoord.xy - 0.5 * uTDOutputInfo.res.zw) / r, uIris.x, uIris.y, uIris.z);
    float open = clamp(0.5 - d * r, 0.0, 1.0);
    // Dust: dark specks 1-3 pixels across in some of an 8 x 8 grid's cells (8% of them at Dust 1).
    vec2 cell = floor(gl_FragCoord.xy / 8.0);
    vec2 at = (cell + vec2(hash(cell), hash(cell + 17.0))) * 8.0;
    float size = 1.0 + 2.0 * hash(cell + 31.0);
    float speck = step(hash(cell + 7.0), 0.08 * uIris.w) * step(distance(gl_FragCoord.xy, at), size);
    fragColor = TDOutputSwizzle(vec4(open * (1.0 - 0.8 * speck), 0.0, 0.0, 1.0));
}
