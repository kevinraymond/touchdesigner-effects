// Fluid (touchdesigner-effects, MIT): the velocity made incompressible: minus the pressure's gradient
// (the projection of Stam 1999; Harris 2004, GPU Gems ch. 38). This is the velocity the dye moves with
// and the next frame starts from.
// Inputs: 0 the velocity before projection, 1 the pressure. Out: rg the velocity (cells per second).
out vec4 fragColor;
float p(vec2 q) { return texture(sTD2DInputs[1], q).r; }
void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    vec2 grad = 0.5 * vec2(p(uv + vec2(px.x, 0.0)) - p(uv - vec2(px.x, 0.0)),
                           p(uv + vec2(0.0, px.y)) - p(uv - vec2(0.0, px.y)));
    fragColor = vec4(texture(sTD2DInputs[0], uv).rg - grad, 0.0, 1.0);
}
