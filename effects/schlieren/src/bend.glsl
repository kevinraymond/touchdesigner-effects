// Schlieren (touchdesigner-effects, MIT): how the warm air bends the light through it. Air's refractive index falls
// as it warms, n = n0 - k T, so light crossing warm air bends away from it, by an angle that goes with the index's
// gradient across the ray (G. S. Settles, "Schlieren and Shadowgraph Techniques", Springer 2001, ch. 2). The heat here
// stands for the warm air summed along the ray, so the deflection is minus its gradient, and its Laplacian is what a
// shadowgraph sees: light gathering where the deflection converges and leaving where it spreads.
// Inputs: 0 the heat (heat.glsl: r 0-1; sets the size).
// Out: rg the deflection (per frame height, 1 a strong one), b the Laplacian (per frame height squared, scaled to
// about 1 where strong), a the heat.
out vec4 fragColor;

#define DEFLECT 50.0     // the heat's gradient, per frame height, that bends light by 1
#define CURVE 2500.0     // its Laplacian, per frame height squared, that counts as 1

float heat(vec2 p) { return texture(sTD2DInputs[0], p).r; }

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    float h = uTD2DInfos[0].res.w;
    float c = heat(uv), l = heat(uv - vec2(px.x, 0.0)), r = heat(uv + vec2(px.x, 0.0));
    float d = heat(uv - vec2(0.0, px.y)), u = heat(uv + vec2(0.0, px.y));
    vec2 bend = -0.5 * vec2(r - l, u - d) * h / DEFLECT;
    float lap = (l + r + d + u - 4.0 * c) * h * h / CURVE;
    fragColor = vec4(bend, lap, c);
}
