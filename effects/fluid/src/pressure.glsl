// Fluid (touchdesigner-effects, MIT): the pressure that cancels the divergence, by Jacobi iteration
// of its Poisson equation (Harris 2004, GPU Gems ch. 38). The GLSL TOP runs this shader Passes times
// a frame, each pass reading the last one's result as input 0 (2025.33230, dev/probes/glsl_passes.py);
// the first pass starts from last frame's pressure, which is close, so a few dozen passes do. Off the
// frame's edges the pressure reads 0 (Input Extend Mode Zero): the fluid flows out freely.
// Inputs: 0 the pressure so far (last frame's on the first pass), 1 the divergence. Out: r the pressure.
out vec4 fragColor;
float p(vec2 q) { return texture(sTD2DInputs[0], q).r; }
void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st;
    float sum = p(uv + vec2(px.x, 0.0)) + p(uv - vec2(px.x, 0.0)) + p(uv + vec2(0.0, px.y)) + p(uv - vec2(0.0, px.y));
    fragColor = vec4(0.25 * (sum - texture(sTD2DInputs[1], uv).r), 0.0, 0.0, 1.0);
}
