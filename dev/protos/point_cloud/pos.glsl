// Point cloud prototype. Every grid point's place in 3D, from the depth.
// Inputs: 0 the depth, brighter nearer (sampled at the grid's resolution).
// Out: xyz the point, w how far along its ray it is (its size factor; 0: dropped, an edge).
// The picture is a plane one unit tall at z = 0, seen from the original camera at (0, 0, uCam.x);
// a point on its ray at nearness n lies along(n) times as far from the camera as the plane.
uniform vec4 uGeo;     // x aspect, y Depth, z Edge Cut (0 off), w edges: 0 dropped, 1 snapped to a side
uniform vec4 uSmooth;  // x the nearness difference still smoothed over (0: no smoothing), y radius in grid steps
uniform vec4 uCam;     // x the original camera's distance to the picture plane, y jitter (0..1 of a grid step)
out vec4 fragColor;

// Where in its grid cell a point samples the picture: off the cell's middle by a fixed random
// amount, so the dots don't line up in rows and columns (which shows as moire from the side).
// dots_vertex.glsl samples the color at the same place.
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
    return (vec2(p) + 0.5 + j * uCam.y) / vec2(size);
}

float nearness(ivec2 p, ivec2 size) {
    return texture(sTD2DInputs[0], cell_uv(clamp(p, ivec2(0), size - 1), size)).r;
}

// How far along its ray: 1 on the plane (the nearest), 1 + Depth at the farthest. Nearness is
// taken as disparity (1 / distance), which is what depth estimators give.
float along(float n) {
    return 1.0 / mix(1.0 / (1.0 + uGeo.y), 1.0, n);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 size = ivec2(uTDOutputInfo.res.zw);
    vec2 uv = cell_uv(p, size);
    float n0 = nearness(p, size), n = n0;
    // An 8-bit depth climbs in steps of 1/255, which show as terraces once seen from the side:
    // smooth over small differences (a bilateral filter) but never across an edge.
    if (uSmooth.x > 0.0) {
        int r = int(uSmooth.y);
        float sum = 0.0, wsum = 0.0;
        for (int y = -r; y <= r; y++)
            for (int x = -r; x <= r; x++) {
                float m = nearness(p + ivec2(x, y), size);
                float d = (m - n0) / uSmooth.x;
                float w = exp(-0.5 * d * d - 2.0 * float(x * x + y * y) / float(r * r + 1));
                sum += w * m;
                wsum += w;
            }
        n = sum / wsum;
    }
    // A point that lies much nearer or farther than a next point sits on an edge between two
    // things: its depth is a blend of both, and drawn there it streaks from one to the other. Drop
    // it, or put it on whichever side it is closer to: the nearest or farthest within 3 steps,
    // past the blend (a depth estimator's edges are soft). Only next points count as an edge, so
    // a floor that falls away steeply, a little each step, doesn't.
    float s = along(n);
    float jump = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            jump = max(jump, abs(along(nearness(p + ivec2(x, y), size)) - along(n0)));
    bool edge = uGeo.z > 0.0 && jump / s > uGeo.z;
    if (edge && uGeo.w > 0.5) {
        float lo = n0, hi = n0;
        for (int y = -3; y <= 3; y++)
            for (int x = -3; x <= 3; x++) {
                float m = nearness(p + ivec2(x, y), size);
                lo = min(lo, m);
                hi = max(hi, m);
            }
        s = along(n0 - lo < hi - n0 ? lo : hi);
        edge = false;
    }
    vec3 q = vec3((uv.x - 0.5) * uGeo.x, uv.y - 0.5, 0.0);
    vec3 cam = vec3(0.0, 0.0, uCam.x);
    fragColor = vec4(cam + (q - cam) * s, edge ? 0.0 : s);
}
