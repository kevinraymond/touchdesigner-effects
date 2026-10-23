// DEV ONLY. Synthetic test motion: textured orange and blue shapes moving over a static
// textured background, so optical flow has texture to lock onto.
uniform float uTime;
out vec4 fragColor;
float stripes(vec2 p, float f) { return 0.5 + 0.5 * sin(p.x * f) * sin(p.y * f * 0.7); }
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = vUV.st * vec2(res.x / res.y, 1.0);
    float t = uTime;
    vec3 col = vec3(0.18, 0.2, 0.24) + 0.12 * stripes(p, 40.0);       // static background
    // orange disc, horizontal sweep
    vec2 c1 = vec2(0.9 + 0.55 * sin(t * 0.9), 0.55 + 0.15 * sin(t * 1.7));
    vec2 q1 = p - c1;
    if (length(q1) < 0.22) col = vec3(0.95, 0.55, 0.15) * (0.6 + 0.4 * stripes(q1 + vec2(t * 0.0), 60.0));
    // blue rotating square
    vec2 c2 = vec2(0.45 + 0.1 * sin(t * 0.6), 0.4);
    float a = t * 0.8;
    vec2 q2 = mat2(cos(a), -sin(a), sin(a), cos(a)) * (p - c2);
    if (max(abs(q2.x), abs(q2.y)) < 0.16) col = vec3(0.2, 0.45, 0.9) * (0.5 + 0.5 * stripes(q2 * 1.3, 50.0));
    // light gray bar drifting down
    float yb = 0.5 + 0.45 * sin(t * 0.5);
    if (abs(p.y - yb) < 0.05 && p.x > 1.1) col = vec3(0.85) * (0.7 + 0.3 * stripes(p + vec2(0.0, -yb), 80.0));
    fragColor = vec4(col, 1.0);
}
