// DEV ONLY. |current - previous| luma, averaged later by an Analyze TOP into a 1x1 cut measure.
out vec4 fragColor;
void main() {
    float d = abs(texture(sTD2DInputs[0], vUV.st).r - texture(sTD2DInputs[1], vUV.st).r);
    fragColor = vec4(d, d, d, 1.0);
}
