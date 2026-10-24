// Blob Track (touchdesigner-effects, MIT). GPU Grid detector, step 1 of 3: how much of each grid
// cell the mask covers, smoothed over time (in seconds). No Blob Track TOP and nothing read back
// to the CPU: the cheap detector.
// Inputs: 0 the mask (mask.glsl); 1 this TOP's previous output (a Feedback TOP).
// Out: r the cell's smoothed coverage, g its brightest mask value now.
uniform vec4 uClock;   // x seconds since the last frame, y smoothing time (s)
out vec4 fragColor;

void main() {
    vec2 cell = floor(gl_FragCoord.xy);
    vec2 G = uTDOutputInfo.res.zw;
    float sum = 0.0, mx = 0.0;
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            float m = texture(sTD2DInputs[0], (cell + (vec2(x, y) + 0.5) / 4.0) / G).r;
            sum += m;
            mx = max(mx, m);
        }
    }
    float old = texelFetch(sTD2DInputs[1], ivec2(cell), 0).r;
    float k = 1.0 - exp(-uClock.x / max(uClock.y, 1e-3));
    fragColor = vec4(mix(old, sum / 16.0, k), mx, 0.0, 1.0);
}
