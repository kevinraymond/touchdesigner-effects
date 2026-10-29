// Frost (touchdesigner-effects, MIT): the Fog style's first pass a frame (fog_atlas.glsl, pasted in front, says how
// the droplets are kept). Each droplet grows as the glass condenses water where it is cold (its radius at a steady
// rate, as when the water on a unit of glass grows steadily, slowing near the largest size), dries where it is warm
// (small ones faster, as they do), and then picks the droplet it will go into if it touches any: the biggest it
// touches that is bigger than it (ties by place). Every droplet works out its neighbors' growth the same way, so the
// choices agree. A droplet off the picture's side of the square (past its height) dries away.
// Inputs: 0 the droplets last frame (Feedback TOP; sets the size: the atlas), 1 the pane (pane.glsl: r cold, g warm).
// Out: r, g, b the droplet grown; a 0, or 1 + which of the 8 cells around it holds the droplet it goes into.
uniform vec4 uG;   // x this frame's step (s), y growth (radius a second where coldest), z drying (radius a second where
                   // warmest), w the largest radius
uniform vec4 uA;   // x the smallest radius (smaller dries away)
out vec4 fragColor;

vec4 grown(int k, ivec2 c) {
    vec4 d = drop(0, k, c);
    if (d.b <= 0.0) return vec4(0.0);
    vec2 pane = texture(sTD2DInputs[1], d.xy / ASP).rg;
    float off = (d.x > ASP.x || d.y > ASP.y) ? 1.0 : 0.0;
    float r = d.b + uG.x * (uG.y * pane.r * (1.0 - pane.g) * max(1.0 - d.b / uG.w, 0.0)
                            - uG.z * max(pane.g, off) * (1.0 + 2.0 * uA.x / d.b));
    r = min(r, k == LEVELS - 1 ? 0.499 * cellsize(k) : uG.w);
    return r < uA.x ? vec4(0.0) : vec4(d.xy, r, 0.0);
}

void main() {
    N = textureSize(sTD2DInputs[0], 0).x;
    ASP = aspect(1);
    ivec3 w = where(ivec2(gl_FragCoord.xy));
    if (w.z < 0) { fragColor = vec4(0.0); return; }
    vec4 me = grown(w.z, w.xy);
    if (me.b <= 0.0) { fragColor = vec4(0.0); return; }
    int mine = w.y * side(w.z) + w.x;
    float best = 0.0;
    int pick = 0;
    int j = 0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++) {
            if (x == 0 && y == 0) continue;
            j++;
            ivec2 c = w.xy + ivec2(x, y);
            vec4 n = grown(w.z, c);
            if (n.b <= 0.0 || distance(n.xy, me.xy) >= n.b + me.b) continue;
            int theirs = c.y * side(w.z) + c.x;
            bool bigger = n.b > me.b || (n.b == me.b && theirs < mine);
            if (bigger && n.b > best) { best = n.b; pick = j; }
        }
    fragColor = vec4(me.xyz, float(pick));
}
