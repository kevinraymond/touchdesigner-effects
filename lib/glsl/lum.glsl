// touchdesigner-effects (MIT), shared by Datamosh and Fluid (lib/glsl, lib_glsl()): the input's
// luma, box-averaged down by an even factor uK (2, 4 or 8): (uK / 2)^2 bilinear taps placed on
// texel corners average a uK x uK block exactly. The motion estimates (optical flow, block
// matching) and the cut test work on these.
uniform float uK;
out vec4 fragColor;
void main() {
    vec2 ipx = uTD2DInfos[0].res.xy;
    int n = max(1, int(uK) / 2);
    float acc = 0.0;
    for (int j = 0; j < n; j++)
    for (int i = 0; i < n; i++) {
        vec2 o = vec2(float(2 * i + 1 - n), float(2 * j + 1 - n));
        acc += dot(texture(sTD2DInputs[0], vUV.st + o * ipx).rgb, vec3(0.2126, 0.7152, 0.0722));
    }
    acc /= float(n * n);
    fragColor = vec4(acc, acc, acc, 1.0);
}
