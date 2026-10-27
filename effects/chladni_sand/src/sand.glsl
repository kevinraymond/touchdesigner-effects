// touchdesigner-effects (MIT), Chladni Sand: the sand. The picture's light, carried along the plate's flow (plate.glsl)
// as sand is carried on a shaking plate: each pixel takes what was a step upstream last frame (semi-Lagrangian, as
// J. Stam's "Stable Fluids", SIGGRAPH 1999, carries a fluid; Fluid does the same), its colors as they were and its mass
// changed by how much the flow gathers or spreads there (by exp(-divergence x step), so what drains from one place
// gathers on the lines). Both settle back to the live picture over Settle seconds, so between strikes the picture comes
// back and the figure clears. A Feedback TOP's first frame is black with alpha 0, and mass never goes below 0.05, so
// alpha 0 means there is no sand yet: the picture as it is.
// Inputs: 0 the picture, 1 this pass's last frame, 2 the plate (rg flow in UV a second, b divergence a second).
// Out: rgb the colors the sand carries, a its mass (1 at rest, up to 8 piled on a line).
uniform vec4 uS;   // x the step, seconds; y Settle, seconds
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec4 pic = texture(sTD2DInputs[0], uv);
    if (texture(sTD2DInputs[1], uv).a <= 0.0) {
        fragColor = vec4(pic.rgb, 1.0);
        return;
    }
    vec4 plate = texture(sTD2DInputs[2], uv);
    vec4 last = texture(sTD2DInputs[1], uv - plate.rg * uS.x);
    float mass = last.a * exp(clamp(-plate.b * uS.x, -0.5, 0.5));
    float settle = 1.0 - exp(-uS.x / max(uS.y, 0.01));
    fragColor = vec4(mix(last.rgb, pic.rgb, settle), clamp(mix(mass, 1.0, settle), 0.05, 8.0));
}
