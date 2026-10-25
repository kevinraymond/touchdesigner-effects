// touchdesigner-effects (MIT), Slit-Scan: the picture as it was, from the history (pasted in front of scan.glsl and
// slit.glsl). frames.glsl lists the input frames newest first; past() finds the two either side of the moment asked
// for and fills in between them.
// Inputs: sTD2DInputs[0] the live picture, sTD2DInputs[1] the frames table (frames.glsl); sTD2DArrayInputs[0] the
// pictures, sTD2DArrayInputs[1] the flow each frame came with (lib lk.glsl at a quarter of the input's size: rg the
// displacement v in UV units since the frame before, current(x) = previous(x - v)).

uniform vec4 uTear;   // x: how much further back a beat's tears look (seconds; 0 none), y: the beat's number

vec4 entry(int j) { return texelFetch(sTD2DInputs[1], ivec2(j, 0), 0); }
float cameAtCut(int j) { return texelFetch(sTD2DInputs[1], ivec2(j, 1), 0).r; }
// How far back the history reaches (seconds): while it fills, after a pause or a change of History, less than Delay.
float reach() { return max(entry(0).a, 0.0); }
// The gap between the input's frames. Every moment is looked up this much later than asked: a moment between the
// newest frame and now has no next frame to fill in toward, so without it the picture would hold each frame (a
// slow clip's slit laid steps). The picture lags the input by one of its frames, as frame interpolation must.
float lead() { return max(texelFetch(sTD2DInputs[1], ivec2(0, 1), 0).g, 0.0); }

// Frame j's picture. The newest is the live input itself, at its full size whatever History Size is.
vec4 framePic(int j, float slot, vec2 uv) {
    if (j == 0) return texture(sTD2DInputs[0], uv);
    return texture(sTD2DArrayInputs[0], vec3(uv, slot));
}

// A beat's tears: how much further back the line at t (0-1 across the picture: rows down from the top, or Slit's lines
// across its film) looks, 0 outside them. A few thin slivers, one in each third of the picture so they stay apart, too
// little of it to count as a flash (as Glitch's are). A band of time
// running through the map on every beat moved whole areas back and forth wherever the picture moved, and flashed (red
// flowers and koi at Calm, 3 and 4 a second); so did Slit's film surging on the beat (3 a second).
float tear(float t) {
    if (uTear.x <= 0.0) return 0.0;
    float row = t * 720.0;                                  // lines in, at 720 across
    float d = 0.0;
    for (int k = 0; k < 3; k++) {
        uint h = ihash(uint(uTear.y) * 7u + uint(k) + 1u);
        float at = 24.0 + 240.0 * float(k) + float(h % 192u);
        float wide = 1.0 + float((h >> 12) % 3u);           // 2 to 6 lines wide
        if (abs(row - at) < wide) d = uTear.x * (0.5 + float((h >> 20) % 64u) / 128.0);
    }
    return d;
}

// The picture at uv as it was d seconds ago. fill: 0 Flow (the two frames either side warped along the movement
// between them to that moment, then mixed), 1 Blend (mixed), 2 Steps (the frame that was showing).
vec4 past(vec2 uv, float d, int fill) {
    d += lead();
    vec4 e0 = entry(0);
    int n = int(e0.b);
    if (e0.r < 0.0 || n < 2 || d <= e0.g) return texture(sTD2DInputs[0], uv);
    vec4 last = entry(n - 1);
    if (d >= last.g) return framePic(n - 1, last.r, uv);
    // The newest frame that came at least d ago (frames are listed newest first, so their ages rise).
    int lo = 1, hi = n - 1;
    while (lo < hi) {
        int mid = (lo + hi) / 2;
        if (entry(mid).g >= d) hi = mid; else lo = mid + 1;
    }
    vec4 a = entry(lo), b = entry(lo - 1);           // a showing d seconds ago, b the next one
    float u = clamp((a.g - d) / max(a.g - b.g, 1e-4), 0.0, 1.0);
    if (fill == 2) return framePic(lo, a.r, uv);
    if (fill == 1 || cameAtCut(lo - 1) > 0.5) return mix(framePic(lo, a.r, uv), framePic(lo - 1, b.r, uv), u);
    // What is at uv at that moment was at uv - u v in a and is at uv + (1 - u) v in b, v the movement from a to b.
    vec2 v = texture(sTD2DArrayInputs[1], vec3(uv, b.r)).rg;
    return mix(framePic(lo, a.r, uv - u * v), framePic(lo - 1, b.r, uv + (1.0 - u) * v), u);
}
