// Blob Track (touchdesigner-effects, MIT). Which of the Blob Track TOP's blobs may get a box: the
// longer side between Min Size and Max Size (as a fraction of the picture's height), and not
// mostly inside a bigger one (a part of something already boxed). Their rank (bt_pick.glsl keeps
// the biggest) favors blobs that already have a box, so boxes near the Max Count cut don't swap in
// and out from frame to frame.
// Input 0: its Info CHOP as a texture, one channel per row: num_blobs, then id, u, v, width and
// height for each blob (u, v its center, all 0-1). Input 1: the picture (for its shape). Input 2:
// track.glsl's previous output (which IDs have a box).
// Out, column j = blob j: row 0 center u, v, width, height; row 1 ID, rank score (-1: no box), 0, count.
uniform vec4 uPick;   // x min size, y max size
out vec4 fragColor;
#define MAXIN 128

float D(int r) { return texelFetch(sTD2DInputs[0], ivec2(0, r), 0).r; }
vec4 box(int j) { return vec4(D(2 + 5 * j), D(3 + 5 * j), D(4 + 5 * j), D(5 + 5 * j)); }

void main() {
    int j = int(gl_FragCoord.x), row = int(gl_FragCoord.y);
    float asp = uTD2DInfos[1].res.z / max(uTD2DInfos[1].res.w, 1.0);
    int n = clamp(int(D(0) + 0.5), 0, min(MAXIN, (textureSize(sTD2DInputs[0], 0).y - 1) / 5));
    if (j >= n) {
        fragColor = row == 0 ? vec4(-1.0, -1.0, 0.0, 0.0) : vec4(-1.0, -1.0, 0.0, float(n));
        return;
    }
    vec4 b = box(j);
    if (row == 0) {
        fragColor = b;
        return;
    }
    float area = b.z * b.w;
    float side = max(b.z * asp, b.w);
    bool keep = side >= uPick.x && side <= uPick.y;
    for (int k = 0; k < MAXIN; k++) {
        if (k >= n || !keep) break;
        vec4 o = box(k);
        float oa = o.z * o.w;
        if (k == j || oa < area || (oa == area && k > j)) continue;
        vec2 lo = max(b.xy - 0.5 * b.zw, o.xy - 0.5 * o.zw), hi = min(b.xy + 0.5 * b.zw, o.xy + 0.5 * o.zw);
        vec2 ov = max(hi - lo, vec2(0.0));
        if (ov.x * ov.y >= 0.75 * area && max(o.z * asp, o.w) <= uPick.y) keep = false;
    }
    float id = D(1 + 5 * j), score = area;
    for (int s = 0; s < 64 && keep; s++) {
        vec4 m = texelFetch(sTD2DInputs[2], ivec2(s, 1), 0);
        if (m.y > 0.0 && abs(m.x - id) < 0.5) { score = 2.0 * area; break; }
    }
    fragColor = vec4(id, keep ? score : -1.0, 0.0, float(n));
}
