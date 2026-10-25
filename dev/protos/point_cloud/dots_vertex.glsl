// Point cloud prototype. One instance per grid point: a square, the dot, either facing the camera
// (a billboard) or lying in the surface (a disc spanning the step to the next points).
uniform sampler2D sPos;     // pos.glsl: xyz, w how far along its ray (0 dropped)
uniform sampler2D sColor;   // the picture
uniform vec4 uDot;          // x size (in grid steps), y 0 billboard / 1 disc, z the grid step (1 / grid height), w Edge Cut
uniform vec4 uPass;         // x 1: the splats' depth pass, pushed back by y (a share of the distance); z jitter
out Vertex {
    vec3 color;
    vec2 uv;
    flat float keep;
} oVert;

// The step to a neighbor, unless it was dropped or lies across an edge: then a flat step.
vec3 step_to(vec4 pos, ivec2 q, float sign_, vec3 flat_) {
    vec4 o = texelFetch(sPos, q, 0);
    if (o.w <= 0.0 || abs(o.w - pos.w) / pos.w > max(uDot.w, 0.02))
        return flat_;
    return (o.xyz - pos.xyz) * sign_;
}

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

vec2 cell_uv(ivec2 p, ivec2 size) {   // as in pos.glsl
    vec2 j = vec2(pcg2d(uvec2(p))) / 4294967295.0 - 0.5;
    return (vec2(p) + 0.5 + j * uPass.z) / vec2(size);
}

void main() {
    int id = TDInstanceID();
    ivec2 size = textureSize(sPos, 0);
    ivec2 p = ivec2(id % size.x, id / size.x);
    vec4 pos = texelFetch(sPos, p, 0);
    oVert.color = texture(sColor, cell_uv(p, size)).rgb;
    vec3 corner = TDPos();      // the square's corner, -0.5..0.5
    oVert.uv = corner.xy * 2.0;
    oVert.keep = pos.w;
    vec4 camP;
    if (uDot.y < 0.5 || pos.w <= 0.0) {
        camP = uTDMats[TDCameraIndex()].cam * vec4(pos.xyz, 1.0);
        camP.xy += corner.xy * uDot.x * uDot.z * pos.w;
    } else {
        int rx = p.x + 1 < size.x ? 1 : -1, uy = p.y + 1 < size.y ? 1 : -1;
        float flat_ = uDot.z * pos.w;
        vec3 du = step_to(pos, p + ivec2(rx, 0), float(rx), vec3(flat_, 0.0, 0.0));
        vec3 dv = step_to(pos, p + ivec2(0, uy), float(uy), vec3(0.0, flat_, 0.0));
        camP = uTDMats[TDCameraIndex()].cam * vec4(pos.xyz + (du * corner.x + dv * corner.y) * uDot.x, 1.0);
    }
    if (uPass.x > 0.5)
        camP.xyz *= 1.0 + uPass.y;   // farther along the same ray: splats within this of the front blend
    gl_Position = uTDMats[TDCameraIndex()].proj * camP;
#ifdef TD_PICKING_ACTIVE
    TDWritePickingValues();
#endif
}
