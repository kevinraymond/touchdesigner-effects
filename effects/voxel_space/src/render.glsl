// touchdesigner-effects (MIT), Voxel Space: the terrain drawn a screen column at a time, as Comanche's Voxel Space
// (NovaLogic, Kyle Freeman, 1992; US patents 5,550,959 and 6,020,893, expired) drew its maps, following Sebastian
// Macke's write-up of it (github.com/s-macke/VoxelSpace, MIT; none of its code or Comanche's maps). Each column's ray
// steps out from the camera, each step a little longer than the last; a step's terrain, projected by its distance,
// draws the column from its top down to the highest point drawn so far (the y-buffer), so nearer hills hide what is
// behind them, and above the last point drawn is the sky.
// Comanche walked the steps one after another. Here one workgroup draws a column: each of its invocations projects
// one step, a running minimum over the steps in shared memory (a scan: W. D. Hillis and G. L. Steele, "Data parallel
// algorithms", CACM 1986) gives the y-buffer after every step, and each pixel finds the first step that reaches it by
// a binary search, since the y-buffer only ever rises. On a slope the pixel takes the terrain's color between that
// step and the one before, where the surface crosses it, so far ground isn't striped by the steps. On a cliff's face
// (the step's top far above where flat ground would put it) it takes the color of the cliff's top, a little coarser,
// as Comanche drew its faces: a face spread the few pixels between the cliff's foot and its top over hundreds of
// rows, and where the depth's edge and the picture's don't quite meet, a dancer's every move swung it between the
// floor's dark and her clothes' light (2 flashes a second more than the clip).
// Every pixel goes through the red guard (lib red_guard.glsl, pasted in front): flown over, the land sweeps its reds
// back and forth, and red flowers that crossed WCAG's saturated-red line once a second in the clip crossed it 3.5 times.
// Inputs: 0 the picture (the colors, eased, mipmapped), 1 terrain.glsl (r height 0-1, g light), 2 flight.glsl (the
// camera). Out: the view, at the picture's size.
layout (local_size_x = 512) in;
uniform vec4 uV;   // x the terrain's height at 1 (world units), y Fog, z Flight (0 Fly, 1 Orbit, 2 Hover), w tan of
                   // half the view's width at Zoom 1
uniform vec4 uZ;   // step k's distance is uZ.x * exp(uZ.y * k) - uZ.z, out to uZ.w

#define STEPS 512
#define WORLD 1024.0
#define SYNC memoryBarrierShared(); barrier()

shared float sTop[STEPS];        // each step's top: rows from the view's top edge
shared float sBuf[2][STEPS];     // the y-buffer after each step, the running minimum of the tops

float dist(int k) {
    return uZ.x * exp(uZ.y * float(k)) - uZ.z;
}

vec2 mirror(vec2 uv) {
    return 1.0 - abs(mod(uv, 2.0) - 1.0);
}

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

bool outside(vec2 uv) {
    return any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)));
}

void main() {
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    int col = int(gl_WorkGroupID.x);
    if (col >= size.x) return;                         // a whole workgroup at once: 1280 are dispatched
    int k = int(gl_LocalInvocationID.x);
    vec4 cam = texelFetch(sTD2DInputs[2], ivec2(0, 0), 0);
    vec4 aux = texelFetch(sTD2DInputs[2], ivec2(1, 0), 0);
    vec4 sky = texelFetch(sTD2DInputs[2], ivec2(2, 0), 0);
    float zoom = texelFetch(sTD2DInputs[2], ivec2(3, 0), 0).w;
    float w = float(size.x), h = float(size.y);
    vec2 world = vec2(WORLD, WORLD * h / w);
    float tanHalf = uV.w / zoom;
    float focal = 0.5 * w / tanHalf;
    vec2 fwd = vec2(sin(cam.w), cos(cam.w)), right = vec2(fwd.y, -fwd.x);
    vec2 dir = fwd + ((float(col) + 0.5) / w * 2.0 - 1.0) * tanHalf * right;
    float alt = cam.z - sky.a;
    float horizon = aux.x * h + (float(col) + 0.5 - 0.5 * w) * tan(aux.y);
    bool island = uV.z > 0.5 && uV.z < 1.5;
    float lod = log2(2.0 * tanHalf / WORLD);           // + log2(distance): the picture's pixels a column spans

    float z = dist(k);
    vec2 uv = (cam.xy + dir * z) / world;
    float ground = 0.0;
    if (!island || !outside(uv))
        ground = textureLod(sTD2DInputs[1], mirror(uv), max(log2(z) + lod - 1.0, 0.0)).r * uV.x;
    float top = horizon + (alt - ground) / z * focal;
    sTop[k] = top;
    sBuf[0][k] = top;
    SYNC;
    int b = 0;
    for (int o = 1; o < STEPS; o <<= 1) {
        float v = sBuf[b][k];
        if (k >= o) v = min(v, sBuf[b][k - o]);
        sBuf[1 - b][k] = v;
        b = 1 - b;
        SYNC;
    }

    vec3 fog = sky.rgb;
    float far = uZ.w;
    float near = far * (1.0 - 0.85 * uV.y);
    for (int y = k; y < size.y; y += STEPS) {
        float row = h - float(y) - 0.5;                // rows from the top
        int lo = 0, hi = STEPS;
        while (lo < hi) {
            int mid = (lo + hi) >> 1;
            if (sBuf[b][mid] <= row) hi = mid; else lo = mid + 1;
        }
        vec3 c;
        if (lo == STEPS) {
            float up = clamp((horizon - row) / h * 1.6, 0.0, 1.0);
            c = mix(fog, fog * 0.45, up);
        } else {
            float d = dist(lo), coarse = 0.0;
            if (lo > 0) {
                float t0 = sTop[lo - 1], t1 = sTop[lo];
                float even = abs(t1 - horizon) * (d / dist(lo - 1) - 1.0);   // the rows flat ground would span
                if (t0 - t1 > 2.0 * even + 2.0)
                    coarse = 1.5;
                else
                    d = mix(dist(lo - 1), d, clamp((t0 - row) / max(t0 - t1, 1e-4), 0.0, 1.0));
            }
            vec2 at = (cam.xy + dir * d) / world;
            if (island && outside(at)) {
                c = fog * 0.4;                         // the sea around the island
            } else {
                float l = max(log2(d) + lod, 0.0) + coarse;
                vec2 m = mirror(at);
                c = textureLod(sTD2DInputs[0], m, l).rgb * textureLod(sTD2DInputs[1], m, max(l - 1.0, 0.0)).g;
            }
            c = mix(c, fog, smoothstep(near, far, d));
        }
        c = toSRGB(redGuard(toLinear(clamp(c, 0.0, 1.0))));
        imageStore(mTDComputeOutputs[0], ivec2(col, y), TDOutputSwizzle(vec4(c, 1.0)));
    }
}
