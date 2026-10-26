// touchdesigner-effects (MIT), Motion Magnify: one direction of the Gaussian that spreads the displacement over its
// neighbors, run across and then down, so areas move together and a part of the picture isn't pulled apart from the
// part beside it (the optical flow's noise varies from cell to cell).
// Inputs: 0 the displacement (move.glsl: rg eased). Out: rg the same, spread along uS.xy.
uniform vec4 uS;   // xy the direction in pixels (1, 0 or 0, 1), z sigma in pixels at 720 high (scaled to the
                   // picture's height, so it spreads over the same share of any picture)
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    float sigma = max(uS.z * uTD2DInfos[0].res.w / 720.0, 0.3);
    int n = int(ceil(2.5 * sigma));
    vec2 acc = vec2(0.0);
    float wsum = 0.0;
    for (int i = -n; i <= n; i++) {
        float w = exp(-0.5 * float(i * i) / (sigma * sigma));
        acc += w * texture(sTD2DInputs[0], vUV.st + float(i) * uS.xy * px).rg;
        wsum += w;
    }
    fragColor = vec4(acc / wsum, 0.0, 1.0);
}
