// DEV ONLY (datamosh round 1). Macroblock codec model, written for tdlib. Two chains run side by
// side: the ENCODER's reconstruction (mode 0) and the DECODER's picture (mode 1). Both predict a
// block from their previous picture moved by the block's quarter-pel motion vector and add the
// same quantized residual (input minus the encoder's prediction), so they agree until the
// decoder misses a keyframe: at a cut the encoder writes an I-frame and the decoder drops it,
// and from then on the new clip's vectors and residuals land on the old picture.
// Inputs: 0 previous picture of this chain (Feedback TOP), 1 input, 2 previous encoder picture,
// 3 block vectors (one pixel per block, UV), 4 1x1 cut measure, 5 (decoder only) the encoder's
// picture this frame: wiring it in is also what makes the encoder cook.
uniform vec4 uA;   // x: quant step, y: motion gain, z: cut threshold, w: residual gain (decoder)
uniform vec4 uB;   // x: frozen block fraction, y: intra block fraction, z: time slot, w: keyframe sweep (-1 off)
uniform vec4 uC;   // x: per-frame chance a block recovers, y: block px, z: frame seed, w: mode (0 enc, 1 dec)
uniform vec4 uD;   // x: keyframe now (1: encoder I-frame, decoder takes it), y: per-frame fade to the encoder's picture
out vec4 fragColor;
vec3 quant(vec3 r, float q) {
    return sign(r) * max(vec3(0.0), floor(abs(r) / q + 0.3)) * q;
}
void main() {
    vec2 uv = vUV.st;
    ivec2 P = ivec2(gl_FragCoord.xy);
    ivec2 B = P / int(uC.y);
    vec2 nb = ceil(uTD2DInfos[1].res.zw / uC.y);
    vec2 v = texelFetch(sTD2DInputs[3], B, 0).rg * uA.y;
    vec3 ic = texture(sTD2DInputs[1], uv).rgb;
    float cut = step(uA.z, texture(sTD2DInputs[4], vec2(0.5)).r);
    // The encoder's picture this frame (both chains compute it the same way).
    vec3 pe = texture(sTD2DInputs[2], uv - v).rgb;
    vec3 r = quant(ic - pe, uA.x);
    if (uC.w < 0.5) {
        vec3 e = (cut > 0.5 || uD.x > 0.5) ? ic : pe + r;
        fragColor = vec4(clamp(e, 0.0, 1.0), 1.0);
        return;
    }
    vec3 enc = texelFetch(sTD2DInputs[5], P, 0).rgb;

    vec3 own = texelFetch(sTD2DInputs[0], P, 0).rgb;
    vec3 s;
    float hf = hash12(vec2(B) + uB.z * 17.13);
    if (cut > 0.5 || hf < uB.x) s = own;                       // dropped I-frame / frozen block
    else s = texture(sTD2DInputs[0], uv - v).rgb + uA.w * r;
    if (hash12(vec2(B) * 1.7 + uB.z * 3.1 + 5.0) < uB.y) s = enc;        // intra block
    float col = (float(B.x) + 0.5) / nb.x;
    // Keyframe sweep: every column behind the sweep takes the encoder's picture until it ends,
    // or vectors pointing into columns not yet swept would carry the mosh back.
    if (uB.w >= 0.0 && col <= uB.w) s = enc;
    if (hash12(vec2(B) * 2.3 + uC.z * 0.618) < uC.x) s = enc;           // block recovers
    s = mix(s, enc, uD.y);                                               // or the whole picture fades back
    fragColor = vec4(clamp(s, 0.0, 1.0), 1.0);
}
