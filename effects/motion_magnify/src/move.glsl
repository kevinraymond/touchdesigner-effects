// touchdesigner-effects (MIT), Motion Magnify: how far each part of the picture is from where it rests. The displacement
// travels with the content (semi-Lagrangian: each pixel takes the displacement from where its content was a frame ago)
// and adds this frame's motion, so it follows a point as it moves, as Liu et al.'s Lagrangian motion magnification
// follows its tracked points (SIGGRAPH 2005). It leaks back to 0 over the leak's time, so where something has moved
// for long its rest moves with it, and only movement that goes back and forth faster than that is left; and it is
// eased over the easing's time, so movement faster than that (a shake, the flow's noise) is left out. Together they
// keep the movements of one speed, the Timing parameter's. Nothing here filters the picture's pixels over time: the
// motion is measured (lib optical_flow(), flow_speed()) and the picture is moved (warp.glsl).
// Inputs: 0 the motion (lib speed.glsl: rg cells per second at a quarter of the picture's size, b confidence), 1 this
// pass last frame (read by UV), 2 the pace (lib pace.glsl, 1 x 1: a the cut now).
// Out: rg the displacement eased, ba the displacement (both UV units: the content here rests that far back).
uniform vec4 uM;   // x the frame step (s), y the leak's time (s), z the easing's time (s)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    // A cut starts again: everything rests where it is now.
    if (texelFetch(sTD2DInputs[2], ivec2(0), 0).a > 0.5) { fragColor = vec4(0.0); return; }
    vec2 v = texture(sTD2DInputs[0], uv).rg / uTD2DInfos[0].res.zw * uM.x;
    vec4 last = texture(sTD2DInputs[1], uv - v);
    vec2 d = (last.ba + v) * exp(-uM.x / uM.y);
    vec2 s = mix(last.rg, d, 1.0 - exp(-uM.x / uM.z));
    fragColor = vec4(s, d);
}
