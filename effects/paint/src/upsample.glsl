// touchdesigner-effects (MIT), Paint: the painting, made at half size (kuwahara.glsl costs a quarter there), brought
// back to the picture's size by joint bilateral upsampling (Kopf, Cohen, Lischinski and Uyttendaele, "Joint Bilateral
// Upsampling", SIGGRAPH 2007): each pixel takes the 4 x 4 half-size painted pixels around it, weighted by distance
// and by how alike the picture is at the pixel and at each of them, so a stroke ends where the picture's edge is,
// not up to a half-size pixel away from it.
// Inputs: 0 the picture (its mipmap level 1 is the picture at half size), 1 the painting at half size.
uniform vec4 uU;   // x: range sigma (color distance, 0-1 units), y: spatial sigma in half-size pixels
out vec4 fragColor;

void main() {
    vec2 lo = uTD2DInfos[1].res.zw;
    vec3 here = texture(sTD2DInputs[0], vUV.st).rgb;
    vec2 p = vUV.st * lo - 0.5;
    vec2 base = floor(p);
    vec3 acc = vec3(0.0);
    float wsum = 0.0;
    for (int j = -1; j <= 2; j++)
    for (int i = -1; i <= 2; i++) {
        vec2 q = base + vec2(float(i), float(j));
        vec2 quv = (q + 0.5) / lo;
        vec3 there = textureLod(sTD2DInputs[0], quv, 1.0).rgb;
        vec3 d = here - there;
        vec2 o = q - p;
        float w = exp(-0.5 * dot(o, o) / (uU.y * uU.y) - 0.5 * dot(d, d) / (uU.x * uU.x));
        acc += w * texture(sTD2DInputs[1], quv).rgb;
        wsum += w;
    }
    fragColor = vec4(wsum > 1e-6 ? acc / wsum : texture(sTD2DInputs[1], vUV.st).rgb, 1.0);
}
