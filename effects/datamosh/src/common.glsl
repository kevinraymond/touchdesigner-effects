// Datamosh-style (touchdesigner-effects, MIT): helpers pasted in front of the shaders that use them.

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

// Catmull-Rom bicubic sample of input i, clamped to the 2 x 2 texels around it, so moving the
// picture once per frame for seconds neither blurs it (as bilinear would) nor rings.
vec4 sampleCR(int i, vec2 uv) {
    ivec2 sz = ivec2(uTD2DInfos[i].res.zw);
    vec2 p = uv * vec2(sz) - 0.5;
    vec2 f = fract(p);
    ivec2 b = ivec2(floor(p));
    vec2 w[4];
    w[0] = f * (-0.5 + f * (1.0 - 0.5 * f));
    w[1] = 1.0 + f * f * (-2.5 + 1.5 * f);
    w[2] = f * (0.5 + f * (2.0 - 1.5 * f));
    w[3] = f * f * (-0.5 + 0.5 * f);
    vec4 acc = vec4(0.0), mn = vec4(1e9), mx = vec4(-1e9);
    for (int y = 0; y < 4; y++)
    for (int x = 0; x < 4; x++) {
        vec4 t = texelFetch(sTD2DInputs[i], clamp(b + ivec2(x - 1, y - 1), ivec2(0), sz - 1), 0);
        acc += t * w[x].x * w[y].y;
        if ((x == 1 || x == 2) && (y == 1 || y == 2)) { mn = min(mn, t); mx = max(mx, t); }
    }
    return clamp(acc, mn, mx);
}

// Integer hash "lowbias32" from Chris Wellons' hash-prospector (public domain, the Unlicense).
uint ihash(uint x) {
    x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16;
    return x;
}
float hash12(vec2 p) {
    return float(ihash(floatBitsToUint(p.x) ^ ihash(floatBitsToUint(p.y)))) / 4294967295.0;
}
