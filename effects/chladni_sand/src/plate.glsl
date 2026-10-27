// touchdesigner-effects (MIT), Chladni Sand: the plate. A square plate as tall as the picture, centered (its figure runs
// on past its sides, where the cosines carry on), shaking in seven modes, one for each band of the music, and the flow
// that carries sand on it. Chladni (Entdeckungen ueber die Theorie des Klanges, 1787) strewed sand on a plate and bowed
// it: the sand leaves the parts that shake and gathers on the nodal lines, the parts that keep still. Wheatstone (Phil.
// Trans. R. Soc. 1833) showed that every such figure is the resultant of simple modes, and two perpendicular ones in
// opposite phase give the square plate's figures: phi = cos(n pi x) cos(m pi y) - cos(m pi x) cos(n pi y).
// The plate's shape u is the modes summed by their weights (the bands rising above their usual level), over the root
// of the sum of their weighted peaks squared: exact for one mode, and for several, nearer their sum's real peak than the
// peaks summed, which a sum of modes rarely reaches (the flow, going as u^2, came out ten times too slow that way). Sand drifts away from where the plate shakes most: its flow is -grad(u^2), which is 0 on
// the nodal lines and points at them from both sides, scaled so every mode carries sand about as fast (the steepest
// slope of u^2 is about 0.78 pi m for each mode, dev/protos/chladni). Its divergence, which says where sand gathers
// (below 0) and where it drains (above), is exact: each mode is an eigenfunction of the Laplacian, with eigenvalue
// -(n^2 + m^2) pi^2, so the divergence -2K (|grad u|^2 + u lap u) needs no neighbors read.
// Inputs: 0 the picture (for this pass's size, a quarter of it), 1 nearness (lib depth_near.glsl: r 0 far to 1 near).
// Out: rg the flow, in UV a second; b its divergence, a second; a |u| (the figure's lines are where it is 0).
uniform vec4 uW0;   // the weights of modes 0-3 (sub bass to mid)
uniform vec4 uW1;   // xyz the weights of modes 4-6 (upper mid to brilliance), w how hard the plate shakes (0 to 1.5)
uniform vec4 uP;    // x the sand's speed at 1, in picture heights a second; y Depth Focus (0 without input 3)
out vec4 fragColor;

const float PI = 3.14159265;
const ivec2 MODE[7] = ivec2[](ivec2(1, 3), ivec2(2, 4), ivec2(2, 5), ivec2(3, 6), ivec2(3, 7), ivec2(4, 8), ivec2(5, 8));
const float PEAK[7] = float[](1.54, 2.0, 2.0, 2.0, 1.92, 2.0, 2.0);   // each mode's largest |phi|

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = vec2((vUV.x - 0.5) * res.x / res.y + 0.5, vUV.y);   // on the plate: 1 is the picture's height
    float w[7] = float[](uW0.x, uW0.y, uW0.z, uW0.w, uW1.x, uW1.y, uW1.z);
    float u = 0.0, lap = 0.0, peak = 1e-6, sum = 1e-6, lines = 0.0;
    vec2 g = vec2(0.0);
    for (int k = 0; k < 7; k++) {
        float a = PI * float(MODE[k].x), b = PI * float(MODE[k].y);
        float cxa = cos(a * p.x), sxa = sin(a * p.x), cxb = cos(b * p.x), sxb = sin(b * p.x);
        float cya = cos(a * p.y), sya = sin(a * p.y), cyb = cos(b * p.y), syb = sin(b * p.y);
        float phi = cxa * cyb - cxb * cya;
        u += w[k] * phi;
        g += w[k] * vec2(-a * sxa * cyb + b * sxb * cya, -b * cxa * syb + a * cxb * sya);
        lap -= w[k] * (a * a + b * b) * phi;
        peak += w[k] * w[k] * PEAK[k] * PEAK[k];
        sum += w[k];
        lines += w[k] * float(MODE[k].y);
    }
    peak = sqrt(peak);
    u /= peak;
    g /= peak;
    lap /= peak;
    float near = texture(sTD2DInputs[1], vUV.st).r;
    float k = uP.x * uW1.w * mix(1.0, near, uP.y) / (0.78 * PI * max(lines / sum, 1.0));
    vec2 flow = -2.0 * k * u * g;                       // picture heights a second
    float div = -2.0 * k * (dot(g, g) + u * lap);
    fragColor = vec4(flow.x * res.y / res.x, flow.y, div, abs(u));
}
