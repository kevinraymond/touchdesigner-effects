// touchdesigner-effects (MIT), Video Vocoder: one band of the picture, gained, and the bands below it added back. A
// band is this pyramid level minus the next smaller level expanded (lib pyramid.glsl, after Burt and Adelson's
// Laplacian pyramid, 1983): the detail of one octave of size. A channel vocoder (Dudley, 1939) gains each band of its
// carrier by the loudness of the matching band of its modulator; here the carrier is the picture and the modulator
// the music, so this band's gain is its slider times the music's gain for its band now, up to a slider of 1. Above 1
// the music swings it no further than at 1: a slider of 3 times the music's swing took every octave at 3 with Drive 1
// to 4 flashes a second under the flash test's beat. Run from the smallest band to the largest, the last pass gives
// the picture: every gain 1, it is the picture as it was.
// Inputs: 0 this level, 1 the next smaller level, 2 the bands below collapsed (the smallest level itself under the
// smallest band), 3 nearness (lib depth_near.glsl: r 0 far to 1 near).
// Out: the picture down to this band, at this level's size.
uniform vec3 uB;   // x this band's slider, y the music's gain for it now, z Depth Focus (0 without input 3)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec4 g = texture(sTD2DInputs[0], uv);
    vec4 band = g - expand(sTD2DInputs[1], uv);
    float near = texture(sTD2DInputs[3], uv).r;
    float music = mix(1.0, uB.y, mix(1.0, near, uB.z));
    float gain = uB.x + min(uB.x, 1.0) * (music - 1.0);
    fragColor = vec4(gain * band.rgb + expand(sTD2DInputs[2], uv).rgb, g.a);
}
