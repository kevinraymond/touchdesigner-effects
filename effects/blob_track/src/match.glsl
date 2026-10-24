// Blob Track (touchdesigner-effects, MIT). Detectors hand out a new ID when a blob splits, merges
// or is found again; without help its box would fade out while a new one fades in. For each box
// whose blob has just vanished, this finds the new blob (an ID no box holds) that overlaps it
// most, which track.glsl lets it take over.
// Inputs: 0 the detector's list (bt_pick.glsl or grid_pick.glsl); 1 track.glsl's previous output.
// Out, column = slot: x the list entry to take over (-1 none), y how well they overlap (0-1).
out vec4 fragColor;
#define N 64

vec4 L(int i, int r) { return texelFetch(sTD2DInputs[0], ivec2(i, r), 0); }
vec4 S(int s, int r) { return texelFetch(sTD2DInputs[1], ivec2(s, r), 0); }

bool idHeld(float id) {
    for (int s = 0; s < N; s++) {
        vec4 m = S(s, 1);
        if (m.y > 0.0 && abs(m.x - id) < 0.5) return true;
    }
    return false;
}

// Intersection over union of two boxes (center, size).
float iou(vec4 a, vec4 b) {
    vec2 lo = max(a.xy - 0.5 * a.zw, b.xy - 0.5 * b.zw), hi = min(a.xy + 0.5 * a.zw, b.xy + 0.5 * b.zw);
    vec2 ov = max(hi - lo, vec2(0.0));
    float i = ov.x * ov.y;
    return i / max(a.z * a.w + b.z * b.w - i, 1e-9);
}

void main() {
    int s = int(gl_FragCoord.x);
    vec4 m = S(s, 1);
    fragColor = vec4(-1.0, 0.0, 0.0, 0.0);
    if (m.y <= 0.0) return;
    int n = min(int(L(0, 1).w + 0.5), N);
    for (int i = 0; i < N; i++) {
        if (i >= n) break;
        if (abs(L(i, 1).x - m.x) < 0.5) return;     // still detected under its own ID
    }
    vec4 a = S(s, 0);
    float best = 0.25;
    int bj = -1;
    for (int i = 0; i < N; i++) {
        if (i >= n) break;
        if (idHeld(L(i, 1).x)) continue;
        float o = iou(a, L(i, 0));
        if (o > best) { best = o; bj = i; }
    }
    if (bj >= 0) fragColor = vec4(float(bj), best, 0.0, 0.0);
}
