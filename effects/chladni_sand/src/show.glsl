// touchdesigner-effects (MIT), Chladni Sand: the sand as it is seen. Where the sand lies as it did (mass near 1 all
// around), the live picture, so nothing that moves in it trails behind; where it has piled up or drained nearby, the
// colors it carried, lit by how much of it lies there: piled on a line up to twice as bright, and drained from between
// the lines down toward black, eased as 2m / (1 + m) so a line never blows out to white. Whether it moved is judged
// over a few taps about 1% of the picture's height apart, since between a drained cell and its piled rim the mass
// passes through 1, and judged at the pixel alone that let a thin outline of the live picture through around every cell.
// Inputs: 0 the picture, 1 the sand (sand.glsl: rgb colors, a mass).
// Out: the picture.
out vec4 fragColor;

float off(vec2 uv) {
    float a = texture(sTD2DInputs[1], uv).a;
    return a > 0.0 ? abs(a - 1.0) : 0.0;
}

void main() {
    vec2 uv = vUV.st;
    vec4 pic = texture(sTD2DInputs[0], uv);
    vec4 sand = texture(sTD2DInputs[1], uv);
    float m = sand.a > 0.0 ? sand.a : 1.0;
    vec2 r = vec2(uTD2DInfos[1].res.w / uTD2DInfos[1].res.z, 1.0) * 0.012;
    float far = max(max(off(uv), max(off(uv + vec2(r.x, 0.0)), off(uv - vec2(r.x, 0.0)))),
                    max(off(uv + vec2(0.0, r.y)), off(uv - vec2(0.0, r.y))));
    float moved = smoothstep(0.0, 0.25, far);
    fragColor = vec4(clamp(mix(pic.rgb, sand.rgb, moved) * 2.0 * m / (1.0 + m), 0.0, 1.0), pic.a);
}
