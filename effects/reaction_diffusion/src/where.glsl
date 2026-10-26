// Reaction-Diffusion (touchdesigner-effects, MIT): where the pattern may grow, and how much ink the picture asks for,
// at the grid's size. Grow On: Everywhere; Brightness, what is bright; Movement, what moved in the last moments
// (moved.glsl); Depth, what stands in front of its surroundings in the depth map on input 3 (lib depth_find.glsl);
// Mask, what is inside the mask on input 3. Sensitivity lowers the bar in each (for Depth, through depth_find's Far
// Limit). The ink follows the picture's darkness, stretched between its darkest and brightest (exposure.glsl, at
// least uG.z apart), then bent by a power that puts Ink Level's share of ink at the middle, and Contrast scales it
// about the middle (0: Ink Level everywhere). Light on Dark draws its lines light, so they follow the picture's
// brightness instead. Loud music adds ink (uG.y). Both ease over uE.y seconds (each frame 1 - exp(-step / uE.y)
// of the way to now), so flicker in the picture (drifting smoke, a video's noise) can't flip the lines back and forth
// while a change that lasts comes through: the lines followed it at once, and the smoke on the test clip flickered
// whole areas between broad and thin lines (dev/flash.py).
// Inputs: 0 the picture at the grid's size, 1 for Movement the motion (r), for Depth the subject (r 1 inside), for
// Mask the mask (r), else black; 2 the picture's darkest (r) and brightest (g); 3 this pass last frame (read by
// UV: any size; a 1 once set, so the first frame takes the picture's tone at once instead of easing up from paper).
// Out: r where it may grow, 0-1; g the ink asked for, 0-1; a 1.
uniform vec4 uW;   // x Grow On (0 Everywhere, 1 Brightness, 2 Movement, 3 Depth, 4 Mask), y Sensitivity (0-1),
                   // z Contrast (0-2), w 1 for Light on Dark
uniform vec4 uG;   // x Ink Level (0-1), y the ink loudness adds, z the least range stretched
uniform vec4 uE;   // x the frame step (s), y how long the easing takes (s)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    float l = luma(texture(sTD2DInputs[0], uv).rgb);
    float m = texture(sTD2DInputs[1], uv).r;
    float s = uW.y, grow = 1.0;
    if (uW.x > 0.5 && uW.x < 1.5) {
        float lo = mix(0.8, 0.2, s);
        grow = smoothstep(lo, lo + 0.15, l);
    } else if (uW.x < 2.5 && uW.x > 1.5) {
        float lo = 0.06 * pow(1.0 / 8.0, s);         // a change in brightness of 0.06 at 0, 0.0075 at 1
        grow = smoothstep(lo, 3.0 * lo, m);
    } else if (uW.x < 3.5 && uW.x > 2.5) {
        grow = m;
    } else if (uW.x > 3.5) {
        float lo = mix(0.9, 0.1, s);
        grow = smoothstep(lo, lo + 0.05, m);
    }
    vec2 range = texture(sTD2DInputs[2], vec2(0.5)).rg;
    float mid = 0.5 * (range.x + range.y), half_ = 0.5 * max(range.y - range.x, uG.z);
    float tone = clamp(0.5 + 0.5 * (l - mid) / half_, 0.0, 1.0);
    float lit = clamp(uW.w > 0.5 ? uG.x : 1.0 - uG.x, 0.02, 0.98);   // what the middle comes out as
    tone = pow(tone, log(lit) / log(0.5));
    float ink = uW.w > 0.5 ? tone : 1.0 - tone;
    ink = clamp(0.5 + (ink - 0.5) * uW.z + (uG.x - 0.5) * (1.0 - min(uW.z, 1.0)) + uG.y, 0.0, 1.0);
    vec4 last = texture(sTD2DInputs[3], uv);
    vec2 now = vec2(grow, ink);
    fragColor = vec4(last.a > 0.5 ? mix(last.rg, now, 1.0 - exp(-uE.x / uE.y)) : now, 0.0, 1.0);
}
