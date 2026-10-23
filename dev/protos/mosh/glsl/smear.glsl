// DEV ONLY (datamosh round 1). Motion-vector smear with a codec-like residual, written for tdlib.
// A P-frame decoder predicts each pixel from the previous decoded picture moved by the motion
// field, then adds the residual the encoder computed against ITS previous picture. While the
// two pictures agree the output is the input exactly; after a cut whose keyframe was dropped
// they don't, and the new clip's motion and residual keep pushing the old picture around.
// Inputs: 0 previous output (Feedback TOP), 1 input, 2 previous input, 3 flow (UV, current(x)
// = previous(x - v)), 4 1x1 cut measure (mean abs luma change).
uniform vec4 uA;   // x: refresh toward the input per frame, y: motion gain, z: cut threshold, w: bicubic
uniform vec4 uB;   // x: luma residual gain, y: chroma residual gain, z: luma refresh per frame
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec4 ic = texture(sTD2DInputs[1], uv);
    vec4 hold = texture(sTD2DInputs[0], uv);
    float cut = step(uA.z, texture(sTD2DInputs[4], vec2(0.5)).r);
    vec2 v = texture(sTD2DInputs[3], uv).rg * uA.y;
    vec4 sp, ip;
    if (uA.w > 0.5) { sp = sampleCR(0, uv - v); ip = sampleCR(2, uv - v); }
    else { sp = texture(sTD2DInputs[0], uv - v); ip = texture(sTD2DInputs[2], uv - v); }
    vec3 r = ic.rgb - ip.rgb;
    // Y-only change = equal change in R, G and B (luma weights sum to 1).
    vec3 s = sp.rgb + uB.y * r + (uB.x - uB.y) * luma(r);
    s += (luma(ic.rgb) - luma(s)) * uB.z;
    s = mix(s, hold.rgb, cut);                 // the cut frame is the dropped keyframe: show nothing new
    s = mix(s, ic.rgb, uA.x);
    fragColor = vec4(clamp(s, 0.0, 1.0), 1.0);
}
