// DEV ONLY (ASCII round 1): input 0 mean, input 1 maximum cell luminance (Analyze TOPs, alpha).
// Out: mean, maximum, the automatic white point.
out vec4 fragColor;
void main() {
    float avg = texelFetch(sTD2DInputs[0], ivec2(0), 0).a, mx = texelFetch(sTD2DInputs[1], ivec2(0), 0).a;
    fragColor = vec4(avg, mx, clamp(min(mx, 2.5 * avg), 0.3, 1.0), 1.0);
}
