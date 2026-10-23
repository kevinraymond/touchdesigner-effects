// DEV ONLY (ASCII round 1), variant D: add a soft glow (input 1, a blur of input 0).
uniform float uGlow;
out vec4 fragColor;
void main() {
    vec3 a = texture(sTD2DInputs[0], vUV.st).rgb, b = texture(sTD2DInputs[1], vUV.st).rgb;
    fragColor = TDOutputSwizzle(vec4(a + uGlow * b, 1.0));
}
