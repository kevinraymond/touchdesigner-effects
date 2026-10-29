// touchdesigner-effects (MIT), Caustics: the water's surface at half the picture's size, as heights and slopes, and the
// water's depth under it. The surface is the wave equation's height field (water.glsl, a quarter of the picture's
// size, read smoothly) plus a base sea of SWELLS slow swells, sine waves heading roughly with the wind, their lengths
// spread about Size, each sloping at most uH.w (steeper as Size grows, so they focus at the same depth), moving with deep water's dispersion (a wave of length L takes
// PERIOD x sqrt(L / Size) seconds), so the pool is never still. They are computed here, every frame, not played back.
// The depth is Depth x the picture's height; with a depth map or mask on input 3, nearer is shallower, down to half of
// it. (Up to one and a half, the far water lay past where the swells focus the light best, and their lines crossed
// into a hard net that hid the floor.)
// The SWELL table (direction, length as a share of Size, phase) is written in front of this shader by the builder.
// Inputs: 0 the picture (only its size: this pass is half of it), 1 the water (water.glsl), 2 input 3 as nearness,
// softened (lib depth_near.glsl, then a blur, so a sudden step in the depth doesn't seam the light).
// Out (half size, 32-bit float): r the height, g and b its slope across and up, a the water's depth (all in this
// map's pixels).
uniform vec4 uS;   // x Size (a share of the width), y the swells' height (Waves, with loudness), z the swells' clock
                   // (s, Wind's speed), w the period of a Size swell (s)
uniform vec4 uH;   // x the wave equation's heights in this map's pixels (Waves), y Depth (a share of the height),
                   // z 1 when input 3 sets the depth, w the swells' slope
out vec4 fragColor;
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = gl_FragCoord.xy;
    vec2 uv = p / res;
    // the wave equation's water, its slope over two of its own pixels
    vec2 w = 1.0 / vec2(textureSize(sTD2DInputs[1], 0));
    float scale = uH.x * res.y / float(textureSize(sTD2DInputs[1], 0).y);
    float h = texture(sTD2DInputs[1], uv).r * scale;
    vec2 g = vec2(texture(sTD2DInputs[1], uv + vec2(w.x, 0.0)).r - texture(sTD2DInputs[1], uv - vec2(w.x, 0.0)).r,
                  texture(sTD2DInputs[1], uv + vec2(0.0, w.y)).r - texture(sTD2DInputs[1], uv - vec2(0.0, w.y)).r)
             * scale / (2.0 * w * res);
    // the swells
    float lam0 = uS.x * res.x;
    for (int i = 0; i < SWELLS; i++) {
        vec4 s = SWELL[i];
        float lam = lam0 * s.z;
        float k = 6.2831853 / lam;
        float om = 6.2831853 / (uS.w * sqrt(s.z));
        float a = uS.y * uH.w / k;
        float ph = k * dot(s.xy, p) - om * uS.z + s.w;
        h += a * sin(ph);
        g += a * k * cos(ph) * s.xy;
    }
    float near = texture(sTD2DInputs[2], uv).r;
    float depth = uH.y * res.y * (uH.z > 0.5 ? 1.0 - 0.5 * near : 1.0);
    fragColor = vec4(h, g, depth);
}
