// touchdesigner-effects (MIT), Pixel Art: the palette, one iteration of mass-constrained deterministic annealing a
// frame (K. Rose, Proc. IEEE 1998), as Gerstner et al. use it (their section 4.3), carried from frame to frame.
// Phase 1, cooling: the palette starts as one color, the picture's mean, at 1.1 times its critical temperature (twice
// the variance along its principal axis). Each color is two entries, perturbed apart along the color's principal axis.
// Every iteration refines each entry to the mean of the superpixels weighted by how much they belong to it (the
// paper's equation 4) and by their importance. When the palette settles, the temperature falls by alpha (0.7), and a
// color whose two entries have drifted apart splits into two colors, each again two entries, until there are Colors
// of them. On video the palette never quite settles, so the temperature also falls once it has spent a little while
// at one temperature (ours: counted in seconds, so the palette takes shape as fast at any frame rate).
// Phase 2, all its colors: each color is one entry, and the temperature goes on falling to the final one as in the
// paper. There (ours, for video) each color is refined every frame as the picture moves, which is k-means warm-started
// from the last frame. A color nobody uses any more takes half of the most spread-out color (split along that color's
// principal axis, MCDA's own direction for a split), and so does a new color when Colors goes up; when Colors goes
// down, the last color goes. One such change a frame.
// Inputs: 0 each entry's totals (totals.glsl), 1 last frame's palette.
// The art shows the palette only once it has all its colors, fading in over Reveal seconds (ours): the splits before
// that, each changing large parts of the picture a few frames apart, flashed while the palette took shape.
// Out, 64 x 4: row 0 the entries (Lab, share of the picture; 0 for none), row 1 the colors as the art shows them (Lab,
// which side of the red line; see shown()), row 2's first pixel the state (temperature, phase, seconds at it,
// colors) and its second how far the palette has faded in (0-1), row 3 the colors (Lab, share; 0 for none). Each pixel
// works the whole step out and writes its own part.
uniform vec4 uP;   // x Colors, y Hold Palette, z the final temperature, w seconds since the last frame
uniform vec4 uQ;   // x alpha, y the most seconds at one temperature, z the palette counts as settled under this much
                   // change (Lab, summed), w two entries this far apart (Lab) are two colors
uniform vec4 uR;   // x the perturbation (Lab), y a color holding less than this (in superpixels) is unused, z the least
                   // variance worth splitting (Lab^2), w Reveal (s)
uniform vec4 uS;   // x Saturation
out vec4 fragColor;

vec4 total(int e, int part) {
    return texelFetch(sTD2DInputs[0], ivec2(3 * e + part, 0), 0);
}

vec4 last(int x, int y) {
    return texelFetch(sTD2DInputs[1], ivec2(x, y), 0);
}

struct Stats {
    float mass;
    vec3 mean;
    mat3 cov;
};

// An entry's superpixels: how much of the picture (sum w P), their weighted mean color and spread. c is the color the
// moments were taken around (the entry's color last frame).
Stats entry(int e, vec3 c) {
    vec4 a = total(e, 0), b = total(e, 1), d = total(e, 2);
    Stats s;
    s.mass = a.x;
    float m = max(a.x, 1e-12);
    vec3 off = a.yzw / m;
    s.mean = a.x > 0.0 ? c + off : c;
    s.cov = mat3(b.x, b.y, b.z, b.y, b.w, d.x, b.z, d.x, d.y) / m - outerProduct(off, off);
    return s;
}

Stats join(Stats p, Stats q) {
    Stats s;
    s.mass = p.mass + q.mass;
    float m = max(s.mass, 1e-12);
    s.mean = (p.mean * p.mass + q.mean * q.mass) / m;
    vec3 dp = p.mean - s.mean, dq = q.mean - s.mean;
    s.cov = (p.mass * (p.cov + outerProduct(dp, dp)) + q.mass * (q.cov + outerProduct(dq, dq))) / m;
    return s;
}

// The largest variance and its direction, by power iteration.
vec3 axis(mat3 cov, out float lam) {
    vec3 v = normalize(vec3(1.0, 0.6, 0.3));
    for (int i = 0; i < 16; i++) {
        vec3 w = cov * v;
        float l = length(w);
        if (l < 1e-9) break;
        v = w / l;
    }
    lam = max(dot(v, cov * v), 0.0);
    return v;
}

// What this pixel writes for color k: as a pair of entries (cooling) or one (following).
vec4 write(ivec2 me, int k, bool on, vec3 mean, float share, bool pair, vec3 v) {
    if (me.y == 3) return on ? vec4(mean, share) : vec4(0.0);
    if (!on) return vec4(0.0);
    int half_ = me.x - 2 * k;
    if (pair) return vec4(mean + (half_ == 0 ? 1.0 : -1.0) * uR.x * v, 0.5 * share);
    return half_ == 0 ? vec4(mean, share) : vec4(0.0);
}

vec4 next(ivec2 me) {
    bool have = PALETTE_OK(1);
    vec4 state = have ? last(0, 2) : vec4(0.0);
    int n = int(state.w + 0.5);
    int want = int(uP.x + 0.5);
    if (state.y > 1.5 && uP.y > 0.5) {   // Hold Palette, once it has all its colors
        return last(me.x, me.y);
    }
    float weight = 0.0;
    for (int e = 0; e < ENTRIES; e++) weight += total(e, 0).x;
    if (me == ivec2(1, 2)) {   // the fade in, from when the palette had all its colors
        return vec4(state.y > 1.5 ? min((have ? last(1, 2).x : 0.0) + uP.w / uR.w, 1.0) : 0.0, 0.0, 0.0, 1.0);
    }
    if (weight <= 0.0 || me.y == 1 || (me.y == 2 && me.x > 1) || (me.y == 3 && me.x >= COLORS)) {
        return (weight <= 0.0 && have) ? last(me.x, me.y) : vec4(0.0);
    }
    int k = me.y == 0 ? me.x / 2 : me.x;   // the color this pixel writes (row 0: its entry's)
    float alpha = uQ.x, tf = uP.z;

    // ---- Start: one color, the picture's mean, at 1.1 times its critical temperature ----
    if (state.y < 0.5) {
        Stats s = entry(0, vec3(0.0));
        float lam;
        vec3 v = axis(s.cov, lam);
        if (me.y == 2) {
            return vec4(max(1.1 * 2.0 * lam, tf), 1.0, 0.0, 1.0);
        }
        return write(me, k, k == 0, s.mean, 1.0, true, v);
    }

    // ---- Cooling: refine every entry; when settled, cool and split ----
    if (state.y < 1.5) {
        float change = 0.0;
        for (int e = 0; e < 2 * n; e++) {
            vec4 o = last(e, 0);
            if (o.a <= 0.0) continue;
            change += dot(abs(entry(e, o.rgb).mean - o.rgb), vec3(1.0));
        }
        float at = state.z + uP.w;
        bool cool = change < uQ.z || at >= uQ.y;
        if (!cool) {
            if (me.y == 2) {
                return vec4(state.x, 1.0, at, float(n));
            }
            if (k >= n) {
                return vec4(0.0);
            }
            Stats a = entry(2 * k, last(2 * k, 0).rgb), b = entry(2 * k + 1, last(2 * k + 1, 0).rgb);
            if (me.y == 3) {
                Stats j = join(a, b);
                return vec4(j.mean, j.mass / weight);
            }
            Stats s = me.x == 2 * k ? a : b;
            return s.mass > 0.0 ? vec4(s.mean, s.mass / weight) : vec4(0.0);
        }
        float t = max(state.x * alpha, tf);
        int room = max(want - n, 0);
        int separated = 0;
        int from = -1, part = 0;   // which old color this pixel's color comes from, and which of its entries (2: both)
        for (int c = 0; c < n; c++) {
            vec4 oa = last(2 * c, 0), ob = last(2 * c + 1, 0);
            bool split = false;
            if (oa.a > 0.0 && ob.a > 0.0 && separated < room) {
                split = distance(entry(2 * c, oa.rgb).mean, entry(2 * c + 1, ob.rgb).mean) > uQ.w;
            }
            if (c == k) {
                from = c;
                part = split ? 0 : 2;
            }
            if (split) {
                if (n + separated == k) {
                    from = c;
                    part = 1;
                }
                separated++;
            }
        }
        int n2 = n + separated;
        bool done = n2 >= want || t <= tf * 1.0001;
        if (me.y == 2) {
            return vec4(t, done ? 2.0 : 1.0, 0.0, float(n2));
        }
        if (from < 0) {
            return vec4(0.0);
        }
        Stats s;
        if (part == 2) s = join(entry(2 * from, last(2 * from, 0).rgb), entry(2 * from + 1, last(2 * from + 1, 0).rgb));
        else s = entry(2 * from + part, last(2 * from + part, 0).rgb);
        float lam;
        vec3 v = axis(s.cov, lam);
        return write(me, k, s.mass > 0.0, s.mean, s.mass / weight, !done, v);
    }

    // ---- All colors: each refined, cooling on to the final temperature, one change a frame ----
    int dead = -1, donor = -1;
    float best = 0.0, change = 0.0;
    for (int c = 0; c < n; c++) {
        vec4 o = last(2 * c, 0);
        float mass = o.a > 0.0 ? total(2 * c, 0).x : 0.0;
        if (mass < uR.y) {
            if (dead < 0) dead = c;
            continue;
        }
        Stats s = entry(2 * c, o.rgb);
        change += dot(abs(s.mean - o.rgb), vec3(1.0));
        float lam;
        axis(s.cov, lam);
        if (lam > uR.z && s.mass * lam > best) {
            best = s.mass * lam;
            donor = c;
        }
    }
    int n2 = n;
    int slot = -1;   // the color that takes half of the donor's
    if (n > want) n2 = n - 1;
    else if (dead >= 0) slot = dead;
    else if (n < want && n < COLORS) slot = n;
    if (slot >= 0 && donor < 0) slot = -1;
    if (slot == n) n2 = n + 1;
    if (me.y == 2) {
        float t = state.x, at = state.z + uP.w;
        if (t > tf && (change < uQ.z || at >= uQ.y)) {
            t = max(t * alpha, tf);
            at = 0.0;
        }
        return vec4(t, 2.0, t > tf ? at : 0.0, float(n2));
    }
    if (k >= n2) {
        return vec4(0.0);
    }
    if (slot >= 0 && (k == slot || k == donor)) {
        Stats s = entry(2 * donor, last(2 * donor, 0).rgb);
        float lam;
        vec3 v = axis(s.cov, lam);
        vec3 c = s.mean + (k == slot ? 1.0 : -1.0) * 0.5 * sqrt(lam) * v;
        return write(me, k, true, c, 0.5 * s.mass / weight, false, v);
    }
    vec4 o = last(2 * k, 0);
    float mass = o.a > 0.0 ? total(2 * k, 0).x : 0.0;
    if (mass <= 0.0) {
        return vec4(0.0);
    }
    Stats s = entry(2 * k, o.rgb);
    return write(me, k, true, s.mean, s.mass / weight, false, vec3(0.0));
}

// The color the art shows for palette color c (ours, for WCAG): saturated by Saturation (the paper's last step), and
// kept clear of WCAG's saturated-red line, a red share of 80% in linear light. That test is all or nothing, so a
// palette color whose share sits near the line and drifts across it as the palette follows the picture turned every
// pixel it covers to "saturated red" and back at once, though nothing visible changed (the red flowers' dark red-brown,
// a share of 0.75 to 0.87 over 8 s: bursts of red flashes with Flashing Off). Each color keeps a side of the line,
// held at most BELOW or at least ABOVE, and changes side only once its own share is past DOWN_AT or UP_AT: green and
// blue are added (as the color has them, as lib red_guard.glsl does) or taken away to hold it there. A deep red stays
// deep red. before: last frame's (its alpha the side, 1 above, -1 below).
#define BELOW 0.77
#define ABOVE 0.83
#define DOWN_AT 0.74
#define UP_AT 0.86

vec4 shown(vec4 c, vec4 before) {
    if (c.a <= 0.0) return vec4(0.0);
    vec3 lin = lab_to_linear(vec3(c.x, c.yz * uS.x));
    float gb = lin.g + lin.b, share = lin.r / max(lin.r + gb, 1e-6);
    float side = before.a != 0.0 ? before.a : (share >= 0.8 ? 1.0 : -1.0);
    if (side > 0.0 && share < DOWN_AT) side = -1.0;
    if (side < 0.0 && share > UP_AT) side = 1.0;
    if (side < 0.0 && share > BELOW) {
        float e = 0.01 * lin.r;
        lin.gb += (lin.r * (1.0 / BELOW - 1.0) - gb) * (lin.gb + e) / (gb + 2.0 * e);
    } else if (side > 0.0 && share < ABOVE) {
        lin.gb *= lin.r * (1.0 / ABOVE - 1.0) / max(gb, 1e-6);
    }
    return vec4(linear_to_lab(lin), side);
}

void main() {
    ivec2 me = ivec2(gl_FragCoord.xy);
    if (me.y == 1) {   // the colors as the art shows them
        fragColor = me.x < COLORS ? shown(next(ivec2(me.x, 3)), PALETTE_OK(1) ? last(me.x, 1) : vec4(0.0)) : vec4(0.0);
        return;
    }
    fragColor = next(me);
}
