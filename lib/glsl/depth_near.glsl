// touchdesigner-effects (MIT), shared by the effects that read depth (lib/glsl, lib_glsl()).
// The depth map (or mask), small, as nearness: each output
// pixel averages a 4 x 4 grid of samples across the input pixels it covers, brighter nearer.
// Depth Type says what input 3 holds. Brighter Is Nearer (depth estimators, masks) is used as it is.
// The depth cameras give distance: the RealSense and Kinect TOPs from 0 to 1 over their range (Distance
// 0-1), the Kinect Azure TOP in meters (Distance in Meters, scaled by Max Distance); both are flipped
// to nearness, and their black (0 m: the camera got no reading there, a shadow or a dark screen) is
// left out of the average. A pixel with no reading at all gets nearness 0 and validity 0, and
// depth_find.glsl treats it as nothing.
// Inputs: 0 the depth map or mask (input 3, or input 1's brightness).
// Out: r nearness 0-1, g how much of the pixel had a reading, 0-1.
uniform vec4 uNear;   // x Depth Type (0 Brighter Is Nearer, 1 Distance 0-1, 2 Distance in Meters), y Max Distance (m)
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
                d = 1.0 - clamp(uNear.x > 1.5 ? d / max(uNear.y, 0.01) : d, 0.0, 1.0);
            }
            sum += d;
            n += 1.0;
        }
    }
    fragColor = vec4(n > 0.0 ? sum / n : 0.0, n / 16.0, 0.0, 1.0);
}
