// Showreel (touchdesigner-effects, MIT). The name of the effect showing (Cycle, or one effect
// chosen), on a plate in the bottom-left corner (Labels); the Grid view names its own cells.
// Input 0: the view.
uniform vec4 uLabel;   // x the name to show (0: none, the Grid view), y Labels (0 or 1)
out vec4 fragColor;

void main() {
    vec4 src = texture(sTD2DInputs[0], vUV.st);
    int k = int(uLabel.x + 0.5);
    if (uLabel.y < 0.5 || k <= 0 || k >= N_TILES) {
        fragColor = TDOutputSwizzle(src);
        return;
    }
    vec2 res = uTDOutputInfo.res.zw;
    float s = max(1.0, floor(3.0 * res.y / 720.0 + 0.5));
    vec3 c = withName(src.rgb, k, vUV.st * res, vec2(6.0 * s), s);
    fragColor = TDOutputSwizzle(vec4(c, src.a));
}
