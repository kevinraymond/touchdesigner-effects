// Point Cloud (touchdesigner-effects, MIT). Every grid point's place in 3D, from the depth.
// The picture is a plane one unit tall at z = 0, seen from the camera at (0, 0, uCam.x), where it
// fills the frame. A point lies on the ray from the camera through its spot on the picture,
// along(n) times as far as the plane: 1 for the nearest (on the plane), 1 + Depth for the farthest.
// So from the camera the cloud is the picture, and anywhere else it shows the depth.
// Inputs: 0 the depth at the grid's size (near_pick.glsl: r nearness, g how much had a reading,
// b 1 when input 1's brightness stands in for a depth input 3 doesn't carry); 1 which points to
// keep (white: all; else the subject, depth_find.glsl, unless the brightness stands in).
// Out: xyz the point; w how far along its ray (dots grow with it, so they cover the picture alike
// near and far), 0 where the point is left out (no reading, or not the subject).
uniform vec4 uGeo;     // x the picture's aspect, y Depth, z 1 when input 3 holds distance (a depth camera), w jitter
uniform vec4 uSmooth;  // x nearness differences up to about this are smoothed over, y radius in grid steps,
                       // z a next point this share farther or nearer lies across an edge
uniform vec4 uCam;     // x the camera's distance to the picture plane
out vec4 fragColor;
bool g_guess;          // no depth on input 3: the brightness stands in, read as nearness, and every point stays

// Where in its grid cell a point samples the picture: off the cell's middle by a fixed random
// amount, so the dots don't line up in rows and columns (seen from the side, rows of dots make
// moire). dot_vertex.glsl samples the color at the same place.
// pcg2d: two random numbers from two, in a few multiplies (Jarzynski and Olano, "Hash Functions
// for GPU Rendering", JCGT 2020, their pick for speed against quality).
uvec2 pcg2d(uvec2 v) {
    v = v * 1664525u + 1013904223u;
    v.x += v.y * 1664525u; v.y += v.x * 1664525u;
    v ^= v >> 16u;
    v.x += v.y * 1664525u; v.y += v.x * 1664525u;
    v ^= v >> 16u;
    return v;
}

vec2 cell_uv(ivec2 p, ivec2 size) {
    vec2 j = vec2(pcg2d(uvec2(p))) / 4294967295.0 - 0.5;
    return (vec2(p) + 0.5 + j * uGeo.w) / vec2(size);
}

// The depth at a grid point's own cell: the point itself reads it at its jittered spot, its
// neighbors (for smoothing and edges) at their middles, a texel each, which costs far less.
vec2 depth_at(ivec2 p, ivec2 size) {
    return texelFetch(sTD2DInputs[0], clamp(p, ivec2(0), size - 1), 0).rg;
}

// How far along its ray. Depth estimators give disparity (1 / distance), so their nearness maps to
// distance through its inverse; a depth camera's distance is spread evenly.
float along(float n) {
    if (uGeo.z > 0.5 && !g_guess)
        return 1.0 + uGeo.y * (1.0 - n);
    return 1.0 / mix(1.0 / (1.0 + uGeo.y), 1.0, n);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 size = ivec2(uTDOutputInfo.res.zw);
    g_guess = texelFetch(sTD2DInputs[0], ivec2(0), 0).b > 0.5;
    vec2 uv = cell_uv(p, size);
    vec2 here = texture(sTD2DInputs[0], uv).rg;
    float n0 = here.r, n = n0;
    // An 8-bit depth climbs in steps of 1/255, which show as terraces from the side: smooth over
    // small differences (a bilateral filter) but never across an edge.
    int r = int(uSmooth.y);
    float sum = 0.0, wsum = 0.0;
    for (int y = -r; y <= r; y++)
        for (int x = -r; x <= r; x++) {
            vec2 m = depth_at(p + ivec2(x, y), size);
            if (m.g < 0.5)
                continue;
            float d = (m.r - n0) / uSmooth.x;
            float w = exp(-0.5 * d * d - 2.0 * float(x * x + y * y) / float(r * r + 1));
            sum += w * m.r;
            wsum += w;
        }
    if (wsum > 0.0)
        n = sum / wsum;
    // A point much nearer or farther than a next point sits on an edge between two things: its
    // depth blends both, and drawn there it would streak from one to the other. Put it on the side
    // it is closer to, the nearest or farthest reading within 3 steps (a depth estimator's edges are
    // soft, a few steps wide). Only next points count, so a floor that falls away steeply, a little
    // each step, stays as it is.
    float s0 = along(n0), jump = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++) {
            vec2 m = depth_at(p + ivec2(x, y), size);
            if (m.g >= 0.5)
                jump = max(jump, abs(along(m.r) - s0));
        }
    float s = along(n);
    if (jump / s0 > uSmooth.z) {
        float lo = n0, hi = n0;
        for (int y = -3; y <= 3; y++)
            for (int x = -3; x <= 3; x++) {
                vec2 m = depth_at(p + ivec2(x, y), size);
                if (m.g >= 0.5) {
                    lo = min(lo, m.r);
                    hi = max(hi, m.r);
                }
            }
        s = along(n0 - lo < hi - n0 ? lo : hi);
    }
    bool keep = here.g >= 0.5 && (g_guess || texture(sTD2DInputs[1], uv).r > 0.5);
    vec3 q = vec3((uv.x - 0.5) * uGeo.x, uv.y - 0.5, 0.0);
    vec3 cam = vec3(0.0, 0.0, uCam.x);
    fragColor = vec4(cam + (q - cam) * s, keep ? s : 0.0);
}
