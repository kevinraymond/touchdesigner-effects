// touchdesigner-effects (MIT), Pencil: the first half of Lu, Xu and Jia's line drawing (NPAR 2012, 3.1,
// Classification). Eight line segments L_i, each 1/30 of the picture's height long at Line Length 1, run through the
// pixel at eight directions over half a turn (a line has no sign, so the paper's 45 degrees over a full turn are 22.5
// over half of one here). Each gives a response G_i = L_i * G, the gradient summed along it (eq. 2), and the pixel
// joins the direction that responds most (eq. 3: C_i = G where i wins, else 0). A pixel is classified by the
// gradients around it along a line, not its own, so noise and texture don't decide it.
// The class is written as a vector at twice its angle with G's length, (G cos 2a_i, G sin 2a_i): shape.glsl reads it
// filtered, and where two classes meet their vectors average to a shorter one between them, never a third class.
// Inputs: 0 G (edges.glsl).
// Out: rg G's class at twice its angle, length G; a 1.
uniform vec4 uC;   // x the segment's half length, a share of the picture's height, y the directions' turn (the
                   // redraw, radians), z how many samples each side of the pixel
out vec4 fragColor;

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    int n = int(uC.z);
    float step = uC.x * uTD2DInfos[0].res.w / uC.z;
    float best = -1.0, ang = 0.0;
    for (int i = 0; i < 8; i++) {
        float a = uC.y + 3.14159265 * float(i) / 8.0;
        vec2 d = vec2(cos(a), sin(a)) * px * step;
        float s = 0.0;
        for (int t = -n; t <= n; t++)
            s += texture(sTD2DInputs[0], uv + float(t) * d).r;
        if (s > best) {
            best = s;
            ang = a;
        }
    }
    float g = texture(sTD2DInputs[0], uv).r;
    fragColor = vec4(g * cos(2.0 * ang), g * sin(2.0 * ang), 0.0, 1.0);
}
