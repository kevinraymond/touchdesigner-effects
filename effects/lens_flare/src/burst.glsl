// touchdesigner-effects (MIT), Lens Flare: the starburst, a light's diffraction around the iris, after Hullin et al.
// (2011). The iris's far-field pattern (dft.glsl) belongs to one wavelength; at another it is the same pattern scaled
// by the wavelength, longer waves spreading wider. Summed over 24 wavelengths across the visible spectrum, each
// through the CIE 1931 color matching functions (C. Wyman, P.-P. Sloan and P. Shirley's analytic fit, "Simple
// Analytic Approximations to the CIE XYZ Color Matching Functions", JCGT 2(2), 2013) and into linear sRGB, the
// spikes come out white near the light and end in rainbows. A real light is far brighter than its clipped pixels
// show, so its faint spikes are seen: the brightness is raised to the power Tone (a quarter), and the pattern fades out
// toward the texture's edge. Cooks only when the iris changes.
// Input: 0 the pattern at 550 nm. Out: the starburst, 1 at the middle.
uniform vec4 uBurst;   // x zoom: frequency steps per pixel at 550 nm; y Tone

float lobe(float lam, float mu, float s1, float s2) {
    float t = (lam - mu) / (lam < mu ? s1 : s2);
    return exp(-0.5 * t * t);
}

vec3 cmf(float lam) {
    return vec3(1.056 * lobe(lam, 599.8, 37.9, 31.0) + 0.362 * lobe(lam, 442.0, 16.0, 26.7)
                - 0.065 * lobe(lam, 501.1, 20.4, 26.2),
                0.821 * lobe(lam, 568.8, 46.9, 40.5) + 0.286 * lobe(lam, 530.9, 16.3, 31.1),
                1.217 * lobe(lam, 437.0, 11.8, 36.0) + 0.681 * lobe(lam, 459.0, 26.0, 13.8));
}

const mat3 XYZ_TO_RGB = mat3(3.2404542, -0.9692660, 0.0556434,
                             -1.5371385, 1.8760108, -0.2040259,
                             -0.4985314, 0.0415560, 1.0572252);

out vec4 fragColor;
void main() {
    vec2 n = vec2(textureSize(sTD2DInputs[0], 0));
    vec2 o = gl_FragCoord.xy - 0.5 * uTDOutputInfo.res.zw;
    vec3 xyz = vec3(0.0);
    vec3 white = vec3(0.0);
    for (int i = 0; i < 24; i++) {
        float lam = 400.0 + (float(i) + 0.5) * 300.0 / 24.0;
        vec2 f = o * uBurst.x * 550.0 / lam;
        float p = texture(sTD2DInputs[0], (f + 0.5 * n) / n).r;
        // The pattern scales with the wavelength, so its power per step spreads over the scale squared.
        xyz += p * cmf(lam) * (550.0 * 550.0) / (lam * lam);
        white += cmf(lam);
    }
    vec3 rgb = max(XYZ_TO_RGB * (xyz / white.y), vec3(0.0));
    vec3 balance = max(XYZ_TO_RGB * (white / white.y), vec3(1e-4));
    rgb /= balance;
    float y = max(dot(rgb, vec3(0.2126, 0.7152, 0.0722)), 1e-9);
    rgb *= pow(y, uBurst.y) / y;
    float r = length(o) / (0.5 * uTDOutputInfo.res.z);
    rgb *= smoothstep(1.0, 0.6, r);
    fragColor = TDOutputSwizzle(vec4(rgb, 1.0));
}
