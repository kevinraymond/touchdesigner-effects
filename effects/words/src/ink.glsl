// touchdesigner-effects (MIT), Words: where each word's ink lies in the atlas, so the layout packs the letters, not
// the line they sit on ("soul" has nothing below its baseline, "body" does). A compute shader, a workgroup a word: its
// invocations share the word's slot in the atlas and keep the leftmost, lowest, rightmost and highest pixel with ink,
// in shared memory. It cooks only when the atlas or the words change.
// Inputs: 0 the atlas (alpha: ink), 1 the words (vocab: a pixel a word; rows x, y (baseline), w, asc, desc).
// Out MAX_WORDS x 1: (left, bottom, right, top) of each word's ink in atlas pixels, right and top past the last pixel;
// a word without ink (or past the last word) gets an empty box at its baseline.
#define THREADS 256
#define PAD 3
layout (local_size_x = THREADS) in;

shared int sLo[2];
shared int sHi[2];

void main() {
    uint t = gl_LocalInvocationIndex;
    int i = int(gl_WorkGroupID.x);
    int n = textureSize(sTD2DInputs[1], 0).x;
    if (t == 0u) {
        sLo[0] = sLo[1] = 1 << 20;
        sHi[0] = sHi[1] = -1;
    }
    memoryBarrierShared();
    barrier();
    vec4 box = vec4(0.0);
    if (i < n) {
        float x = texelFetch(sTD2DInputs[1], ivec2(i, 0), 0).r;
        float y = texelFetch(sTD2DInputs[1], ivec2(i, 1), 0).r;
        float w = texelFetch(sTD2DInputs[1], ivec2(i, 2), 0).r;
        float asc = texelFetch(sTD2DInputs[1], ivec2(i, 3), 0).r;
        float desc = texelFetch(sTD2DInputs[1], ivec2(i, 4), 0).r;
        ivec2 size = textureSize(sTD2DInputs[0], 0);
        int x0 = max(int(floor(x)) - PAD, 0), x1 = min(int(ceil(x + w)) + PAD, size.x);
        int y0 = max(int(floor(y - desc)) - PAD, 0), y1 = min(int(ceil(y + asc)) + PAD, size.y);
        int cols = max(x1 - x0, 0);
        int count = cols * max(y1 - y0, 0);
        ivec2 lo = ivec2(1 << 20), hi = ivec2(-1);
        for (int k = int(t); k < count; k += THREADS) {
            ivec2 p = ivec2(x0 + k % cols, y0 + k / cols);
            if (texelFetch(sTD2DInputs[0], p, 0).a > 0.3) {
                lo = min(lo, p);
                hi = max(hi, p);
            }
        }
        if (hi.x >= 0) {
            atomicMin(sLo[0], lo.x);
            atomicMin(sLo[1], lo.y);
            atomicMax(sHi[0], hi.x);
            atomicMax(sHi[1], hi.y);
        }
        memoryBarrierShared();
        barrier();
        box = sHi[0] >= 0 ? vec4(sLo[0], sLo[1], sHi[0] + 1, sHi[1] + 1) : vec4(x, y, x, y);
    }
    if (t == 0u) imageStore(mTDComputeOutputs[0], ivec2(i, 0), TDOutputSwizzle(box));
}
