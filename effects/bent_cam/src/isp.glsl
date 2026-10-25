// Bent Cam (touchdesigner-effects, MIT). The camera's own processing. Each pixel's two missing colors are filled
// in from its neighbors (bilinear demosaicing, which is where moire turns to color), then come gamma, the contrast
// and saturation cheap webcams push, and the red guard. In the loop, contrast and saturation build up on every
// pass, and the guard keeps reds short of WCAG's red flash line as they do. It runs once a camera frame (30 a
// second) and holds its picture in between, so the loop goes round at the camera's rate whatever
// TouchDesigner's frame rate is.
// Inputs: 0 the sensor (r), 1 the camera's last picture (feed_fb). Out: R'G'B', the camera's picture.
uniform vec4 uIsp;    // x a new camera frame (1) or not (0), y Contrast, z Saturation
out vec4 fragColor;
#define CHROMA_MAX 0.3      // the most color (distance from gray, R'G'B') Saturation builds up to
#define TNR 0.5             // how much of the last frame each new one keeps (temporal noise reduction)

int bayer(ivec2 p) { return (p.x & 1) + (p.y & 1); }   // RGGB: 0 red, 1 green, 2 blue

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy), sz = ivec2(uTDOutputInfo.res.zw);
    if (uIsp.x < 0.5 && ivec2(uTD2DInfos[1].res.zw) == sz) {
        fragColor = texelFetch(sTD2DInputs[1], p, 0);
        return;
    }
    vec3 acc = vec3(0.0), wsum = vec3(0.0);
    for (int dy = -1; dy <= 1; dy++)
    for (int dx = -1; dx <= 1; dx++) {
        ivec2 q = clamp(p + ivec2(dx, dy), ivec2(0), sz - 1);
        float w = float((2 - abs(dx)) * (2 - abs(dy)));
        int ch = bayer(q);
        acc[ch] += w * texelFetch(sTD2DInputs[0], q, 0).r;
        wsum[ch] += w;
    }
    vec3 c = pow(max(acc / max(wsum, vec3(1e-6)), 0.0), vec3(1.0 / 2.2));
    c = 0.5 + (c - 0.5) * uIsp.y;
    // Saturation scales each color's distance from its gray, eased toward CHROMA_MAX: round the loop it builds up
    // to a vivid color and stops there, instead of every hue running to the one pure primary that grows fastest.
    float y = dot(c, vec3(0.299, 0.587, 0.114));
    vec3 d = c - y;
    float m = length(d), ms = m * uIsp.z;
    c = clamp(y + d * (m > 1e-5 ? CHROMA_MAX * tanh(ms / CHROMA_MAX) / m : uIsp.z), 0.0, 1.0);
    c = pow(redGuard(pow(c, vec3(2.2))), vec3(1.0 / 2.2));
    // Temporal noise reduction, as webcams do it: each frame blended with the last one the camera put out.
    vec4 last = texelFetch(sTD2DInputs[1], p, 0);
    if (ivec2(uTD2DInfos[1].res.zw) == sz) c = mix(c, last.rgb, TNR * last.a);
    fragColor = vec4(c, 1.0);
}
