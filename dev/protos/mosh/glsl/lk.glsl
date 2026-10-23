// DEV ONLY (datamosh round 1). Iterative Lucas-Kanade optical flow, written from
// B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to
// Stereo Vision" (1981): a 7x7 Gaussian-weighted window, the 2x2 normal equations solved per
// pixel, three Newton steps re-sampling the previous frame at the current estimate.
// Input 0: current luma, 1: previous luma (same size), 2: a coarser flow to start from (optional).
// Output rg: displacement v in UV units with current(x) = previous(x - v); b: confidence
// (smaller eigenvalue of the structure tensor, Shi-Tomasi); a: 1.
uniform vec4 uP;   // x: use input 2 as the start (0/1), y: regularization, z: max |v| in pixels here
out vec4 fragColor;
float prv(vec2 p) { return texture(sTD2DInputs[1], p).r; }
void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    vec2 v = vec2(0.0);                       // pixels at this level
    if (uP.x > 0.5) v = texture(sTD2DInputs[2], uv).rg / px;
    float C[49];
    for (int j = 0; j < 7; j++)
    for (int i = 0; i < 7; i++)
        C[j * 7 + i] = texture(sTD2DInputs[0], uv + vec2(float(i - 3), float(j - 3)) * px).r;
    float conf = 0.0;
    for (int it = 0; it < 3; it++) {
        float a11 = 0.0, a12 = 0.0, a22 = 0.0, b1 = 0.0, b2 = 0.0;
        for (int j = 0; j < 7; j++)
        for (int i = 0; i < 7; i++) {
            vec2 o = vec2(float(i - 3), float(j - 3));
            float w = exp(-dot(o, o) / 8.0);
            vec2 q = uv + (o - v) * px;
            float gx = 0.5 * (prv(q + vec2(px.x, 0.0)) - prv(q - vec2(px.x, 0.0)));
            float gy = 0.5 * (prv(q + vec2(0.0, px.y)) - prv(q - vec2(0.0, px.y)));
            float e = C[j * 7 + i] - prv(q);
            a11 += w * gx * gx; a12 += w * gx * gy; a22 += w * gy * gy;
            b1 += w * gx * e;   b2 += w * gy * e;
        }
        float h = 0.5 * (a11 + a22);
        conf = h - sqrt(0.25 * (a11 - a22) * (a11 - a22) + a12 * a12);
        a11 += uP.y; a22 += uP.y;
        float det = a11 * a22 - a12 * a12;
        vec2 dv = -vec2(a22 * b1 - a12 * b2, a11 * b2 - a12 * b1) / det;
        v += clamp(dv, -2.0, 2.0);
        float m = length(v);
        if (m > uP.z) v *= uP.z / m;
    }
    fragColor = vec4(v * px, conf, 1.0);
}
