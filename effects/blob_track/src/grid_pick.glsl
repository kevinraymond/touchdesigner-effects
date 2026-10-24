// Blob Track (touchdesigner-effects, MIT). GPU Grid detector, step 3 of 3: the peaks as a list,
// strongest first, at most as many as track.glsl has slots: the same table bt_pick.glsl writes for
// the Blob Track TOP.
// A peak's ID is its cell's number (match.glsl lets a box follow it into the next cell).
// Input 0: grid_peaks.glsl.
// Out, column i = the i-th strongest: row 0 center u, v, width, height (0-1); row 1 ID, 0, 0, count.
uniform vec4 uPick;   // z most peaks to pass on
out vec4 fragColor;
#define MAXP 128

void main() {
    int col = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    ivec2 G = textureSize(sTD2DInputs[0], 0);
    int cells = G.x * G.y;
    // The peaks, gathered once (at most MAXP), then ranked among themselves.
    float sc[MAXP];
    int at[MAXP];
    int P = 0;
    for (int i = 0; i < 4096; i++) {
        if (i >= cells || P >= MAXP) break;
        float s = texelFetch(sTD2DInputs[0], ivec2(i % G.x, i / G.x), 0).r;
        if (s > 0.0) { sc[P] = s; at[P] = i; P++; }
    }
    int found = -1;
    for (int a = 0; a < MAXP; a++) {
        if (a >= P) break;
        int rank = 0;
        for (int b = 0; b < MAXP; b++) {
            if (b >= P) break;
            if (sc[b] > sc[a] || (sc[b] == sc[a] && b < a)) rank++;
        }
        if (rank == col) { found = at[a]; break; }
    }
    int count = min(P, int(uPick.z + 0.5));
    if (found < 0 || col >= count) {
        fragColor = row == 0 ? vec4(-1.0, -1.0, 0.0, 0.0) : vec4(-1.0, 0.0, 0.0, float(count));
        return;
    }
    ivec2 c = ivec2(found % G.x, found / G.x);
    vec4 p = texelFetch(sTD2DInputs[0], c, 0);
    fragColor = row == 0 ? vec4((vec2(c) + 0.5) / vec2(G), 2.0 * p.g / float(G.x), 2.0 * p.b / float(G.y))
                         : vec4(float(found + 1), 0.0, 0.0, float(count));
}
