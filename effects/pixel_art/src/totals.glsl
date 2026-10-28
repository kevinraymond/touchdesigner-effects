// touchdesigner-effects (MIT), Pixel Art: the sums the palette's "refine" step needs. For each palette entry c: how
// much of the picture it holds, sum of w_s P(c | s), and the first and second moments of the superpixels' colors around
// c weighted the same way, which give the entry's new color (the paper's equation 4) and its spread along its
// principal axis (where MCDA splits it, and how hot its critical temperature is). w_s is the superpixel's importance
// (lab.glsl), and P(c | s) = P(c) exp(-|m_s - c|^2 / T) / Z_s with assoc.glsl's Z_s. Moments are taken around c, not 0,
// so 32-bit floats keep the spread. Before the palette starts, every superpixel belongs wholly to entry 0, which gives
// the picture's mean and spread.
// A compute shader, one workgroup an entry: its 256 invocations share the superpixels, each summing every 256th, and
// the sums are added up in shared memory, halving each step (a parallel reduction, after W. D. Hillis and G. L.
// Steele, "Data parallel algorithms", CACM 1986).
// Inputs: 0 the superpixels' colors (colors.glsl), 1 assoc.glsl, 2 last frame's palette.
// Out: 3 pixels per entry across, one row: (sum w P, sum w P d), (dL dL, dL da, dL db, da da), (da db, db db, 0, 0),
// with d = m_s - c, each summed with weight w P.
layout (local_size_x = 256) in;

shared vec4 sA[256];
shared vec4 sB[256];
shared vec4 sC[256];

void main() {
    int e = int(gl_WorkGroupID.x);
    uint t = gl_LocalInvocationIndex;
    vec4 state = PALETTE_STATE(2);
    bool start = state.y < 0.5;
    vec4 c = start ? vec4(0.0, 0.0, 0.0, e == 0 ? 1.0 : 0.0) : texelFetch(sTD2DInputs[2], ivec2(e, 0), 0);
    if (c.a <= 0.0) {   // the same for the whole workgroup
        if (t < 3u) imageStore(mTDComputeOutputs[0], ivec2(3 * e + int(t), 0), TDOutputSwizzle(vec4(0.0)));
        return;
    }
    float temp = max(state.x, 1e-3);
    float prior = log(c.a);
    int g = textureSize(sTD2DInputs[0], 0).x;
    vec4 a = vec4(0.0), b = vec4(0.0), d2 = vec4(0.0);
    for (int i = int(t); i < g * g; i += 256) {
        ivec2 q = ivec2(i % g, i / g);
        vec4 x = texelFetch(sTD2DInputs[0], q, 0);
        if (x.a <= 0.0) continue;
        vec3 d = x.rgb - c.rgb;
        float p = x.a;
        if (!start) {
            vec4 z = texelFetch(sTD2DInputs[1], q, 0);
            p *= exp(prior - dot(d, d) / temp - z.x) / z.y;
        }
        a += p * vec4(1.0, d);
        b += p * vec4(d.x * d.x, d.x * d.y, d.x * d.z, d.y * d.y);
        d2 += p * vec4(d.y * d.z, d.z * d.z, 0.0, 0.0);
    }
    sA[t] = a;
    sB[t] = b;
    sC[t] = d2;
    memoryBarrierShared();
    barrier();
    for (uint k = 128u; k > 0u; k >>= 1) {
        if (t < k) {
            sA[t] += sA[t + k];
            sB[t] += sB[t + k];
            sC[t] += sC[t + k];
        }
        memoryBarrierShared();
        barrier();
    }
    if (t == 0u) {
        imageStore(mTDComputeOutputs[0], ivec2(3 * e, 0), TDOutputSwizzle(sA[0]));
        imageStore(mTDComputeOutputs[0], ivec2(3 * e + 1, 0), TDOutputSwizzle(sB[0]));
        imageStore(mTDComputeOutputs[0], ivec2(3 * e + 2, 0), TDOutputSwizzle(sC[0]));
    }
}
