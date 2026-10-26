// touchdesigner-effects (MIT), Pencil: the second half of Lu, Xu and Jia's line drawing (NPAR 2012, 3.1, Line
// Shaping): S' = sum_i L_i (x) C_i, each direction's class map spread back along its own line segment. Gradient pixels
// that line up along a direction join into one stroke, a gap in an edge closes, and a stroke runs on past where its
// edge ends, so two strokes cross at a corner the way a quick hand's do; the middle of a long line, reached from both
// sides, comes out darker than its ends. draw.glsl turns S' over into the stroke map.
// Inputs: 0 the classes (classify.glsl: rg G at twice its class's angle).
// Out: r S', the strokes' darkness (G's units), a 1.
uniform vec4 uC;   // as classify.glsl's: x the half length (share of the height), y the turn, z samples each side
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    int n = int(uC.z);
    float step = uC.x * uTD2DInfos[0].res.w / uC.z;
    float s = 0.0;
    for (int i = 0; i < 8; i++) {
        float a = uC.y + 3.14159265 * float(i) / 8.0;
        vec2 d = vec2(cos(a), sin(a)) * px * step;
        vec2 e = vec2(cos(2.0 * a), sin(2.0 * a));
        for (int t = -n; t <= n; t++) {
            vec2 c = texture(sTD2DInputs[0], uv + float(t) * d).rg;
            float g = length(c);
            // In class i when within half a class (22.5 degrees at twice the angle) of its direction.
            s += dot(c, e) >= 0.9238795 * g ? g : 0.0;
        }
    }
    fragColor = vec4(s / float(2 * n + 1), 0.0, 0.0, 1.0);
}
