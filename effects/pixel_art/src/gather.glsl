// touchdesigner-effects (MIT), Pixel Art: each superpixel's new center and mean color, from the pixels that joined
// it (assign.glsl), SLIC's update step. A superpixel reaches only the pixels within S of its center, so it looks
// through that 2S x 2S window. A compute shader, one workgroup a superpixel: its 64 invocations share the window, each
// summing every eighth pixel across and down, and the 64 sums are added up in shared memory, halving each step (a
// parallel reduction, as in W. D. Hillis and G. L. Steele, "Data parallel algorithms", CACM 1986). One invocation
// walking the whole window alone cost 2.2 ms on the reference Mac. A superpixel that lost every pixel keeps its place
// and takes the color under its center (left at 0, it would show as black specks where a bright light crowds its
// neighbors out).
// Inputs: 0 which superpixel each pixel joined (assign.glsl), 1 the picture in Lab (lab.glsl), 2 last frame's centers.
// Out, 2G x G, two pixels per superpixel side by side (0 past the grid's used part; one texture rather than two
// buffers, so nothing needs a Render Select TOP to pick the second out): at 2x its center (in pixels), how many pixels
// joined, S; at 2x + 1 their mean Lab, their mean importance.
#define SIDE 8
layout (local_size_x = SIDE, local_size_y = SIDE) in;
uniform vec4 uGrid;   // x Pixel Size, y the grid's allocated size G

shared vec4 sPlace[SIDE * SIDE];   // x, y, count, importance
shared vec4 sColor[SIDE * SIDE];   // L, a, b

void put(ivec2 me, vec4 place, vec4 color) {
    imageStore(mTDComputeOutputs[0], ivec2(2 * me.x, me.y), TDOutputSwizzle(place));
    imageStore(mTDComputeOutputs[0], ivec2(2 * me.x + 1, me.y), TDOutputSwizzle(color));
}

void main() {
    ivec2 res = textureSize(sTD2DInputs[1], 0);
    int s = cell_size(res, uGrid.x, uGrid.y);
    ivec2 n = grid_size(res, s);
    ivec2 me = ivec2(gl_WorkGroupID.xy);
    uint t = gl_LocalInvocationIndex;
    if (me.x >= n.x || me.y >= n.y) {   // the same for the whole workgroup
        if (t == 0u) put(me, vec4(0.0), vec4(0.0));
        return;
    }
    vec2 center = (vec2(me) + 0.5) * float(s);
    if (GRID_OK(2, uGrid.y)) {
        vec4 c = texelFetch(sTD2DInputs[2], me, 0);
        if (c.w > 0.0 && c.z == float(s)) center = c.xy;
    }
    ivec2 lo = max(ivec2(floor(center - float(s))), ivec2(0));
    ivec2 hi = min(ivec2(ceil(center + float(s))), res);
    ivec2 mine = ivec2(gl_LocalInvocationID.xy);
    vec4 place = vec4(0.0);
    vec3 color = vec3(0.0);
    for (int y = lo.y + mine.y; y < hi.y; y += SIDE) {
        for (int x = lo.x + mine.x; x < hi.x; x += SIDE) {
            ivec2 o = ivec2(round(texelFetch(sTD2DInputs[0], ivec2(x, y), 0).rg * 2.0)) - 1;
            if (ivec2(x, y) / s + o != me) continue;
            vec4 lab = texelFetch(sTD2DInputs[1], ivec2(x, y), 0);
            place += vec4(float(x) + 0.5, float(y) + 0.5, 1.0, lab.a);
            color += lab.rgb;
        }
    }
    sPlace[t] = place;
    sColor[t] = vec4(color, 0.0);
    memoryBarrierShared();
    barrier();
    for (uint k = uint(SIDE * SIDE / 2); k > 0u; k >>= 1) {
        if (t < k) {
            sPlace[t] += sPlace[t + k];
            sColor[t] += sColor[t + k];
        }
        memoryBarrierShared();
        barrier();
    }
    if (t != 0u) return;
    vec4 sum = sPlace[0];
    if (sum.z > 0.0) {
        put(me, vec4(sum.xy / sum.z, sum.z, float(s)), vec4(sColor[0].rgb / sum.z, sum.w / sum.z));
        return;
    }
    put(me, vec4(center, 0.0, float(s)), texelFetch(sTD2DInputs[1], clamp(ivec2(center), ivec2(0), res - 1), 0));
}
