// Depth Particles (touchdesigner-effects, MIT). Finds the people: whatever stands in front of its
// surroundings in the depth map.
// Find on Stand Out: a pixel counts when it is nearer than the Far Limit and something at least
// Stand Out farther lies both to its left and to its right in the same row. A floor is about as
// near all along a row, and a wall gets steadily nearer or farther along one, so neither passes;
// a person has background on both sides. (Two things it can't tell: a person cut off by the left
// or right edge of the frame has nothing beside them on that side and drops out, and feet merge
// with the floor they stand on. A plain threshold or a blurred background brought in the floor,
// the walls and every beam overhead, on the library's test clips.)
// Find on Nearer Than: the Far Limit alone decides, for a mask or a depth camera that sees no floor.
// Inputs: 0 nearness and validity (near.glsl).
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
    // The farthest reading to the left and to the right along the row.
    float left = 2.0, right = 2.0;
    for (int x = 0; x < w; x++) {
        vec2 d = texelFetch(sTD2DInputs[0], ivec2(x, p.y), 0).rg;
        if (d.g < 0.5 || x == p.x) continue;
        if (x < p.x) left = min(left, d.r); else right = min(right, d.r);
    }
    float stand = left > 1.5 || right > 1.5 ? 0.0 : here.r - max(left, right);
    bool near = here.r > uFind.z;
    bool inside = uFind.x > 0.5 ? near : near && stand > uFind.y;
    fragColor = vec4(inside ? 1.0 : 0.0, here.r, max(stand, 0.0), 1.0);
}
