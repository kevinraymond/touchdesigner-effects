// Frost (touchdesigner-effects, MIT): one step of the Fern style's ice, R. Kobayashi's phase field of a growing
// crystal ("Modeling and numerical simulations of dendritic crystal growth", Physica D 63, 1993). A phase p goes
// from 0 (the air at the glass) to 1 (ice) across a thin interface whose energy depends on which way it faces,
//     eps(theta) = eps_bar (1 + delta cos(6 (theta - theta0))),   theta the direction of grad p,
// six-fold for ice, and freezing gives off latent heat that raises the temperature T:
//     tau dp/dt = div(eps^2 grad p) - d/dx(eps eps' dp/dy) + d/dy(eps eps' dp/dx) + p (1 - p) (p - 1/2 + m),
//     m = (alpha / pi) atan(gamma (1 - T)),   1 the melting point (below it, ice grows),
//     dT/dt = lap T + K dp/dt.
// The heat a growing arm sheds slows the cells beside it, so arms run out ahead and branch: dendrites. His
// constants (eps_bar 0.01, tau 3e-4, alpha 0.9, gamma 10), with a grid step of 0.0625 (his was 0.03: thinner arms for
// the cells; the model step keeps his step over the grid step squared) and K, delta for fern-like arms. Steered as
// T. Kim and M. C. Lin steered it for artists ("Visual Simulation of Ice Crystal Growth", SCA 2003): theta0 follows
// the picture's edges where they are clear, so arms run along them. Here the glass also draws the heat out toward its
// own temperature, colder than the melting point where the room is far or dark, and drawn out weakly, so the arms'
// own heat keeps them dendritic (drawn out fast, the ice grew in compact sheets: dev/protos/frost/offline.py). Where
// something warms the glass the ice melts outright and its interface tips toward melting, which leaves the
// temperature alone, so the frost grows back as soon as the warmth has gone. A little noise at the interface,
// Kobayashi's a p (1 - p) (chi - 1/2), sets off side branches. Derivatives are central differences, the Laplacians
// 9-point (less pull toward the grid's own four directions), and cells off the frame read as the frame's edge.
// Inputs: 0 the ice (seed.glsl's, then each pass the last one's: r p, g T, b seconds frozen), 1 the pane (pane.glsl:
// r cold, g warm), 2 the flow (lib tensor_flow.glsl: rg along the edges, a unit vector; b how clear, 0-1). All the
// grid's size.
// Out: r p, g T, b kept, a 1.
uniform vec4 uM;   // x eps_bar, y delta, z K, w dt / tau
uniform vec4 uS;   // x dt (model time a step), y 1 / dx, z alpha / pi, w gamma
uniform vec4 uP;   // x the glass's pull on T (per model time), y the undercooling where coldest, w melting where warm
                   // (per model time)
uniform vec4 uT;   // x how far warmth tips the interface toward melting, y the noise, z Follow Edges, w the clock
out vec4 fragColor;

ivec2 top;
vec2 at(ivec2 q) { return texelFetch(sTD2DInputs[0], clamp(q, ivec2(0), top), 0).rg; }

// eps and eps eps' for an interface facing g (where there is no interface, its direction doesn't matter).
vec2 aniso(vec2 g, float th0) {
    if (dot(g, g) < 1e-12) return vec2(uM.x, 0.0);
    float th = 6.0 * (atan(g.y, g.x) - th0);
    float e = uM.x * (1.0 + uM.y * cos(th));
    return vec2(e, e * (-6.0 * uM.x * uM.y * sin(th)));
}

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    top = textureSize(sTD2DInputs[0], 0) - 1;
    vec4 s = texelFetch(sTD2DInputs[0], c, 0);
    vec2 C = s.rg;
    vec2 E = at(c + ivec2(1, 0)), W = at(c - ivec2(1, 0)), N = at(c + ivec2(0, 1)), S = at(c - ivec2(0, 1));
    vec2 NE = at(c + ivec2(1, 1)), NW = at(c + ivec2(-1, 1)), SE = at(c + ivec2(1, -1)), SW = at(c + ivec2(-1, -1));
    float EE = at(c + ivec2(2, 0)).r, WW = at(c - ivec2(2, 0)).r;
    float NN = at(c + ivec2(0, 2)).r, SS = at(c - ivec2(0, 2)).r;
    float h = 0.5 * uS.y;
    // grad p at the cell and at its four neighbors
    vec2 gC = h * vec2(E.r - W.r, N.r - S.r);
    vec2 gE = h * vec2(EE - C.r, NE.r - SE.r), gW = h * vec2(C.r - WW, NW.r - SW.r);
    vec2 gN = h * vec2(NE.r - NW.r, NN - C.r), gS = h * vec2(SE.r - SW.r, C.r - SS);
    // The arms' direction: the picture's edges where clear (a line has no sign, and an angle plus any multiple of 60
    // degrees is the same six arms), one way elsewhere.
    vec4 f = texelFetch(sTD2DInputs[2], c, 0);
    float th0 = uT.z * smoothstep(0.1, 0.4, f.b) * atan(f.g, f.r);
    vec2 aC = aniso(gC, th0), aE = aniso(gE, th0), aW = aniso(gW, th0), aN = aniso(gN, th0), aS = aniso(gS, th0);
    float i2 = uS.y * uS.y;
    vec2 lap = ((E + W + N + S) * 0.5 + (NE + NW + SE + SW) * 0.25 - 3.0 * C) * i2;
    // div(eps^2 grad p) = eps^2 lap p + grad(eps^2) . grad p, and the cross terms
    vec2 ge2 = h * vec2(aE.x * aE.x - aW.x * aW.x, aN.x * aN.x - aS.x * aS.x);
    float skew = h * ((aN.y * gN.x - aS.y * gS.x) - (aE.y * gE.y - aW.y * gW.y));
    vec2 pane = texelFetch(sTD2DInputs[1], c, 0).rg;
    float glass = 1.0 - uP.y * pane.r;
    float m = uS.z * atan(uS.w * (1.0 - C.g)) - uT.x * pane.g;
    uint salt = ihash(floatBitsToUint(uT.w) + uint(uTDPass));
    float chi = float(ihash(uint(c.x) + 8192u * uint(c.y) + salt)) / 4294967295.0 - 0.5;
    float p = C.r;
    float dp = uM.w * (aC.x * aC.x * lap.r + dot(ge2, gC) + skew + p * (1.0 - p) * (p - 0.5 + m + 2.0 * uT.y * chi))
             - uP.w * uS.x * pane.g * p;
    float T = C.g + uS.x * lap.g + uM.z * dp + uP.x * uS.x * (glass - C.g);
    fragColor = vec4(clamp(p + dp, 0.0, 1.0), T, s.b, 1.0);
}
