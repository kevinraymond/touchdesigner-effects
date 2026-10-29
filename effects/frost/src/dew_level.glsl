// Frost (touchdesigner-effects, MIT): the Dew style's third pass a frame (dew_atlas.glsl says how the droplets are
// kept). Droplets marked to move up a level (dew_merge.glsl) leave their cell, and the cell above that holds their
// place takes them, merged with what it holds; a droplet that a bigger one a level or more above touches goes into
// it, which takes its volume; and free glass starts new droplets: a cell of the smallest level that no droplet covers
// starts one with a chance a second, where the glass is cold and not warm, at a random place in it.
// Inputs: 0 dew_merge's droplets (a: 1 if moving up), 1 the pane (pane.glsl: r cold, g warm).
// Out: r, g, b the droplet, a 0.
uniform vec4 uN;   // x the chance a second a free cell starts a droplet where coldest, y a new droplet's radius,
                   // z this frame's step (s), w the clock
out vec4 fragColor;

float rand(ivec2 c, uint salt) {
    return float(ihash(uint(c.x) + 8192u * uint(c.y) + ihash(floatBitsToUint(uN.w) + salt))) / 4294967295.0;
}

void add(inout float vol, inout vec2 m, vec4 d) {
    float v = d.b * d.b * d.b;
    vol += v;
    m += d.xy * v;
}

void main() {
    N = textureSize(sTD2DInputs[0], 0).x;
    ASP = aspect(1);
    ivec3 w = where(ivec2(gl_FragCoord.xy));
    if (w.z < 0) { fragColor = vec4(0.0); return; }
    int k = w.z;
    vec4 me = drop(0, k, w.xy);
    if (me.a > 0.5) me = vec4(0.0);
    // touched by a bigger droplet above: it goes into that one
    for (int j = k + 1; j < LEVELS && me.b > 0.0; j++) {
        ivec2 cc = cellof(j, me.xy);
        for (int y = -1; y <= 1; y++)
            for (int x = -1; x <= 1; x++) {
                vec4 n = drop(0, j, cc + ivec2(x, y));
                if (n.b > 0.0 && distance(n.xy, me.xy) < n.b + me.b) me = vec4(0.0);
            }
    }
    float vol = 0.0;
    vec2 m = vec2(0.0);
    if (me.b > 0.0) add(vol, m, me);
    if (k > 0) {
        // the droplets moving up from the four cells below this one
        for (int y = 0; y <= 1; y++)
            for (int x = 0; x <= 1; x++) {
                vec4 ch = drop(0, k - 1, 2 * w.xy + ivec2(x, y));
                if (ch.b > 0.0 && ch.a > 0.5) add(vol, m, ch);
            }
        // and the smaller ones this droplet touches, which go into it
        if (me.b > 0.0) {
            ivec2 cc = cellof(k - 1, me.xy);
            for (int y = -2; y <= 2; y++)
                for (int x = -2; x <= 2; x++) {
                    vec4 ch = drop(0, k - 1, cc + ivec2(x, y));
                    if (ch.b > 0.0 && ch.a < 0.5 && distance(ch.xy, me.xy) < ch.b + me.b) add(vol, m, ch);
                }
        }
    }
    if (vol > 0.0) {
        fragColor = vec4(m / vol, pow(vol, 1.0 / 3.0), 0.0);
        return;
    }
    // free glass at the smallest level: a new droplet, now and then
    if (k == 0) {
        float cs = cellsize(0);
        vec2 mid = (vec2(w.xy) + 0.5) * cs;
        bool covered = mid.x > ASP.x || mid.y > ASP.y;
        for (int j = 0; j < LEVELS && !covered; j++) {
            ivec2 cc = cellof(j, mid);
            for (int y = -1; y <= 1; y++)
                for (int x = -1; x <= 1; x++) {
                    vec4 n = drop(0, j, cc + ivec2(x, y));
                    if (n.b > 0.0 && distance(n.xy, mid) < n.b + 0.5 * cs) covered = true;
                }
        }
        if (!covered) {
            vec2 pane = texture(sTD2DInputs[1], mid / ASP).rg;
            if (rand(w.xy, 0u) < uN.x * uN.z * pane.r * (1.0 - pane.g)) {
                vec2 at = (vec2(w.xy) + vec2(rand(w.xy, 1u), rand(w.xy, 2u))) * cs;
                fragColor = vec4(at, uN.y, 0.0);
                return;
            }
        }
    }
    fragColor = vec4(0.0);
}
