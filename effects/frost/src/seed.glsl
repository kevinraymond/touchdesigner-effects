// Frost (touchdesigner-effects, MIT): the ice where this frame's steps take it up. Last frame's ice, new crystals
// where they start, and how long each cell has been frozen.
//   Fern: r Kobayashi's phase p (0 the air at the glass, 1 ice), g the temperature T, b seconds frozen.
//   Stars: r Reiter's s (ice where 1 or more; below, the water vapor there), g 0 (the step's), b seconds frozen.
// Stars keeps its cells on a hexagonal lattice (stars.glsl): texel (i, j) is the cell whose middle lies at
// ((i + (j odd ? 0.5 : 0)) HEX, j) on the grid, HEX = 2 / sqrt(3), rows a cell apart, so the lattice is regular
// and as tall as the grid (its right sixth runs past the frame and is never seen).
// A crystal starts in a cell with a chance this frame that follows where crystals may start (the pane's b, the
// picture's cold edges), uN.x a second over the frame; along its rims (the outer 2 cells, where cold and not warm)
// uN.y a second; and on a beat, uN.z more at once along the edges. A Fern crystal is the 3 x 3 cells around its
// cell (Kobayashi's grows from a small round seed), a Stars crystal its one cell (Reiter's grows from one), and only
// where the vapor is still most of what the glass holds: Reiter's ice never melts unless warmed, so a crystal started
// in the dry air around a grown one stayed a lone speck (Fern's melt away).
// Inputs: 0 the pane (pane.glsl: r cold, g warm, b where crystals may start; sets the size), 1 the ice last frame
// (Feedback TOP; alpha 0 on the first frame, which starts the pane clear).
// Out: the ice (above), a 1.
uniform vec4 uN;   // x crystals a second on the edges, y along the rims, z crystals on this frame's beat, w the clock
uniform vec4 uI;   // x this frame's step (s), y 0 Fern, 1 Stars, z Fern: the undercooling where coldest,
                   // w Stars: the vapor where coldest (Reiter's beta)
out vec4 fragColor;

#define HEX 1.1547005
#define EDGE_MEAN 0.05     // what the pane's b averages to over a picture with edges: sets the edges' chance

// Where texel c lies on the grid, as a fraction of it.
vec2 place(ivec2 c, vec2 size) {
    vec2 g = uI.y > 0.5 ? vec2((float(c.x) + ((c.y & 1) == 1 ? 0.5 : 0.0)) * HEX, float(c.y)) : vec2(c);
    return (g + 0.5) / size;
}

// Whether a crystal starts in texel c this frame.
bool starts(ivec2 c, vec2 size) {
    vec2 uv = place(c, size);
    if (uv.x > 1.0) return false;
    vec3 pane = texture(sTD2DInputs[0], uv).rgb;
    float cells = size.x * size.y;
    vec2 g = uv * size;
    float rim = (min(g.x, size.x - g.x) < 2.0 || min(g.y, size.y - g.y) < 2.0) ? pane.r * (1.0 - pane.g) : 0.0;
    float chance = (uN.x * uI.x + uN.z) * pane.b / (cells * EDGE_MEAN) + uN.y * uI.x * rim / (4.0 * (size.x + size.y));
    uint frame = floatBitsToUint(uN.w);
    float h = float(ihash(uint(c.x) + 8192u * uint(c.y) + ihash(frame))) / 4294967295.0;
    return h < chance;
}

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    vec2 size = uTDOutputInfo.res.zw;
    vec4 last = texture(sTD2DInputs[1], (vec2(c) + 0.5) / size);   // by UV: a new Size scales the ice
    vec3 pane = texture(sTD2DInputs[0], place(c, size)).rgb;
    bool stars = uI.y > 0.5;
    if (last.a == 0.0) {
        // A clear pane: Fern's air as cold as the glass, Stars' vapor as much as the glass holds.
        last = stars ? vec4(uI.w * pane.r * (1.0 - pane.g), 0.0, 0.0, 1.0)
                     : vec4(0.0, 1.0 - uI.z * pane.r, 0.0, 1.0);
    }
    bool born = false;
    if (stars) {
        born = last.r < 1.0 && last.r > 0.9 * uI.w * pane.r * (1.0 - pane.g) && starts(c, size);
    } else {
        for (int y = -1; y <= 1 && !born; y++)
            for (int x = -1; x <= 1 && !born; x++)
                born = starts(c + ivec2(x, y), size);
    }
    if (born) last.r = 1.0;
    bool ice = stars ? last.r >= 1.0 : last.r > 0.5;
    last.b = ice ? last.b + uI.x : last.b * exp(-uI.x / 0.3);
    fragColor = vec4(last.r, stars ? 0.0 : last.g, last.b, 1.0);
}
