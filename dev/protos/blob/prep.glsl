// DEV ONLY (blob round 1): "highlights" = brighter than the neighborhood, so one threshold
// serves dark and bright footage. Inputs: 0 small mono, 1 the same blurred.
uniform vec4 uK;   // x how much of the local mean to subtract, y gain
out vec4 fragColor;
void main() {
    float l = texture(sTD2DInputs[0], vUV.st).r, b = texture(sTD2DInputs[1], vUV.st).r;
    fragColor = TDOutputSwizzle(vec4(vec3(clamp((l - uK.x * b) * uK.y, 0.0, 1.0)), 1.0));
}
