// touchdesigner-effects (MIT), shared by the effects that read depth (lib/glsl, lib_glsl()).
// Finds the people (or anything) in the depth map: whatever stands in front of its surroundings.
// Find on Stand Out: a pixel counts when it is nearer than the Far Limit and something at least
// Stand Out farther lies both to its left and to its right in the same row. A floor is about as
// near all along a row, and a wall gets steadily nearer or farther along one, so neither passes;
// a person has background on both sides. (Two things it can't tell: a person cut off by the left
// or right edge of the frame has nothing beside them on that side and drops out, and feet merge
// with the floor they stand on. A plain threshold or a blurred background brought in the floor,
// the walls and every beam overhead, on the library's test clips.)
// Find on Nearer Than: the Far Limit alone decides, for a mask or a depth camera that sees no floor.
// Inputs: 0 nearness and validity (depth_near.glsl).
// Out: r 1 inside, else 0; g nearness; b how much nearer than its row's surroundings it is.
uniform vec4 uFind;   // x Find (0 Stand Out, 1 Nearer Than), y Stand Out, z Far Limit
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    int w = textureSize(sTD2DInputs[0], 0).x;
    vec2 here = texelFetch(sTD2DInputs[0], p, 0).rg;
    if (here.g < 0.5) {                      // no reading here
        fragColor = vec4(0.0);
        return;
    }
    // The farthest reading to the left and to the right along the row, where it is the nearest of
    // three pixels side by side: a lone speck of sensor noise reading farther doesn't count, or one
    // speck would make a whole span of the row stand out. a, b, c: three pixels, -1 without a reading.
    float left = 2.0, right = 2.0, a = -1.0, b = -1.0;
    for (int x = 0; x <= w; x++) {
        float c = -1.0;
        if (x < w) {
            vec2 d = texelFetch(sTD2DInputs[0], ivec2(x, p.y), 0).rg;
            c = d.g < 0.5 ? -1.0 : d.r;
        }
        if (x >= 1 && x - 1 != p.x && b >= 0.0) {
            float m = max(b, max(a, c));
            if (x - 1 < p.x) left = min(left, m); else right = min(right, m);
        }
        a = b;
        b = c;
    }
    float stand = left > 1.5 || right > 1.5 ? 0.0 : here.r - max(left, right);
    bool near = here.r > uFind.z;
    bool inside = uFind.x > 0.5 ? near : near && stand > uFind.y;
    fragColor = vec4(inside ? 1.0 : 0.0, here.r, max(stand, 0.0), 1.0);
}
