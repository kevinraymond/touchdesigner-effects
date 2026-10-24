// Blob Track (touchdesigner-effects, MIT). The picture's recent past, for Movement: the current
// frame and a background that follows it slowly (seconds behind, so what moves stands out from
// it but the place a thing just left does not). It advances only when the picture changes, so a
// 16 fps clip in a 60 fps project (each frame shown about four times) moves it once per clip
// frame, and the background's pace is set in seconds, not frames.
// Inputs: 0 the picture, small and gray; 1 this TOP's previous output (a Feedback TOP).
// Out: r the current frame, g the background, b 2 once started, a seconds since the last change.
uniform vec4 uClock;   // x seconds since the last frame, y background time constant (s)
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float cur = texelFetch(sTD2DInputs[0], p, 0).r;
    vec4 old = texelFetch(sTD2DInputs[1], p, 0);
    if (old.b < 1.5) {                       // the first frame
        fragColor = vec4(cur, cur, 2.0, 0.0);
        return;
    }
    // Has the picture changed since the frame kept in r? Every pixel reads the same 64 samples,
    // so every pixel reaches the same answer.
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    float diff = 0.0;
    for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
            ivec2 q = ivec2((vec2(x, y) + 0.5) / 8.0 * vec2(size));
            diff += abs(texelFetch(sTD2DInputs[0], q, 0).r - texelFetch(sTD2DInputs[1], q, 0).r);
        }
    }
    float since = old.a + uClock.x;
    if (diff < 0.02) {
        fragColor = vec4(old.rg, 2.0, since);
        return;
    }
    // A cut (or the first real frame after black, or cooking again after a pause) changes much
    // of the picture at once: start the background over rather than box everything for seconds.
    float k = diff / 64.0 > 0.12 ? 1.0 : 1.0 - exp(-since / max(uClock.y, 1e-3));
    fragColor = vec4(cur, mix(old.g, cur, k), 2.0, 0.0);
}
