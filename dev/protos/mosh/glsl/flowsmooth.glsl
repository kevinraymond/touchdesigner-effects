// DEV ONLY. Smooths the flow: a confidence-weighted 5x5 average (fills flat areas from textured
// neighbors), a dead zone that zeroes sub-threshold jitter, and a running average over frames
// (sample movies are 30 fps in a 60 fps project, so every other frame shows no motion).
// Input 0: previous smoothed flow (Feedback TOP), 1: new flow, 2: 1x1 cut measure.
uniform vec4 uS;   // x: blend of the new flow per frame, y: cut threshold, z: dead zone in output px, w: output width px
out vec4 fragColor;
void main() {
    vec2 px = uTD2DInfos[1].res.xy;
    vec2 acc = vec2(0.0); float wsum = 0.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        vec4 f = texture(sTD2DInputs[1], vUV.st + vec2(float(i), float(j)) * px);
        float w = (f.b + 1e-5) * exp(-float(i * i + j * j) / 4.0);
        acc += w * f.rg; wsum += w;
    }
    vec2 f = acc / wsum;
    float lenpx = length(f * vec2(uS.w, uS.w * uTD2DInfos[1].res.w / uTD2DInfos[1].res.z));
    f *= smoothstep(uS.z, 2.0 * uS.z, lenpx);
    vec2 prev = texture(sTD2DInputs[0], vUV.st).rg;
    float cut = step(uS.y, texture(sTD2DInputs[2], vec2(0.5)).r);
    vec2 o = mix(prev, f, uS.x) * (1.0 - cut);
    fragColor = vec4(o, 0.0, 1.0);
}
