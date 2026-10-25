// touchdesigner-effects (MIT), Slit-Scan: the history's input frames, newest first. Three rings (the pictures, their
// flow, the stamps) are written once a cook, in step, so a slot's stamp describes its picture: which cook wrote it (a
// serial), which input frame it holds (an id), when that frame came and when the cook was. A clip slower than the
// project fills several slots with one frame; each frame is listed at the first slot it appears in, where its flow
// is the movement since the frame before it.
// Walking back from the newest slot, a slot is history while its serial is the next one down and its cook came at
// most uF.y seconds before the newer one's. Memory the rings never wrote, slots from before they were reallocated
// (History changed) and slots left from before a pause (nothing used the output, so nothing cooked) all fail that,
// and never show.
// Inputs: sTD2DInputs[0] this cook's stamp (stamp.glsl, 2 x 1), sTD2DArrayInputs[0] the stamps ring.
// Out (N x 2, N the ring's size). Row 0, per frame j: r its slot (-1 past the last frame), g how long ago it came
// (seconds), b how many frames there are, a how far back the history reaches (seconds). Row 1: r 1 when frame j
// came at a cut (its flow means nothing), g the gap between the input's frames now (seconds).
uniform vec4 uF;   // x: the clock's wrap (CLOCK), y: the longest gap between cooks the history survives (seconds)
out vec4 fragColor;
const float SERIALS = 1048576.0;

vec4 stampAt(int slot, int px) { return texelFetch(sTD2DArrayInputs[0], ivec3(px, 0, slot), 0); }
float since(float now, float then) { return mod(now - then + uF.x, uF.x); }

void main() {
    int j = int(gl_FragCoord.x);
    int row = int(gl_FragCoord.y);
    int n = textureSize(sTD2DArrayInputs[0], 0).z;
    vec4 cur = texelFetch(sTD2DInputs[0], ivec2(0, 0), 0);
    int newest = -1;
    for (int i = 0; i < n; i++) {
        if (stampAt(i, 0).r == cur.r) { newest = i; break; }
    }
    if (newest < 0) {
        fragColor = vec4(-1.0, 0.0, 0.0, 0.0);
        return;
    }
    vec4 st = stampAt(newest, 0);
    float id = st.g, came = st.b, tNewer = cur.a, cut = 0.0, reach = 0.0;
    int first = newest, k = 0;
    vec2 mine = vec2(-1.0, 0.0);
    float mineCut = 0.0;
    for (int a = 0; a < n; a++) {
        int s = (newest - a + n) % n;
        st = stampAt(s, 0);
        if (st.r != mod(cur.r - float(a) + SERIALS, SERIALS) || since(tNewer, st.a) > uF.y) break;
        if (st.g != id) {           // an older frame starts here: the newer one first appeared one slot later
            if (k == j) { mine = vec2(float(first), since(cur.a, came)); mineCut = cut; }
            k++;
            id = st.g;
            came = st.b;
        }
        first = s;
        cut = stampAt(s, 1).r;
        tNewer = st.a;
        reach = since(cur.a, st.a);
    }
    // The oldest frame: where it first appeared may have left the ring, but it is never the newer of two frames, so
    // its flow is never read.
    if (k == j) { mine = vec2(float(first), since(cur.a, came)); mineCut = cut; }
    float gap = texelFetch(sTD2DInputs[0], ivec2(1, 0), 0).g;
    fragColor = row == 0 ? vec4(mine, float(k + 1), reach) : vec4(mineCut, gap, 0.0, 1.0);
}
