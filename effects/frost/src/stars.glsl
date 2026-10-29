// Frost (touchdesigner-effects, MIT): one half-step of the Stars style's ice, C. A. Reiter's local cellular model of
// a snow crystal ("A local cellular model for snow crystal growth", Chaos, Solitons and Fractals 23, 2005). Cells on a
// hexagonal lattice hold s, ice where s is 1 or more and water vapor below. A cell is receptive when it or one of its
// six neighbors is ice. Each step, receptive cells keep what they hold and gain a little more (gamma), and the vapor
// in the others diffuses: half of it is averaged with its six neighbors' (receptive neighbors count as holding none,
// which is how ice draws the vapor toward it). With his beta 0.4 and gamma 1e-4 the crystals grow as six needle-like
// arms with side branches. Here the glass also condenses vapor where it is cold (relaxing the vapor toward beta, a
// little each step), none where it is warm, where ice melts too.
// Passes alternate: even passes mark which cells are receptive (g), odd passes take the step. Texel (i, j) is the cell
// whose middle lies at ((i + (j odd ? 0.5 : 0)) HEX + 0.5, j + 0.5) on the grid (seed.glsl), HEX = 2 / sqrt(3): its
// neighbors are the two beside it in its row and two in each row above and below, those at i - 1 and i in an even
// row, i and i + 1 in an odd one. Cells off the lattice read as its edge.
// Inputs: 0 the ice (seed.glsl's, then each pass the last one's: r s, g receptive, b seconds frozen), 1 the pane
// (pane.glsl: r cold, g warm), both the grid's size.
// Out: r s, g receptive (even passes) or 0, b kept, a 1.
uniform vec4 uR;   // x gamma, y beta (the vapor the glass holds where coldest), z how fast the glass condenses it
                   // (a share a step), w melting where warm (a step)
out vec4 fragColor;

#define HEX 1.1547005
ivec2 top;
vec4 at(ivec2 q) { return texelFetch(sTD2DInputs[0], clamp(q, ivec2(0), top), 0); }

void neighbors(ivec2 c, out ivec2 n[6]) {
    int o = c.y & 1;   // odd rows sit half a cell right
    n[0] = c + ivec2(-1, 0);
    n[1] = c + ivec2(1, 0);
    n[2] = c + ivec2(o - 1, -1);
    n[3] = c + ivec2(o, -1);
    n[4] = c + ivec2(o - 1, 1);
    n[5] = c + ivec2(o, 1);
}

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    top = textureSize(sTD2DInputs[0], 0) - 1;
    vec4 s = texelFetch(sTD2DInputs[0], c, 0);
    ivec2 n[6];
    neighbors(c, n);
    if ((uTDPass & 1) == 0) {
        bool rec = s.r >= 1.0;
        for (int k = 0; k < 6; k++) rec = rec || at(n[k]).r >= 1.0;
        fragColor = vec4(s.r, rec ? 1.0 : 0.0, s.b, 1.0);
        return;
    }
    vec2 size = vec2(top + 1);
    vec2 uv = (vec2((float(c.x) + ((c.y & 1) == 1 ? 0.5 : 0.0)) * HEX, float(c.y)) + 0.5) / size;
    vec2 pane = texture(sTD2DInputs[1], uv).rg;
    bool rec = s.g > 0.5;
    float u = rec ? 0.0 : s.r;
    float v = rec ? s.r + uR.x * (1.0 - pane.g) : 0.0;
    float sum = 0.0;
    for (int k = 0; k < 6; k++) {
        vec4 q = at(n[k]);
        sum += q.g > 0.5 ? 0.0 : q.r;
    }
    u += 0.5 * (sum / 6.0 - u);
    if (!rec) u += uR.z * (uR.y * pane.r * (1.0 - pane.g) - u);
    else v = max(v - uR.w * pane.g, 0.0);
    fragColor = vec4(u + v, 0.0, s.b, 1.0);
}
