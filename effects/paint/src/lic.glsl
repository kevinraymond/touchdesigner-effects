// touchdesigner-effects (MIT), Paint: the second half of the flow-based difference of Gaussians (XDoG, 2.6, after
// Kang, Lee and Chui 2007): dog.glsl's two blurs smoothed along the flow by a Gaussian of sigma_m, a line integral
// convolution (Cabral and Leedom, "Imaging Vector Fields Using Line Integral Convolution", SIGGRAPH 1993). It walks
// a pixel at a time each way along the flow from the pixel, turning with it, so a line that bends is smoothed along
// its bend and broken bits of an edge join up. The flow has no sign, so each step keeps the heading of the last.
// Inputs: 0 dog.glsl's blurs (rg), 1 the flow (rg the direction along edges).
// Out: rg the two blurs, smoothed along the flow; a 1.
uniform vec4 uM;   // x: sigma_m in pixels at 720 high
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    float sm = max(uM.x * uTD2DInfos[0].res.w / 720.0, 0.3);
    int n = int(ceil(2.0 * sm));
    vec2 acc = texture(sTD2DInputs[0], uv).rg;
    float wsum = 1.0;
    for (int dir = -1; dir <= 1; dir += 2) {
        vec2 p = uv;
        vec2 v = float(dir) * texture(sTD2DInputs[1], uv).rg;
        for (int i = 1; i <= n; i++) {
            p += v * px;
            vec2 tn = texture(sTD2DInputs[1], p).rg;
            v = dot(tn, v) < 0.0 ? -tn : tn;
            float w = exp(-0.5 * float(i * i) / (sm * sm));
            acc += w * texture(sTD2DInputs[0], p).rg;
            wsum += w;
        }
    }
    fragColor = vec4(acc / wsum, 0.0, 1.0);
}
