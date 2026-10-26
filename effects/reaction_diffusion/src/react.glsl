// Reaction-Diffusion (touchdesigner-effects, MIT): one step of the Gray-Scott model, as J. E. Pearson studied it
// ("Complex Patterns in a Simple System", Science 1993), with its diffusion steered along the picture's edges, as
// A. Witkin and M. Kass steered theirs ("Reaction-Diffusion Textures", SIGGRAPH 1991). Two chemicals: U feeds V,
// and V turns U into more V:
//     dU/dt = Du lap(U) - U V^2 + F (1 - U)
//     dV/dt = Dv lap(V) + U V^2 - (F + k) V
// F feeds U in, k kills V off. Where the picture has a clear direction (the flow, lib tensor_flow.glsl), the
// diffusion runs stretch times faster along it and stretch times slower across it, which keeps the stripes'
// spacing and stretches them along the edges: stripes run along contours instead of every way. Each second
// difference is taken along a unit step, read bilinearly from the 3 x 3 neighborhood, so every neighbor's weight
// is positive and the step stays stable at any angle (with dt Du 4 (stretch + 1/stretch) below 2).
// A direction counts only where the picture changes enough to have one: on a dark stage the noise points every
// way, and a stretch along it only spreads the pattern thin.
// Inputs: 0 the state (r U, g V, b k, a F; each pass reads the last one's, the first reads seed's),
// 1 the flow at the same size (rg along the edges, a unit vector in cells; b how clear it is, 0-1; a how strongly
// the picture changes there, squared).
// Out: the state a step later, b and a kept.
uniform vec4 uR;   // x Du, y Dv, z the step dt, w ln(stretch) at Follow Edges (0: the same every way)
uniform vec4 uA;   // x the clarity (anisotropy) at which the stretch is full; yz the change (squared) from
                   // which a direction starts to count, and from which it counts fully
out vec4 fragColor;

vec2 n[9];         // the 3 x 3 neighborhood's U and V, n[(x + 1) + 3 (y + 1)]

// U and V a step d away (|d.x|, |d.y| <= 1), bilinear between the four cells around it.
vec2 at(vec2 d) {
    ivec2 o = ivec2(sign(d));
    vec2 a = abs(d);
    return mix(mix(n[4], n[4 + o.x], a.x), mix(n[4 + 3 * o.y], n[4 + o.x + 3 * o.y], a.x), a.y);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 last = textureSize(sTD2DInputs[0], 0) - 1;
    // Cells off the edge read as the edge: nothing diffuses out of the frame.
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            n[(x + 1) + 3 * (y + 1)] = texelFetch(sTD2DInputs[0], clamp(p + ivec2(x, y), ivec2(0), last), 0).rg;
    vec4 s = texelFetch(sTD2DInputs[0], p, 0);
    vec4 f = texelFetch(sTD2DInputs[1], p, 0);
    float stretch = exp(uR.w * clamp(f.b / uA.x, 0.0, 1.0) * smoothstep(uA.y, uA.z, f.a));
    vec2 t = f.rg, c = n[4];
    vec2 lap = stretch * (at(t) + at(-t) - 2.0 * c) + (at(vec2(-t.y, t.x)) + at(vec2(t.y, -t.x)) - 2.0 * c) / stretch;
    float U = c.x, V = c.y, k = s.b, F = s.a;
    float uvv = U * V * V;
    U += uR.z * (uR.x * lap.x - uvv + F * (1.0 - U));
    V += uR.z * (uR.y * lap.y + uvv - (F + k) * V);
    fragColor = vec4(clamp(U, 0.0, 1.0), clamp(V, 0.0, 1.0), k, F);
}
