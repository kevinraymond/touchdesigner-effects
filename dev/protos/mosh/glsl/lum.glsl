// DEV ONLY (datamosh round 1). Luma, box-downsampled by an even factor uK: n x n bilinear taps
// placed on texel corners average a uK x uK block exactly. Written for tdlib.
uniform float uK;
out vec4 fragColor;
void main() {
    vec2 ipx = uTD2DInfos[0].res.xy;
    int n = max(1, int(uK) / 2);
    float acc = 0.0;
    for (int j = 0; j < n; j++)
    for (int i = 0; i < n; i++) {
        vec2 o = vec2(float(2 * i + 1 - n), float(2 * j + 1 - n));
        vec3 c = texture(sTD2DInputs[0], vUV.st + o * ipx).rgb;
        acc += dot(c, vec3(0.2126, 0.7152, 0.0722));
    }
    acc /= float(n * n);
    fragColor = vec4(acc, acc, acc, 1.0);
}
