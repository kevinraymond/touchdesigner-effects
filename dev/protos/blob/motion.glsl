// DEV ONLY (blob round 1, variant B): motion mask = |picture - running background|, gained.
// Blurred afterwards so ripples merge into a few blobs instead of thousands of specks (the
// Blob Track TOP's cost follows the number of raw contours, not the blobs it keeps).
uniform vec4 uK;   // y gain
out vec4 fragColor;
void main() {
    float a = texture(sTD2DInputs[0], vUV.st).r, b = texture(sTD2DInputs[1], vUV.st).r;
    fragColor = TDOutputSwizzle(vec4(vec3(clamp(abs(a - b) * uK.y, 0.0, 1.0)), 1.0));
}
