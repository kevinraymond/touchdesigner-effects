// Point Cloud (touchdesigner-effects, MIT). One instance per grid point: a square, the dot. For
// Points and Glow it faces the camera; for Surface it lies in the surface, spanning the steps to
// the next points, so neighbors overlap into one skin (Botsch, Hornung, Zwicker, Kobbelt 2005).
// The camera stays where the picture fills the frame; the cloud turns around its middle instead,
// and the music moves it: a beat deepens it along the camera's rays, a build scatters it, a drop
// blows it apart and lets it settle back.
uniform sampler2D sPos;     // pos.glsl: xyz, w how far along its ray (0: left out)
uniform sampler2D sColor;   // the picture
uniform sampler2D sPivot;   // pivot.glsl: the cloud's middle
uniform vec4 uDot;     // x size in grid steps (before the music's),  y the grid step (1 / rows), z a next point this share farther lies across an edge, w jitter
uniform vec4 uView;    // x turn (radians, about the vertical), y tilt (radians), z camera distance (share of the start), w the camera's distance to the picture plane
uniform vec4 uMove;    // x how much deeper on the beat (0: as is), y scatter (the build), z burst (the drop, 0-1), w seconds
uniform vec4 uLook;    // x color (0 picture, 1 depth, 2 white), y brightness, z pass (0 Points, 1 Glow, 2 Surface, 3 Surface's depth pass), w Depth
uniform vec4 uGain;    // x how much bigger the music makes the dots (loudness, the beat's pop)
out Vertex {
    vec3 color;
    vec2 uv;
    flat float keep;
} oVert;

// The surface's depth pass draws each splat this share of its distance farther away, so splats on
// one surface all pass the depth test and blend, while those on a surface behind fail it.
#define SPLAT_PUSH 0.03
#define ORANGE vec3(1.0, 0.55, 0.12)
#define BLUE vec3(0.15, 0.45, 1.0)

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

// pcg3d: the same for three (Jarzynski and Olano 2020).
uvec3 pcg3d(uvec3 v) {
    v = v * 1664525u + 1013904223u;
    v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
    v ^= v >> 16u;
    v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
    return v;
}

vec2 cell_uv(ivec2 p, ivec2 size) {   // as in pos.glsl
    vec2 j = vec2(pcg2d(uvec2(p))) / 4294967295.0 - 0.5;
    return (vec2(p) + 0.5 + j * uDot.w) / vec2(size);
}

vec3 dice(ivec2 p) {                  // three more fixed random numbers per point, -0.5..0.5
    return vec3(pcg3d(uvec3(uvec2(p), 7u))) / 4294967295.0 - 0.5;
}

// The step to a next point, unless it was left out or lies across an edge: then a flat step.
vec3 step_to(vec4 pos, ivec2 q, float dir, vec3 flat_) {
    vec4 o = texelFetch(sPos, q, 0);
    if (o.w <= 0.0 || abs(o.w - pos.w) / pos.w > uDot.z)
        return flat_;
    return (o.xyz - pos.xyz) * dir;
}

void main() {
    int id = TDInstanceID();
    ivec2 size = textureSize(sPos, 0);
    ivec2 p = ivec2(id % size.x, id / size.x);
    vec4 pos = texelFetch(sPos, p, 0);
    vec3 corner = TDPos();            // the square's corner, -0.5..0.5
    oVert.uv = corner.xy * 2.0;
    oVert.keep = pos.w;
    if (pos.w <= 0.0) {               // left out: a square of no size, nothing drawn
        gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
        return;
    }
    int pass = int(uLook.z + 0.5);
    vec3 cam = vec3(0.0, 0.0, uView.w);
    vec3 mid = texelFetch(sPivot, ivec2(0), 0).rgb;

    // The beat: farther along each ray from the camera, the farther the point already is.
    float s = pos.w, deeper = (1.0 + (s - 1.0) * (1.0 + uMove.x)) / s;
    vec3 P = cam + (pos.xyz - cam) * deeper;
    // The build: each point wanders off its place; the drop: everything flies out from the middle.
    vec3 r = dice(p);
    P += uMove.y * 0.06 * vec3(sin(P.y * 9.0 + uMove.w * 1.3 + r.x * 6.3), sin(P.z * 9.0 + uMove.w * 1.1 + r.y * 6.3),
                              sin(P.x * 9.0 + uMove.w * 0.9 + r.z * 6.3));
    P = mid + (P - mid) * (1.0 + 0.5 * uMove.z) + r * 0.15 * uMove.z;
    // Turn the cloud around its middle, which is the camera going round it, then move the camera
    // in or out along its line to the middle.
    float cy = cos(uView.x), sy = sin(uView.x), cx = cos(uView.y), sx = sin(uView.y);
    mat3 turn = mat3(1.0, 0.0, 0.0, 0.0, cx, sx, 0.0, -sx, cx) * mat3(cy, 0.0, -sy, 0.0, 1.0, 0.0, sy, 0.0, cy);
    P = mid + turn * (P - mid) + (cam - mid) * (1.0 - uView.z);

    vec3 color = texture(sColor, cell_uv(p, size)).rgb;
    if (uLook.x > 1.5)
        color = vec3(1.0);
    else if (uLook.x > 0.5)
        color = mix(ORANGE, BLUE, clamp((s - 1.0) / max(uLook.w, 0.001), 0.0, 1.0));
    // Glow adds its dots up, so a bigger dot would be a brighter one: a beat's pop would flash. Its
    // dots keep their light as they grow, spread thinner.
    oVert.color = color * uLook.y / (pass == 1 ? uGain.x * uGain.x : 1.0);

    vec4 camP;
    if (pass < 2) {
        camP = uTDMats[TDCameraIndex()].cam * vec4(P, 1.0);
        camP.xy += corner.xy * uDot.x * uGain.x * uDot.y * s * deeper;
    } else {
        int rx = p.x + 1 < size.x ? 1 : -1, uy = p.y + 1 < size.y ? 1 : -1;
        float flat_ = uDot.y * s;
        vec3 du = step_to(pos, p + ivec2(rx, 0), float(rx), vec3(flat_, 0.0, 0.0));
        vec3 dv = step_to(pos, p + ivec2(0, uy), float(uy), vec3(0.0, flat_, 0.0));
        camP = uTDMats[TDCameraIndex()].cam * vec4(P + turn * (du * corner.x + dv * corner.y) * uDot.x * uGain.x * deeper, 1.0);
        if (pass == 3)
            camP.xyz *= 1.0 + SPLAT_PUSH;
    }
    gl_Position = uTDMats[TDCameraIndex()].proj * camP;
#ifdef TD_PICKING_ACTIVE
    TDWritePickingValues();
#endif
}
