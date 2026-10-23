// DEV ONLY (blob round 1): synthetic moving input for tracking tests. A dim, slowly drifting
// noise ground with bright blobs, squares and a ring on smooth paths, some merging and parting.
uniform float uTime;
out vec4 fragColor;

float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    float asp = res.x / res.y;
    vec2 p = vUV.st * vec2(asp, 1.0);
    float t = uTime;
    float g = 0.06 + 0.07 * vnoise(p * 3.0 + vec2(t * 0.07, 0.0)) + 0.05 * vnoise(p * 14.0 - vec2(0.0, t * 0.2));
    g += 0.05 * smoothstep(0.0, 1.0, vUV.t);
    vec3 col = vec3(g) * vec3(0.92, 0.96, 1.0);
    for (int i = 0; i < 16; i++) {
        float fi = float(i);
        float r1 = h21(vec2(fi, 1.0)), r2 = h21(vec2(fi, 2.0)), r3 = h21(vec2(fi, 3.0));
        vec2 c = vec2(0.5 * asp, 0.5) + vec2(0.42 * asp * sin(t * (0.23 + 0.25 * r1) + fi * 1.7),
                                             0.38 * sin(t * (0.19 + 0.21 * r2) + fi * 2.3 + 1.0));
        float r = (0.018 + 0.05 * r3) * (1.0 + 0.25 * sin(t * 1.3 + fi));
        float d;
        if (i % 4 == 1) {                       // squares, turning
            float a = t * 0.6 + fi;
            vec2 q = mat2(cos(a), -sin(a), sin(a), cos(a)) * (p - c);
            d = max(abs(q.x), abs(q.y)) / 0.85;
        } else if (i % 4 == 3) {                // elongated blobs (wide boxes)
            d = length((p - c) * vec2(0.5, 1.6));
        } else {
            d = length(p - c);
        }
        float m = smoothstep(r, r * 0.55, d);
        if (i == 6) m = smoothstep(0.012, 0.0, abs(length(p - c) - 0.09));   // a ring
        vec3 tint = mix(vec3(1.0, 0.78, 0.55), vec3(0.62, 0.78, 1.0), r2);
        col = max(col, m * tint * (0.65 + 0.35 * r1));
    }
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
