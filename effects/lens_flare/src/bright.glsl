// touchdesigner-effects (MIT), Lens Flare: each pixel's light past Threshold, at a quarter of the picture's size. A
// pixel counts by how far its brightness is past the threshold (0 at it, 1 at white), squared, so what is near white
// (a lamp, the sun, a headlight) counts far more than a bright wall; that times its color in linear light. Four
// bilinear reads average the 4 x 4 pixels under each, so a small light isn't missed.
// Input: 0 the picture.
// Out: rgb its color times its weight, a its weight.
uniform vec4 uBright;   // x Threshold

out vec4 fragColor;
void main() {
    vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[0], 0));
    vec4 sum = vec4(0.0);
    for (int i = 0; i < 4; i++) {
        vec2 o = vec2((i & 1) == 0 ? -1.0 : 1.0, (i & 2) == 0 ? -1.0 : 1.0) * px;
        vec3 c = texture(sTD2DInputs[0], vUV.st + o).rgb;
        float y = dot(c, vec3(0.2126, 0.7152, 0.0722));
        float e = max(y - uBright.x, 0.0) / max(1.0 - uBright.x, 0.001);
        e *= e;
        sum += vec4(srgb_to_linear(c) * e, e);
    }
    fragColor = TDOutputSwizzle(sum * 0.25);
}
