// Datamosh-style (touchdesigner-effects, MIT): the motion the decoder applies, at a quarter of
// the input's size, in UV units with current(x) = previous(x - v). Smear smooths the optical flow
// (5 x 5, weighted by how textured each place is, so flat areas borrow from their neighbors),
// zeroes sub-pixel jitter and blends it with the last field; Blocks takes the block vectors as
// they are. Only a new input frame updates it: a cut, Hold or a skipped keyframe keeps the last
// field, which the decoder then applies again and again (the "bloom" mosh).
// Inputs: 0 new motion (Smear: rg flow, b confidence; Blocks: rg block vectors), 1 the previous
// field (Feedback TOP), 2 the decoder's clock (1 x 1: r new frame, g cut). Out: rg the field,
// a the Mode it was made in, plus 1: on the first frame after a Mode change the newly used
// estimate compares against a stale frame, so the field holds for that frame.
uniform vec4 uM;   // x: Mode (0 Smear, 1 Blocks), y: Hold, z: skip envelope, w: dead zone (px)
uniform vec4 uM2;  // x: blend of the new flow per frame
out vec4 fragColor;
void main() {
    vec2 uv = vUV.st;
    vec4 st = texelFetch(sTD2DInputs[2], ivec2(0), 0);
    vec4 prev = texture(sTD2DInputs[1], uv);
    float mode = uM.x + 1.0;
    bool switched = abs(prev.a - mode) > 0.5;
    if (st.r < 0.5 || st.g > 0.5 || uM.y > 0.5 || uM.z > 0.01 || switched) { fragColor = vec4(prev.rg, 0.0, mode); return; }
    if (uM.x > 0.5) { fragColor = vec4(texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0).rg, 0.0, mode); return; }
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 acc = vec2(0.0);
    float wsum = 0.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec4 f = texture(sTD2DInputs[0], uv + vec2(float(i), float(j)) * px);
        float w = (f.b + 1e-5) * exp(-float(i * i + j * j) / 4.0);
        acc += w * f.rg;
        wsum += w;
    }
    vec2 f = acc / wsum;
    f *= smoothstep(uM.w, 2.0 * uM.w, length(f * uTD2DInfos[0].res.zw * 4.0));   // in input pixels: the field is 1/4 size
    fragColor = vec4(mix(prev.rg, f, uM2.x), 0.0, mode);
}
