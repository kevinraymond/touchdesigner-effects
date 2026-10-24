// Blob Track (touchdesigner-effects, MIT). The picture's recent past, for Movement: the current
// frame and a background that follows it slowly (seconds behind, so what moves stands out from
// it). Where the picture has stayed still for a while, the background catches up quickly: the
// place a thing has just left would otherwise stand out as a "ghost" trailing it for seconds,
// and boxes would follow the ghost. It advances only when the picture changes, so a 16 fps clip
// in a 60 fps project (each frame shown about four times) moves it once per clip frame, and its
// pace is set in seconds, not frames.
// Inputs: 0 the picture, small and gray; 1 this TOP's previous output (a Feedback TOP).
// Out: r the current frame, g the background, b 2 + seconds this pixel has stayed still (2 once
// started), a seconds since the picture last changed.
uniform vec4 uClock;   // x seconds since the last frame, y background time constant (s), z the same
                       // where the pixel has stayed still for w seconds or more
#define STILL 0.03     // a pixel that changes less than this between frames is still
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
        fragColor = vec4(old.rgb, since);
        return;
    }
    // A cut (or the first real frame after black, or cooking again after a pause) changes much
    // of the picture at once: start the background over rather than box everything for seconds.
    float still = abs(cur - old.r) < STILL ? old.b - 2.0 + since : 0.0;
    float tc = still >= uClock.w ? uClock.z : uClock.y;
    float k = diff / 64.0 > 0.12 ? 1.0 : 1.0 - exp(-since / max(tc, 1e-3));
    fragColor = vec4(cur, mix(old.g, cur, k), 2.0 + still, 0.0);
}
