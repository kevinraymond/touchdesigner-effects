// Ferrofluid (touchdesigner-effects, MIT): one step of the surface's height h, by the Swift-Hohenberg equation
// (J. Swift and P. C. Hohenberg, "Hydrodynamic fluctuations at the convective instability", Phys. Rev. A 15, 1977),
// the model physicists use for patterns that rise past a threshold with a set spacing, the Rosensweig spikes among
// them. In units where the spikes' wavenumber k0 is 1:
//     dh/dt = r h - (1 + lap / k0^2)^2 h + g h^2 - h^3
// The middle term lets through only ripples of the spikes' spacing; r (drive.glsl) is how far past the threshold the
// field is; the quadratic term makes the ripples meet in hexagons, spikes up, and makes the onset abrupt, so spikes
// snap up once the field passes the threshold and linger a little as it falls back (the hexagons of a real magnetic
// fluid, measured from the flat surface on: A. Gollwitzer, I. Rehberg and R. Richter, "Via hexagons to squares in
// ferrofluids", J. Phys.: Condens. Matter 18, 2006); the cubic one stops their growth. Euler steps, the Laplacian
// the isotropic 9-point one (Y. Oono and S. Puri, Phys. Rev. A 38, 1988), applied twice from a 5 x 5 patch; cells off
// the grid read as its edge. The spikes are six cells apart: the steepest ripples the grid holds limit the step (dt
// under 2 / (1 - 5.33 / k0^2)^2: 0.13 at six cells, 0.034 at eight, too short to grow spikes within a frame or two;
// dev/protos/ferrofluid). The height is never carried along by any
// velocity: it rises and falls in place.
// Inputs: 0 the height (seed.glsl's, then each pass the last one's: r h), 1 the field (drive.glsl: r the growth rate).
// Out: r h, a 1.
uniform vec4 uF;   // x dt (model time a step), y 1 / k0^2 (cells squared), z g
out vec4 fragColor;

ivec2 top;
float H(ivec2 q) { return texelFetch(sTD2DInputs[0], clamp(q, ivec2(0), top), 0).r; }

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    top = textureSize(sTD2DInputs[0], 0) - 1;
    float v[25];
    for (int j = -2; j <= 2; j++)
        for (int i = -2; i <= 2; i++)
            v[(j + 2) * 5 + i + 2] = H(c + ivec2(i, j));
    // h + lap h / k0^2 at the cell and its 8 neighbors
    float l1[9];
    for (int b = -1; b <= 1; b++)
        for (int a = -1; a <= 1; a++) {
            int k = (b + 2) * 5 + a + 2;
            float e = v[k - 1] + v[k + 1] + v[k - 5] + v[k + 5];
            float d = v[k - 6] + v[k - 4] + v[k + 4] + v[k + 6];
            l1[(b + 1) * 3 + a + 1] = v[k] + uF.y * (4.0 * e + d - 20.0 * v[k]) / 6.0;
        }
    float e = l1[1] + l1[3] + l1[5] + l1[7];
    float d = l1[0] + l1[2] + l1[6] + l1[8];
    float l2 = l1[4] + uF.y * (4.0 * e + d - 20.0 * l1[4]) / 6.0;
    float h = v[12];
    float r = texelFetch(sTD2DInputs[1], c, 0).r;
    h += uF.x * (r * h - l2 + uF.z * h * h - h * h * h);
    fragColor = vec4(clamp(h, -4.0, 4.0), 0.0, 0.0, 1.0);
}
