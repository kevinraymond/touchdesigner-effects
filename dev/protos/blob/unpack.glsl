// DEV ONLY (blob round 1): repack the Info CHOP texture into a compact blob table, MAXB x 2,
// rgba32float, and find each blob's two nearest neighbors (O(n^2) once, not per pixel).
//   row 0, pixel i: center u, center v, width, height (normalized)
//   row 1, pixel i: id, nearest index, 2nd nearest index, blob count (-1 = none)
out vec4 fragColor;
void main() {
    int i = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    int n = nBlobs();
    vec2 res = vec2(1280.0, 720.0);
    if (i >= n) { fragColor = row == 0 ? vec4(-10.0, -10.0, 0.0, 0.0) : vec4(-1.0, -1.0, -1.0, float(n)); return; }
    int id; vec2 c, sz;
    blobAt(i, res, id, c, sz);
    if (row == 0) { fragColor = vec4(c / res, sz / res); return; }
    float d1 = 1e9, d2 = 1e9; int j1 = -1, j2 = -1;
    for (int j = 0; j < n; j++) {
        if (j == i) continue;
        vec2 cj = vec2(D(2 + 5 * j), D(3 + 5 * j)) * res;
        float d = distance(c, cj);
        if (d < d1) { d2 = d1; j2 = j1; d1 = d; j1 = j; }
        else if (d < d2) { d2 = d; j2 = j; }
    }
    fragColor = vec4(float(id), float(j1), float(j2), float(n));
}
