// touchdesigner-effects (MIT), shared by Fluid and VHS + CRT (lib/glsl, flow_speed()): the input's
// motion as a speed, at a quarter of the input's size, in cells (its pixels) per second. On a new
// input frame it takes the optical flow (lk.glsl: the displacement since the last input frame)
// smoothed over 5 x 5, each pixel weighted by how textured it is so flat areas borrow from their
// neighbors, and divides it by the gap between frames (pace.glsl). Between new frames it holds, so
// a slow clip that repeats a frame keeps moving like a live camera; when no new frame has come for
// a while (a paused clip) it dies away.
// A cut brings no motion: the flow across a cut is meaningless.
// Inputs: 0 the flow (lk4: rg displacement in UV units, b confidence), 1 this pass's previous output
// (Feedback TOP), 2 the pace (1 x 1). Out: rg the speed (cells per second), b the confidence, a 1.
uniform vec4 uM;   // x: seconds now (clock_seconds(), wrapped every 16384 s: compared modulo that), y: this
                   // frame's step (s), z: dead zone (cells per frame), w: hold (s)
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec4 pace = texelFetch(sTD2DInputs[2], ivec2(0), 0);
    vec4 prev = texture(sTD2DInputs[1], uv);
    if (pace.a > 0.5) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
    if (pace.b < 0.5) {
        float idle = mod(uM.x - pace.r, 16384.0);
        fragColor = vec4(prev.rgb * (idle > uM.w ? exp(-uM.y / 0.15) : 1.0), 1.0);
        return;
    }
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 acc = vec2(0.0);
    float wsum = 0.0, conf = 0.0, gsum = 0.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec4 f = texture(sTD2DInputs[0], uv + vec2(float(i), float(j)) * px);
        float g = exp(-float(i * i + j * j) / 4.0);
        float w = (f.b + 1e-5) * g;
        acc += w * f.rg;
        wsum += w;
        conf += f.b * g;
        gsum += g;
    }
    vec2 d = acc / wsum * res;                                  // cells moved since the last frame
    d *= smoothstep(uM.z, 2.0 * uM.z, length(d));
    fragColor = vec4(d / max(pace.g, 1e-3), conf / gsum, 1.0);
}
