// Blob Track (touchdesigner-effects, MIT). The blobs that may get a box (bt_clean.glsl), biggest
// first (those already boxed count double), at most as many as track.glsl has slots (Max Count
// limits the boxes showing there, not the blobs followed).
// Input 0: bt_clean.glsl.
// Out, column i = the i-th biggest: row 0 center u, v, width, height (0-1); row 1 ID, 0, 0, count.
uniform vec4 uPick;   // z most blobs to pass on
out vec4 fragColor;
#define MAXIN 128

vec4 C(int j, int r) { return texelFetch(sTD2DInputs[0], ivec2(j, r), 0); }

void main() {
    int col = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    int n = min(int(C(0, 1).w + 0.5), MAXIN);
    // The areas of those that may get a box, gathered once, then ranked among themselves.
    float area[MAXIN];
    int at[MAXIN];
    int P = 0;
    for (int j = 0; j < MAXIN; j++) {
        if (j >= n) break;
        float a = C(j, 1).y;
        if (a >= 0.0) { area[P] = a; at[P] = j; P++; }
    }
    int found = -1;
    for (int a = 0; a < MAXIN; a++) {
        if (a >= P) break;
        int rank = 0;
        for (int b = 0; b < MAXIN; b++) {
            if (b >= P) break;
            if (area[b] > area[a] || (area[b] == area[a] && b < a)) rank++;
        }
        if (rank == col) { found = at[a]; break; }
    }
    int count = min(P, int(uPick.z + 0.5));
    if (found < 0 || col >= count) {
        fragColor = row == 0 ? vec4(-1.0, -1.0, 0.0, 0.0) : vec4(-1.0, 0.0, 0.0, float(count));
        return;
    }
    fragColor = row == 0 ? C(found, 0) : vec4(C(found, 1).x, 0.0, 0.0, float(count));
}
