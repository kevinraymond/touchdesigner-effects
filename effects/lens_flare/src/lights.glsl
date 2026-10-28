// touchdesigner-effects (MIT), Lens Flare: the lights, found in the tiles (tiles.glsl). The brightest tile becomes a
// light along with the tiles around it, then the brightest light left, and so on, Lights times and once more. A tile
// within half of MERGE of the brightest gives it all its light, one further out less and less, none past MERGE, and
// keeps the rest for the lights after: with a hard edge a tile would switch lights whenever another became the
// brightest, and the light's place would jump (its ghosts further still: they sit at multiples of it). A light's place is its tiles' centroid, its spread how far their light lies from it (a big
// lamp blurs its ghosts, ghost.glsl), its color their mean. The last light's energy is taken off every other one,
// so a light that drops out of the brightest few fades out instead of vanishing (and nothing changes if fewer are
// found). Then each energy E becomes S ln(1 + E / S): the picture clips every light to white, so how much of it is
// clipped is all that tells a lamp from the sun, and taken as is the sun would whiten the whole picture.
// A compute shader, one workgroup: its invocations each hold a few tiles, and every step (the brightest tile, the sums
// of a light's tiles) is added up in shared memory, halving each step (a parallel reduction, as in W. D. Hillis and
// G. L. Steele, "Data parallel algorithms", CACM 1986).
// Input: 0 the tiles. Out MAX_LIGHTS x 2: row 0 each light's (x, y, energy, spread), row 1 its (red, green, blue, 1);
// zeros past the lights found.
#define THREADS 512
#define PER 4
#define MAX_LIGHTS 16
layout (local_size_x = THREADS) in;
uniform vec4 uLights;   // x how many lights (Lights), y MERGE (picture units), z T (tiles across), w S

shared vec4 sA[THREADS];
shared vec4 sB[THREADS];
shared vec4 sPlace[MAX_LIGHTS + 1];
shared vec4 sColor[MAX_LIGHTS + 1];

void main() {
    uint t = gl_LocalInvocationIndex;
    int T = int(uLights.z);
    int K = min(int(uLights.x), MAX_LIGHTS);
    vec4 mom[PER];
    vec3 col[PER];
    vec2 cen[PER];
    float left[PER];   // the share of each tile's light no light has taken yet
    for (int k = 0; k < PER; k++) {
        int i = int(t) + k * THREADS;
        mom[k] = vec4(0.0);
        col[k] = vec3(0.0);
        cen[k] = vec2(0.0);
        left[k] = 0.0;
        if (i < T * T) {
            ivec2 tile = ivec2(i % T, i / T);
            mom[k] = texelFetch(sTD2DInputs[0], tile, 0);
            col[k] = texelFetch(sTD2DInputs[0], tile + ivec2(T, 0), 0).rgb;
            left[k] = mom[k].x > 1e-9 ? 1.0 : 0.0;
            cen[k] = mom[k].yz / max(mom[k].x, 1e-12);
        }
    }
    int found = 0;
    for (int n = 0; n <= K; n++) {
        vec4 best = vec4(0.0);
        for (int k = 0; k < PER; k++) {
            float e = left[k] * mom[k].x;
            if (e > best.x) best = vec4(e, 0.0, cen[k]);
        }
        sA[t] = best;
        memoryBarrierShared();
        barrier();
        for (uint s = uint(THREADS / 2); s > 0u; s >>= 1) {
            if (t < s && sA[t + s].x > sA[t].x) sA[t] = sA[t + s];
            memoryBarrierShared();
            barrier();
        }
        vec4 win = sA[0];
        barrier();
        if (win.x <= 1e-12) break;   // the same for every invocation: all read it from shared memory
        vec4 m = vec4(0.0);
        vec3 c = vec3(0.0);
        for (int k = 0; k < PER; k++) {
            float w = left[k] * clamp(2.0 - 2.0 * distance(cen[k], win.zw) / uLights.y, 0.0, 1.0);
            m += w * mom[k];
            c += w * col[k];
            left[k] -= w;
        }
        sA[t] = m;
        sB[t] = vec4(c, 0.0);
        memoryBarrierShared();
        barrier();
        for (uint s = uint(THREADS / 2); s > 0u; s >>= 1) {
            if (t < s) {
                sA[t] += sA[t + s];
                sB[t] += sB[t + s];
            }
            memoryBarrierShared();
            barrier();
        }
        if (t == 0u) {
            vec4 sum = sA[0];
            vec2 p = sum.yz / sum.x;
            sPlace[n] = vec4(p, sum.x, sqrt(max(sum.w / sum.x - dot(p, p), 0.0)));
            sColor[n] = vec4(sB[0].rgb / sum.x, 1.0);
        }
        found = n + 1;
        memoryBarrierShared();
        barrier();
    }
    if (t < uint(MAX_LIGHTS)) {
        int i = int(t);
        bool lit = i < min(found, K);
        vec4 place = lit ? sPlace[i] : vec4(0.0);
        place.z = max(place.z - (found > K ? sPlace[K].z : 0.0), 0.0);
        place.z = uLights.w * log(1.0 + place.z / uLights.w);
        imageStore(mTDComputeOutputs[0], ivec2(i, 0), TDOutputSwizzle(place));
        imageStore(mTDComputeOutputs[0], ivec2(i, 1), TDOutputSwizzle(lit ? sColor[i] : vec4(0.0)));
    }
}
