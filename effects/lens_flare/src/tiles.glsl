// touchdesigner-effects (MIT), Lens Flare: the bright pass (bright.glsl) summed in tiles of 8 x 8 (32 x 32 of the
// picture's pixels): each tile's energy, the first and second moments of where it lies, and its light's color. A flare
// is linear in the light that makes it, so these sums are all the light finding needs: lights.glsl gathers tiles into
// lights by them. Eased over time (EASE, a fifth of a second), so a light's noise and bobbing don't flicker its ghosts,
// which sit far from it and magnify its movement.
// Energy is in picture units squared (an area times how far past the threshold it is), so it doesn't change with the
// picture's size.
// Inputs: 0 the bright pass, 1 last frame's tiles (tiles_fb).
// Out 2T x T (T = 40 tiles across: enough for the free license's 1280): at x < T a tile's (energy, energy x, energy
// y, energy |p|^2); at x >= T its (red, green, blue) energy and 1 (the feedback's first frame reads 0 there).
uniform vec4 uTiles;   // x T, y how far to ease this frame (0-1)

out vec4 fragColor;
void main() {
    ivec2 o = ivec2(gl_FragCoord.xy);
    int T = int(uTiles.x);
    bool color = o.x >= T;
    ivec2 tile = ivec2(color ? o.x - T : o.x, o.y);
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    float area = 1.0 / (0.25 * dot(vec2(size), vec2(size)));   // one pixel of the pass, in picture units squared
    vec4 sum = vec4(0.0);
    for (int y = 0; y < 8; y++) {
        for (int x = 0; x < 8; x++) {
            ivec2 b = tile * 8 + ivec2(x, y);
            if (b.x >= size.x || b.y >= size.y) continue;
            vec4 v = texelFetch(sTD2DInputs[0], b, 0) * area;
            if (color) {
                sum.rgb += v.rgb;
            } else {
                vec2 p = to_picture(vec2(b) + 0.5, vec2(size));
                sum += v.a * vec4(1.0, p, dot(p, p));
            }
        }
    }
    if (color) sum.a = 1.0;
    ivec2 last_size = textureSize(sTD2DInputs[1], 0);
    if (last_size == ivec2(2 * T, T) && texelFetch(sTD2DInputs[1], ivec2(T + tile.x, tile.y), 0).a > 0.5) {
        sum = mix(texelFetch(sTD2DInputs[1], o, 0), sum, uTiles.y);
    }
    fragColor = TDOutputSwizzle(sum);
}
