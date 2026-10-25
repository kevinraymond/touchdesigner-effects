// Datamosh-style decoder: the effect's picture (touchdesigner-effects, MIT). It imitates what a
// video decoder shows when keyframes go missing; it never touches a real codec stream.
//
// A codec's P-frame predicts the picture from the previous decoded picture moved by motion
// vectors, then adds a residual: whatever the motion didn't explain. Here the motion is this
// effect's own estimate (Smear: optical flow per pixel; Blocks: one vector per 16 px block, a
// quantized residual and frozen blocks) and the residual is the input minus the previous input
// moved the same way. While the picture matches the input the result is the input; once it
// doesn't (a dropped keyframe at a cut, a withheld residual, a held motion field) the motion keeps
// pushing the old picture around. Recovery and keyframes fade back to the input; nothing cuts.
//
// Inputs: 0 input, 1 previous output (Feedback TOP), 2 previous input frame, 3 motion (UV units,
// current(x) = previous(x - v)), 4 the clock (1 x 1: r a new input frame, g a cut).
uniform vec4 uP1;   // Mode (0 Smear, 1 Blocks), Mosh, Motion, Recovery (s)
uniform vec4 uP2;   // Chroma, Hold, Frozen Blocks, Mosh Cuts
uniform vec4 uP3;   // Fade (s), Level, Song Structure, block size (px)
uniform vec4 uAud;  // input 2's level and build, skip envelope (0..1), keyframe progress (0: none)
uniform vec4 uBeat; // a beat's surge (1 at the beat, falling to 0), Beat Surge
uniform vec4 uPush; // at a full surge: how much further the motion pushes, its bloom (zoom per second), how fast
                    // the picture catches up as it fades (per second); how much further a skip pushes
uniform vec4 uT;    // seconds, seconds since the last frame
out vec4 fragColor;

// Residuals are quantized with a dead zone, as codecs do: small changes are lost.
vec3 quant(vec3 r, float q) { return sign(r) * floor(abs(r) / q + 0.35) * q; }

void main() {
    vec2 uv = vUV.st;
    bool blocks = uP1.x > 0.5;
    float bs = uP3.w;
    vec2 B = floor(gl_FragCoord.xy / bs);
    vec4 I = texture(sTD2DInputs[0], uv);
    vec4 st = texelFetch(sTD2DInputs[4], ivec2(0), 0);
    float dt = clamp(uT.y, 0.0, 0.1);
    float build = clamp(uAud.y, 0.0, 1.0) * uP3.z, skip = clamp(uAud.z, 0.0, 1.0), key = clamp(uAud.w, 0.0, 1.0);
    float hold = uP2.y, env = clamp(uBeat.x, 0.0, 1.0), surge = env * uBeat.y;
    // A beat's surge blooms the decoder's own picture: it zooms out from the middle, every frame, as
    // far as the surge says, and with no corrections arriving the zoom smears.
    vec2 bloom = (uv - 0.5) * uPush.y * surge * dt;
    vec3 D = sampleCR(1, uv - bloom).rgb;

    // How much of each frame's residual is withheld: Mosh, more when it is loud, most through a
    // build; all of it during a skip or Hold, and at a beat's surge; none while a keyframe fades in.
    float m = uP1.y + (1.0 - uP1.y) * uP3.y * uAud.x;
    m = mix(m, max(m, 0.9), build);
    float g = key > 0.0 ? 1.0 : (1.0 - m) * (1.0 - skip) * (1.0 - hold) * (1.0 - surge);
    // The decoder moves its picture Motion times as far as the input moved, further at a beat's
    // surge and through a skip (whose motion is held: the bloom).
    float push = uP1.z * (1.0 + uPush.x * surge + uPush.w * skip);
    // Chroma: brightness takes its residual, color is left behind.
    float gy = mix(g, 1.0, uP2.x), gc = g * (1.0 - uP2.x);

    vec3 S = D;
    if (st.r > 0.5) {                                   // a new input frame
        if (st.g > 0.5) {                               // a cut: drop its keyframe, or take it
            if (uP2.w < 0.5) S = I.rgb;
        } else {
            vec2 v = blocks
                ? texelFetch(sTD2DInputs[3], ivec2((B + 0.5) * bs * uTD2DInfos[3].res.zw / uTDOutputInfo.res.zw), 0).rg
                : texture(sTD2DInputs[3], uv).rg;
            vec3 pred = sampleCR(1, uv - bloom - v * push).rgb;  // the decoder moves its picture push times as far
            vec3 r = I.rgb - sampleCR(2, uv - v).rgb;        // as the encoder's residual expects
            if (blocks) r = quant(r, 1.0 / 32.0);
            float ry = luma(r);
            S = pred + gy * ry + gc * (r - ry);
            // Frozen blocks miss the update (a few every quarter second, more during a skip).
            if (blocks && hash12(B + floor(uT.x * 4.0) * vec2(17.13, 3.71)) < uP2.z * (1.0 + 4.0 * skip)) S = D;
        }
    }
    // Recovery: every frame a little of the way back to the input; paused by a skip or Hold, slowed
    // by a build. Blocks recover unevenly, block by block. As a beat's surge fades the picture
    // catches up fast (not during a skip, whose smear is meant to stay), so each beat blooms and
    // comes back.
    float k = 3.0 / max(uP1.w, 0.05) * (1.0 - build) * (1.0 - skip) * (1.0 - hold);
    if (blocks) k *= 0.5 + hash12(B * 1.37 + 11.0);
    k += surge > 0.0 ? uPush.z * (1.0 - env) * (1.0 - skip) * (1.0 - hold) : 0.0;
    S = mix(S, I.rgb, 1.0 - exp(-k * dt));
    // Chroma: brightness follows the input within a fraction of a second; color doesn't.
    S += (luma(I.rgb) - luma(S)) * (1.0 - exp(-12.0 * uP2.x * dt));
    // A keyframe fades back to the input over Fade: all at once (Smear) or in a sweep of block
    // columns, left to right, each fading in (Blocks); swept columns stay clean until it ends.
    if (key > 0.0) {
        float s0 = blocks ? 0.7 * (B.x + 0.5) / ceil(uTDOutputInfo.res.z / bs) : 0.0;
        float e0 = blocks ? s0 + 0.3 : 1.0;
        float a = key < s0 ? 0.0 : (key >= e0 ? 1.0 : dt / max(uP3.x * (e0 - key), dt));
        S = mix(S, I.rgb, clamp(a, 0.0, 1.0));
    }
    fragColor = vec4(clamp(S, 0.0, 1.0), I.a);
}
