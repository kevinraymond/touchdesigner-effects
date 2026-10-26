// touchdesigner-effects (MIT), shared by the effects that follow the picture's edges (lib/glsl,
// structure_tensor(ease=...)): the smoothed structure tensor eased over time, so the direction of the edges
// (tensor_flow.glsl) turns smoothly instead of jittering with the picture's noise and flicker from frame to frame.
// Easing the tensor, not the direction, keeps it right where a direction has no sign: a line's two ends average
// to the line, where their directions would cancel. Each frame moves it 1 - exp(-step / ease) of the way to now.
// Inputs: 0 the smoothed tensor now (r E, g F, b G), 1 this pass last frame (read by UV: any size).
// Out: the tensor, eased.
uniform vec4 uE;   // x the frame step (s), y how long the easing takes (s)
out vec4 fragColor;

void main() {
    vec3 now = texture(sTD2DInputs[0], vUV.st).rgb;
    vec3 last = texture(sTD2DInputs[1], vUV.st).rgb;
    fragColor = vec4(mix(last, now, 1.0 - exp(-uE.x / uE.y)), 1.0);
}
