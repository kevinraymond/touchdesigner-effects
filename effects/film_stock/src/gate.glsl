// Film Stock (touchdesigner-effects, MIT). The gate: the film is never quite still in the camera's or the projector's
// gate. It weaves sideways and jumps up and down by a few micrometers from frame to frame (the sprockets' play) and
// drifts slowly as the loop breathes, so the whole picture wanders: on 35 mm barely, on Super 8, whose frame is a
// quarter the height, four times as far on screen. Each beat kicks the film in the gate (a jump down, settling back),
// and a splice (a drop) rolls the frame line through: the picture drops by a tenth of its height and climbs back over
// a few frames, the black between frames showing above it. The picture is resampled with Catmull-Rom (lib
// common.glsl), so sub-pixel movement neither blurs nor rings, and comes out in linear light as the exposure the film
// sees, Exposure stops over or under.
// Inputs: 0 the picture (held at the film's frame rate). Out: linear light, alpha 1.
uniform vec4 uW;      // x Weave 0-1, y the beat's kick (0-1, Beat Kick x its envelope), z the splice (1 at the cut, falling
                      // to 0), w Exposure (stops)
out vec4 fragColor;
#define WEAVE_UM 20.0     // the slow weave at Weave 1, in micrometers
#define JITTER_UM 6.0     // the frame-to-frame jitter at Weave 1
#define KICK 0.025        // a beat's kick at Beat Kick 1, of the picture's height
#define SPLICE 0.12       // a splice drops the picture this far, of its height

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    float px = um(res.y), t = uF.y;
    uint f = frameSeed();
    vec2 d = vec2(0.0);                                      // how far the frame sits from true, in pixels
    d.x += WEAVE_UM * uW.x * (0.6 * wave(t * 0.7, 11u) + 0.4 * wave(t * 1.9, 12u)) / px;
    d.y += WEAVE_UM * uW.x * (0.6 * wave(t * 0.9, 13u) + 0.4 * wave(t * 2.3, 14u)) / px;
    d += JITTER_UM * uW.x * (vec2(die(f, 1u, 21u), die(f, 2u, 21u)) * 2.0 - 1.0) / px;
    d.y -= KICK * uW.y * res.y;
    float roll = SPLICE * uW.z;
    vec2 uv = vUV.st - d / res;
    uv.y += roll;
    vec3 c = toLinear(clamp(sampleCR(0, uv).rgb, 0.0, 1.0)) * exp2(uW.w);
    if (uv.y > 1.0) c = vec3(0.0);                           // the frame line above the frame
    fragColor = vec4(c, 1.0);
}
