// Depth Particles (touchdesigner-effects, MIT). The depth map (or mask), small: each output pixel
// averages a 4 x 4 grid of samples across the input pixels it covers, as nearness, brighter nearer.
// With Polarity on Darker Is Nearer (TouchDesigner's RealSense TOP), a sample is flipped, and black
// means the camera got no reading there, so it is left out of the average; a pixel with no reading
// at all gets nearness 0 and validity 0, and find.glsl treats it as nothing.
// Inputs: 0 the depth map or mask (input 3, or input 1's brightness).
// Out: r nearness 0-1, g how much of the pixel had a reading, 0-1.
uniform vec4 uNear;   // x Polarity: 0 brighter is nearer, 1 darker is nearer (0 = no reading)
out vec4 fragColor;

void main() {
    vec2 src = vec2(textureSize(sTD2DInputs[0], 0));
    vec2 out_size = uTDOutputInfo.res.zw;
    vec2 base = floor(gl_FragCoord.xy) / out_size;     // this pixel's corner, as a fraction
    float sum = 0.0, n = 0.0;
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            vec2 uv = base + (vec2(x, y) + 0.5) / (4.0 * out_size);
            float d = texelFetch(sTD2DInputs[0], ivec2(uv * src), 0).r;
            if (uNear.x > 0.5) {
                if (d <= 0.0) continue;
                d = 1.0 - d;
            }
            sum += d;
            n += 1.0;
        }
    }
    fragColor = vec4(n > 0.0 ? sum / n : 0.0, n / 16.0, 0.0, 1.0);
}
