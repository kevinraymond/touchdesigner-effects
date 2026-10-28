// touchdesigner-effects (MIT), Words: the words over the picture, dimmed to Backdrop (0: black).
// Inputs: 0 the picture, 1 the words (premultiplied). Out: the effect's picture.
uniform vec4 uLook;   // x Backdrop
out vec4 fragColor;
void main() {
    vec4 words = texture(sTD2DInputs[1], vUV.st);
    vec3 back = texture(sTD2DInputs[0], vUV.st).rgb * uLook.x;
    fragColor = TDOutputSwizzle(vec4(words.rgb + back * (1.0 - words.a), 1.0));
}
