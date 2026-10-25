// Point Cloud (touchdesigner-effects, MIT). What the cloud turns around: the kept points' middle,
// eased so it glides as the picture changes rather than jumping. Kept on the GPU (no CHOP reads it),
// where dot_vertex.glsl samples it.
// Inputs: 0 the kept points' average (pivot_in.glsl through an Analyze TOP); 1 this TOP's last frame.
// Out: rgb the middle; a 1 once there is one.
uniform vec4 uPivot;   // x the seconds since last frame, y how long it takes to settle (s)
out vec4 fragColor;

void main() {
    vec4 avg = texelFetch(sTD2DInputs[0], ivec2(0), 0);
    vec4 last = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    if (avg.a <= 0.0) {          // nothing kept: stay put
        fragColor = last;
        return;
    }
    vec3 now = avg.rgb / avg.a;
    fragColor = last.a < 0.5 ? vec4(now, 1.0) : vec4(mix(last.rgb, now, 1.0 - exp(-uPivot.x / uPivot.y)), 1.0);
}
