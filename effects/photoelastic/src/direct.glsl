// Photoelastic (touchdesigner-effects, MIT): the plastic's thermoelastic potential psi at the coarsest level of the
// warmth's pyramid, worked out directly: psi is the warmth spread by the Laplacian's Green's function (an infinite
// plate, so nothing happens at the frame's edges), each cell of the level adding its warmth times G at its distance.
// On the square lattice of the 5-point Laplacian, G(r) = (ln r + gamma + 1.5 ln 2) / (2 pi) away from the cell itself
// and 0 on it: the potential kernel of the plane's simple random walk, a / 4, in its large-r form (F. Spitzer,
// "Principles of Random Walk", 1964), within a few percent from r = 1, where G is exactly 1/4.
// Outside the frame the plastic is as warm as the frame's mean, so the warmth less its mean is what is summed (an even
// warmth stresses nothing).
// Inputs: 0 the warmth at this level (lib pyramid(): r; sets the size), 1 the warmth's mean (one pixel: r).
// Out: r psi, in the finest level's pixels squared.
uniform vec4 uS;   // x the warmth's scale at this level (4^k: its Laplacian is in this level's pixels)
out vec4 fragColor;

#define G0 1.6168821   // Euler's gamma + 1.5 ln 2
#define TWO_PI 6.2831853

void main() {
    ivec2 res = ivec2(uTD2DInfos[0].res.zw);
    ivec2 p = ivec2(gl_FragCoord.xy);
    float mean = texelFetch(sTD2DInputs[1], ivec2(0), 0).r;
    float psi = 0.0;
    for (int y = 0; y < res.y; y++)
        for (int x = 0; x < res.x; x++) {
            ivec2 d = ivec2(x, y) - p;
            if (d == ivec2(0)) continue;
            float g = (0.5 * log(float(d.x * d.x + d.y * d.y)) + G0) / TWO_PI;
            psi += g * (texelFetch(sTD2DInputs[0], ivec2(x, y), 0).r - mean);
        }
    fragColor = vec4(uS.x * psi, 0.0, 0.0, 1.0);
}
