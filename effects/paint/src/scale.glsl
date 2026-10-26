// touchdesigner-effects (MIT), Paint: how big the brush is at each pixel. From input 3's nearness (lib
// depth_near.glsl): finer near (or inside a mask) and broader far (or outside), 2^(Depth Brush (1 - 2 nearness)), so
// halfway (and nothing on input 3) keeps Brush; where a depth camera got no reading the brush keeps its size. Then a
// beat's sweep: a band of broad strokes crossing the picture, straight, from one side to the other, the brush up to
// 1 + uS.z times its size at the band's middle (a Gaussian across it). Each beat comes from another direction.
// Inputs: 0 the picture (only its size: this pass is a quarter of it, whatever input 3's size), 1 nearness (r) and
// how much of the pixel had a reading (g).
// Out: r the brush's scale.
uniform vec4 uD;   // x: Depth Brush 0-1
uniform vec4 uS;   // x: the sweep's progress, 0 (none, or not yet in) to 1 (gone past), y: its direction (radians),
                   // z: how much bigger the brush is in its middle, w: its half-width (picture heights)
out vec4 fragColor;

void main() {
    vec2 nv = texture(sTD2DInputs[1], vUV.st).rg;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    float s = mix(1.0, exp2(uD.x * (1.0 - 2.0 * nv.r)), clamp(nv.g, 0.0, 1.0));
    if (uS.x > 0.0) {
        vec2 dir = vec2(cos(uS.y), sin(uS.y));
        vec2 q = vec2((vUV.s - 0.5) * aspect, vUV.t - 0.5);   // picture heights from the middle
        float extent = 0.5 * (abs(dir.x) * aspect + abs(dir.y)) + 2.0 * uS.w;   // from off one side to off the other
        float d = (dot(q, dir) - mix(-extent, extent, uS.x)) / uS.w;
        s *= 1.0 + uS.z * exp(-d * d);
    }
    fragColor = vec4(s, 0.0, 0.0, 1.0);
}
