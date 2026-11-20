// Photoelastic (touchdesigner-effects, MIT): the stress in the warmed plastic. Its deviatoric part, the part that
// makes plastic birefringent, is psi's Hessian less its trace (Goodier 1937): a = (psi_xx - psi_yy) / 2 and
// b = psi_xy. Scale-free: a warm disc gives the same stress at its rim whatever its size. Inside a warm patch the
// stress is even and shows nothing; it gathers at the patch's outline and falls away as 1 / r^2 outside it.
// Inputs: 0 psi (solve.glsl, the finest level). Out: r a, g b.
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 o = uTD2DInfos[0].res.xy;
    float c = texture(sTD2DInputs[0], uv).r;
    float xp = texture(sTD2DInputs[0], uv + vec2(o.x, 0.0)).r, xm = texture(sTD2DInputs[0], uv - vec2(o.x, 0.0)).r;
    float yp = texture(sTD2DInputs[0], uv + vec2(0.0, o.y)).r, ym = texture(sTD2DInputs[0], uv - vec2(0.0, o.y)).r;
    float xy = texture(sTD2DInputs[0], uv + o).r + texture(sTD2DInputs[0], uv - o).r
             - texture(sTD2DInputs[0], uv + vec2(o.x, -o.y)).r - texture(sTD2DInputs[0], uv + vec2(-o.x, o.y)).r;
    fragColor = vec4(0.5 * ((xp + xm) - (yp + ym)), 0.25 * xy, 0.0, 1.0);
}
