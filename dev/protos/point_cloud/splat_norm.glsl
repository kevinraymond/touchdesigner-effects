// Point cloud prototype. The splats' added colors divided by their added weights: each pixel the
// weighted average of the splats over it (Botsch, Hornung, Zwicker, Kobbelt 2005).
// Inputs: 0 the splat pass (rgb color x weight, a weight).
out vec4 fragColor;

void main() {
    vec4 c = texture(sTD2DInputs[0], vUV.st);
    fragColor = c.a > 0.001 ? vec4(c.rgb / c.a, 1.0) : vec4(0.0, 0.0, 0.0, 1.0);
}
