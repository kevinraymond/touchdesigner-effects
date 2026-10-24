// ASCII (touchdesigner-effects, MIT): the picture's luminance at half resolution, where the edge
// pass works; there the blurs and the Sobel filter cost about a quarter of what they would at full size.
out vec4 fragColor;
void main() {
    // At half resolution each output texel sits between four input texels; the linear filter averages them.
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    fragColor = TDOutputSwizzle(vec4(l, l, l, 1.0));
}
