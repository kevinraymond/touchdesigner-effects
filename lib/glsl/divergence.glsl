// touchdesigner-effects (MIT), shared by the effects that run a fluid (lib/glsl, incompressible()): Fluid. How much
// fluid each cell gains or loses (the divergence of the velocity), which the pressure solve then cancels so the fluid
// neither piles up nor thins out (Harris 2004, GPU Gems ch. 38).
// Inputs: 0 the velocity before projection (cells per second). Out: r the divergence (per second).
out vec4 fragColor;
vec2 vel(vec2 p) { return texture(sTD2DInputs[0], p).rg; }
void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    float div = 0.5 * (vel(uv + vec2(px.x, 0.0)).x - vel(uv - vec2(px.x, 0.0)).x
                     + vel(uv + vec2(0.0, px.y)).y - vel(uv - vec2(0.0, px.y)).y);
    fragColor = vec4(div, 0.0, 0.0, 1.0);
}
