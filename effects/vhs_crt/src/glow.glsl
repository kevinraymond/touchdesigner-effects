// VHS + CRT (touchdesigner-effects, MIT). The light the glow spreads: the signal at an eighth of the
// output's size, in linear light, each pixel the mean of the 4 x 2 spots it covers, for the Blur TOP after it.
// Inputs: 0 the picture (for the size); 1 the signal (R'G'B').
out vec4 fragColor;
#define GAMMA 2.2

void main() {
    vec2 px = uTDOutputInfo.res.xy;                         // one output pixel, in UV
    vec3 acc = vec3(0.0);
    for (int i = 0; i < 4; i++)
    for (int j = 0; j < 2; j++) {
        vec2 uv = vUV.st + px * (vec2(float(i), float(j)) + 0.5 - vec2(2.0, 1.0)) / vec2(4.0, 2.0);
        acc += pow(max(texture(sTD2DInputs[1], uv).rgb, 0.0), vec3(GAMMA));
    }
    fragColor = vec4(acc / 8.0, 1.0);
}
