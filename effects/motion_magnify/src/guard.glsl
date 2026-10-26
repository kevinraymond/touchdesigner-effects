// touchdesigner-effects (MIT), Motion Magnify: the fold guard. The displacement is scaled down wherever it would stretch
// the picture more than uG.x pixels per pixel anywhere near (the largest stretch around, each neighbor's counted less
// the farther it is), so the warp never folds the picture over itself and the scaling itself changes smoothly.
// Inputs: 0 the displacement made larger and its stretch (stretch.glsl: rg UV units, b pixels per pixel).
// Out: rg the displacement to move the picture by (UV units), b how much of it is kept (0-1).
uniform vec4 uG;   // x the most stretch allowed (pixels per pixel), y how far a stretch reaches, in pixels at 720 high
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    float reach = max(uG.y * uTD2DInfos[0].res.w / 720.0, 0.5);
    int n = int(ceil(2.0 * reach));
    float g = 0.0;
    for (int j = -n; j <= n; j++)
    for (int i = -n; i <= n; i++) {
        float w = exp(-0.5 * float(i * i + j * j) / (reach * reach));
        g = max(g, w * texture(sTD2DInputs[0], uv + vec2(float(i), float(j)) * px).b);
    }
    float keep = min(1.0, uG.x / max(g, 1e-6));
    fragColor = vec4(texture(sTD2DInputs[0], uv).rg * keep, keep, 1.0);
}
