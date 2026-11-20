// Photoelastic (touchdesigner-effects, MIT): the plastic's thermoelastic potential psi at one level of the warmth's
// pyramid. A plate warmed by T swells there, and its displacement is the gradient of a potential psi with
// lap psi = T (J. N. Goodier, "On the integration of the thermo-elastic equations", Phil. Mag. 23, 1937), up to the
// material's constants, which the effect's Stress folds in. psi is solved afresh every frame by cascadic multigrid
// (F. A. Bornemann and P. Deuflhard, "The cascadic multigrid method for elliptic problems", Numer. Math. 75, 1996):
// the coarsest level summed directly (direct.glsl), each finer level starting from the coarser one's solution
// (Catmull-Rom) and smoothed by a few Jacobi passes. The edges hold, so the plate runs on past the frame rather than being clamped
// at it (clamped edges drew fringes along the frame). The plate is free, and a free plate warmed evenly only grows, so
// the warmth's mean stresses nothing and is taken away: with the edges held, a warmth whose mean isn't 0 has no
// solution, and the passes drifted into a bowl that stressed the whole picture evenly.
// Passes: pass 0 starts from the coarser level, each later pass is one Jacobi step reading the last pass as input 0.
// Inputs: 0 the last pass (on pass 0, the warmth at this level, for the size), 1 the coarser level's psi, 2 the warmth at this level (lib pyramid(): r), 3 the warmth's mean (one pixel: r).
// Out: r psi, in the finest level's pixels squared.
uniform vec4 uS;   // x the warmth's scale at this level (4^k: its Laplacian is in this level's pixels)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    if (uTDPass == 0) {
        fragColor = vec4(sampleCR(1, uv).r, 0.0, 0.0, 1.0);
        return;
    }
    vec2 o = uTD2DInfos[0].res.xy;
    float n = texture(sTD2DInputs[0], uv + vec2(o.x, 0.0)).r + texture(sTD2DInputs[0], uv - vec2(o.x, 0.0)).r
            + texture(sTD2DInputs[0], uv + vec2(0.0, o.y)).r + texture(sTD2DInputs[0], uv - vec2(0.0, o.y)).r;
    fragColor = vec4(0.25 * (n - uS.x * (texture(sTD2DInputs[2], uv).r - texelFetch(sTD2DInputs[3], ivec2(0), 0).r)), 0.0, 0.0, 1.0);
}
