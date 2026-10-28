// touchdesigner-effects (MIT), Lens Flare: the flare (render) added to the picture in linear light, as a lens adds it,
// or over black (Show: Flare Only). Added as 1 - (1 - picture) e^-flare: a faint flare adds as it is, a strong one
// rolls off toward white instead of clipping flat.
// Inputs: 0 the picture, 1 the flare.
uniform vec4 uLook;   // x 1 to show the picture, 0 for the flare alone

out vec4 fragColor;
void main() {
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    vec3 flare = texture(sTD2DInputs[1], vUV.st).rgb;
    vec3 lin = 1.0 - (1.0 - min(srgb_to_linear(c.rgb) * uLook.x, vec3(1.0))) * exp(-flare);
    fragColor = TDOutputSwizzle(vec4(linear_to_srgb(lin), uLook.x > 0.5 ? c.a : 1.0));
}
