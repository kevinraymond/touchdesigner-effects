// touchdesigner-effects (MIT), Paint: the first half of the flow-based difference of Gaussians (FDoG) the ink
// lines come from, as Winnemoeller, Kyprianidis and Olsen describe it ("XDoG: An eXtended Difference-of-Gaussians
// Compendium Including Advanced Image Stylization", Computers & Graphics 2012, 2.6; after Kang, Lee and Chui,
// "Coherent Line Drawing", NPAR 2007): the brightness blurred by two 1D Gaussians, sigma_e and k sigma_e (k = 1.6),
// straight across the edges (the gradient's direction, at right angles to the flow). lic.glsl then smooths both
// along the flow and paint.glsl takes their difference.
// Inputs: 0 the picture (its brightness is used), 1 the flow (lib tensor_flow.glsl: rg the direction along edges).
// Out: r the brightness blurred by sigma_e across the edge, g by k sigma_e, a 1.
uniform vec4 uE;   // x: sigma_e in pixels at 720 high, y: k
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    vec2 t = texture(sTD2DInputs[1], uv).rg;
    vec2 across = vec2(-t.y, t.x) * px;
    float se = max(uE.x * uTD2DInfos[0].res.w / 720.0, 0.3), sk = uE.y * se;
    int n = int(ceil(2.5 * sk));
    vec2 acc = vec2(0.0), wsum = vec2(0.0);
    for (int i = -n; i <= n; i++) {
        float x = float(i);
        float l = dot(texture(sTD2DInputs[0], uv + x * across).rgb, vec3(0.2126, 0.7152, 0.0722));
        vec2 w = exp(-0.5 * x * x / vec2(se * se, sk * sk));
        acc += w * l;
        wsum += w;
    }
    fragColor = vec4(acc / wsum, 0.0, 1.0);
}
