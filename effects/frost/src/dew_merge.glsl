// Frost (touchdesigner-effects, MIT): the Dew style's second pass a frame (dew_atlas.glsl says how the droplets are
// kept). Droplets that touch become one: a droplet that picked another (dew_grow.glsl) goes, and one that was picked
// takes the volumes of all that picked it (a radius cubed each), at their center of volume. A droplet grown to half
// its cell or more is marked to move up a level, where the next pass takes it.
// Inputs: 0 dew_grow's droplets (a: 1 + which of the 8 cells around holds the droplet each goes into).
// Out: r, g, b the droplet; a 1 if it moves up a level.
out vec4 fragColor;

// The offset of the cell a pick (1-8) names, in dew_grow.glsl's order: the row below first, left to right.
ivec2 offset(int j) {
    int i = j < 5 ? j - 1 : j;   // skip the middle
    return ivec2(i % 3 - 1, i / 3 - 1);
}

void main() {
    N = textureSize(sTD2DInputs[0], 0).x;
    ivec3 w = where(ivec2(gl_FragCoord.xy));
    vec4 me = w.z < 0 ? vec4(0.0) : drop(0, w.z, w.xy);
    if (me.b <= 0.0 || me.a > 0.5) { fragColor = vec4(0.0); return; }
    float vol = me.b * me.b * me.b;
    vec2 m = me.xy * vol;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++) {
            if (x == 0 && y == 0) continue;
            vec4 n = drop(0, w.z, w.xy + ivec2(x, y));
            if (n.b <= 0.0 || n.a < 0.5 || offset(int(n.a + 0.5)) != ivec2(-x, -y)) continue;
            float v = n.b * n.b * n.b;
            vol += v;
            m += n.xy * v;
        }
    float r = pow(vol, 1.0 / 3.0);
    bool up = w.z < LEVELS - 1 && r >= 0.5 * cellsize(w.z);
    fragColor = vec4(m / vol, r, up ? 1.0 : 0.0);
}
