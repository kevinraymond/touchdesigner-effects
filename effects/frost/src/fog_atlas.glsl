// Frost (touchdesigner-effects, MIT): the Fog style's droplets, pasted in front of each fog shader. Breath figures,
// the droplets that fog a cold pane, as D. Beysens and C. M. Knobler watched them form ("Growth of Breath Figures",
// Phys. Rev. Lett. 57, 1986) and D. Fritter, C. M. Knobler and D. Beysens simulated them (Phys. Rev. A 43, 1991):
// droplets start on the free glass, grow as it condenses water, and two that touch become
// one, its volume theirs, at their center of volume, which frees glass for new small droplets between the big ones.
// The droplets live in one atlas, a level a size: level k's cells are 2^k times level 0's, one droplet a cell, its
// radius at most half its cell, so a droplet can only touch those in the 3 x 3 cells around it on its own level
// (and bigger ones above). The atlas is N cells wide (its width), levels stacked: level 0's N rows, level 1's N / 2
// rows of N / 2, and so on, LEVELS levels. A texel holds a droplet: r, g its middle and b its radius, in units of the
// picture's longer side (the droplets lie on a square that long, its corner at the picture's lower left); b 0 for
// none; a a flag the passes use.
#define LEVELS 4
int N;

int side(int k) { return N >> k; }
int base(int k) { return k == 0 ? 0 : k == 1 ? N : k == 2 ? N + N / 2 : N + N / 2 + N / 4; }
float cellsize(int k) { return 1.0 / float(N >> k); }

// Which level and cell texel t holds (level -1: none).
ivec3 where(ivec2 t) {
    for (int k = 0; k < LEVELS; k++)
        if (t.y >= base(k) && t.y < base(k) + side(k)) return t.x < side(k) ? ivec3(t.x, t.y - base(k), k) : ivec3(-1);
    return ivec3(-1);
}

// The droplet in level k's cell c of the atlas on input i (none off the level).
vec4 drop(int i, int k, ivec2 c) {
    if (any(lessThan(c, ivec2(0))) || any(greaterThanEqual(c, ivec2(side(k))))) return vec4(0.0);
    return texelFetch(sTD2DInputs[i], ivec2(c.x, base(k) + c.y), 0);
}

// The picture's size as a share of its longer side (1 and 0.5625 for 1280 x 720), from input i (any TOP the
// picture's shape).
vec2 ASP;
vec2 aspect(int i) { vec2 s = uTD2DInfos[i].res.zw; return s / max(s.x, s.y); }

// Level k's cell holding a point (in the droplets' units).
ivec2 cellof(int k, vec2 p) { return ivec2(floor(p / cellsize(k))); }
