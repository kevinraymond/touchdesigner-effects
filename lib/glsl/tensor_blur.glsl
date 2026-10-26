// touchdesigner-effects (MIT), shared by the effects that follow the picture's edges (lib/glsl,
// structure_tensor()): one direction of the Gaussian that smooths the structure tensor (tensor.glsl), run
// across and then down. The smoothed tensor averages the gradients' outer products over a neighborhood, so
// gradients that point opposite ways (both sides of a thin line) add up instead of canceling, and noise
// averages out (Kyprianidis and Doellner, NPAR 2011, 3.2.2).
// Inputs: 0 the tensor (r E, g F, b G). Out: the same, smoothed along uB.xy.
uniform vec4 uB;   // xy: the direction in pixels (1, 0 or 0, 1), z: sigma in pixels at 720 high (scaled to the
                   // picture's height, so it smooths the same share of any picture)
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    float sigma = max(uB.z * uTD2DInfos[0].res.w / 720.0, 0.3);
    int n = int(ceil(2.5 * sigma));
    vec2 step = uB.xy * px;
    vec4 acc = vec4(0.0);
    float wsum = 0.0;
    for (int i = -n; i <= n; i++) {
        float w = exp(-0.5 * float(i * i) / (sigma * sigma));
        acc += w * texture(sTD2DInputs[0], vUV.st + float(i) * step);
        wsum += w;
    }
    fragColor = vec4((acc / wsum).rgb, 1.0);
}
