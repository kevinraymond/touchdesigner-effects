// touchdesigner-effects (MIT), Pixel Art: the picture in L*a*b*, and how much each pixel counts toward the palette.
// Gerstner et al. let an importance map weigh the palette toward what matters (their section 4.5): here input 3's
// nearness (or mask) mixed in by Subject Colors, 1 everywhere with nothing on input 3. Never quite 0, so far things
// still get the nearest of the colors the near ones chose.
// Inputs: 0 the picture, 1 nearness (lib depth_near.glsl, a quarter size).
// Out: rgb L*a*b*, a the pixel's importance 0.02-1.
uniform vec4 uImp;   // x Subject Colors (0 with nothing on input 3)
out vec4 fragColor;

void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    float near = texture(sTD2DInputs[1], vUV.st).r;
    fragColor = vec4(rgb_to_lab(c), max(mix(1.0, near, uImp.x), 0.02));
}
