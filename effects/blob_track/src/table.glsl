// Blob Track (touchdesigner-effects, MIT). The boxes to draw: the slots that are showing (not those
// still waiting to show), packed to the front, each with its four nearest neighbors among them for
// the links (worked out once here, not in every pixel).
// Inputs: 0 track.glsl; 1 the picture (for its shape).
// Out, column i: row 0 center u, v, width, height (0-1); row 1 ID shown, nearest, 2nd nearest (columns,
// -1 for none), count; row 2 fade 0-1, age (s), 3rd and 4th nearest.
out vec4 fragColor;
#define N 64
#define SHOWN 0.005

vec4 S(int s, int r) { return texelFetch(sTD2DInputs[0], ivec2(s, r), 0); }

void main() {
    int i = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    vec2 res = uTD2DInfos[1].res.zw;
    int me = -1, n = 0;
    for (int s = 0; s < N; s++) {
        if (S(s, 1).y < SHOWN) continue;
        if (n == i) me = s;
        n++;
    }
    if (me < 0) {
        fragColor = row == 0 ? vec4(-1.0, -1.0, 0.0, 0.0)
                  : row == 1 ? vec4(-1.0, -1.0, -1.0, float(n)) : vec4(0.0, 0.0, -1.0, -1.0);
        return;
    }
    vec4 b = S(me, 0), m = S(me, 1), shown = S(me, 2);
    if (row == 0) {
        fragColor = b;
        return;
    }
    vec2 c = b.xy * res;
    float d0 = 1e9, d1 = 1e9, d2 = 1e9, d3 = 1e9;
    int j0 = -1, j1 = -1, j2 = -1, j3 = -1, k = 0;
    for (int s = 0; s < N; s++) {
        if (S(s, 1).y < SHOWN) continue;
        if (s != me) {
            float d = distance(c, S(s, 0).xy * res);
            if (d < d0) { d3 = d2; j3 = j2; d2 = d1; j2 = j1; d1 = d0; j1 = j0; d0 = d; j0 = k; }
            else if (d < d1) { d3 = d2; j3 = j2; d2 = d1; j2 = j1; d1 = d; j1 = k; }
            else if (d < d2) { d3 = d2; j3 = j2; d2 = d; j2 = k; }
            else if (d < d3) { d3 = d; j3 = k; }
        }
        k++;
    }
    fragColor = row == 1 ? vec4(shown.x, float(j0), float(j1), float(n)) : vec4(m.y, m.z, float(j2), float(j3));
}
