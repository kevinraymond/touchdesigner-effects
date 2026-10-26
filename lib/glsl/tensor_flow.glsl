// touchdesigner-effects (MIT), shared by the effects that follow the picture's edges (lib/glsl,
// structure_tensor()): the smoothed structure tensor's eigenanalysis, per pixel, as Kyprianidis, Kang and
// Doellner use it ("Image and Video Abstraction by Anisotropic Kuwahara Filtering", Pacific Graphics 2009;
// NPAR 2011, 3.2.2). Its eigenvalues are
//     lambda1,2 = (E + G +- sqrt((E - G)^2 + 4 F^2)) / 2,
// the major eigenvector points across the edges (the direction of most change), and the minor one along them,
// at the angle phi = atan(2F, E - G) / 2 + pi/2: the flow, which strokes follow. The anisotropy
//     A = (lambda1 - lambda2) / (lambda1 + lambda2)
// is 0 where nothing has a direction (flat or noisy) and 1 along a clean edge (Yang et al. 1996).
// The flow has no sign (a line has two ends): anything that walks along it keeps its own heading.
// Inputs: 0 the smoothed tensor (r E, g F, b G).
// Out: rg the flow, a unit vector in pixels (x right, y up); b the anisotropy A, 0-1; a lambda1, how strong
// the strongest change is (squared gradient, the picture's values 0-1).
out vec4 fragColor;

void main() {
    vec3 t = texture(sTD2DInputs[0], vUV.st).rgb;
    float E = t.r, F = t.g, G = t.b;
    float root = sqrt((E - G) * (E - G) + 4.0 * F * F);
    float l1 = 0.5 * (E + G + root), l2 = 0.5 * (E + G - root);
    // Below this the picture is flat to 8 bits: no direction to speak of, and atan(0, 0) is undefined.
    if (l1 + l2 < 1e-9) {
        fragColor = vec4(0.0, 1.0, 0.0, 0.0);
        return;
    }
    float phi = 0.5 * atan(2.0 * F, E - G) + 1.5707963;
    fragColor = vec4(cos(phi), sin(phi), (l1 - l2) / (l1 + l2), l1);
}
