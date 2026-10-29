// touchdesigner-effects (MIT), shared by the effects that sum light over wavelengths (lib/glsl, lib_glsl()): Lens
// Flare's starburst. The CIE 1931 color matching functions by C. Wyman, P.-P. Sloan and P. Shirley's analytic fit
// ("Simple Analytic Approximations to the CIE XYZ Color Matching Functions", JCGT 2(2), 2013), a sum of piecewise
// Gaussian lobes per function, and the matrix from CIE XYZ to linear sRGB (D65).

float lobe(float lam, float mu, float s1, float s2) {
    float t = (lam - mu) / (lam < mu ? s1 : s2);
    return exp(-0.5 * t * t);
}

// x-bar, y-bar, z-bar at a wavelength (nm).
vec3 cmf(float lam) {
    return vec3(1.056 * lobe(lam, 599.8, 37.9, 31.0) + 0.362 * lobe(lam, 442.0, 16.0, 26.7)
                - 0.065 * lobe(lam, 501.1, 20.4, 26.2),
                0.821 * lobe(lam, 568.8, 46.9, 40.5) + 0.286 * lobe(lam, 530.9, 16.3, 31.1),
                1.217 * lobe(lam, 437.0, 11.8, 36.0) + 0.681 * lobe(lam, 459.0, 26.0, 13.8));
}

const mat3 XYZ_TO_RGB = mat3(3.2404542, -0.9692660, 0.0556434,
                             -1.5371385, 1.8760108, -0.2040259,
                             -0.4985314, 0.0415560, 1.0572252);
