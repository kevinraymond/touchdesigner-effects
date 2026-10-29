// touchdesigner-effects (MIT), Temporal Resonator: the background, what isn't moving, which the string's plucks are
// measured from. A running approximate median (McFarlane and Schofield, 1995): each frame every pixel steps toward the
// picture by at most a fixed amount, so it settles on the value the pixel holds most of the time, and someone walking
// through leaves no trace, where a running average would keep a faint copy of them that came back as a dark echo
// (dev/protos/temporal_resonator/offline.py, board #4717). It starts as the picture whenever the string starts again.
// Inputs: 0 the picture, 1 this pass's previous output (Feedback TOP: alpha 0 on its first frame), 2 the stamp
// (stamp.glsl).
// Out: rgb the background, a 1.
uniform vec4 uB;   // x how far the background may move in a second (0-1 of the range)
out vec4 fragColor;
void main() {
    vec3 x = texture(sTD2DInputs[0], vUV.st).rgb;
    vec4 prev = texture(sTD2DInputs[1], vUV.st);
    vec4 st = texelFetch(sTD2DInputs[2], ivec2(0, 0), 0);
    float step = uB.x * texelFetch(sTD2DInputs[2], ivec2(1, 0), 0).r;
    vec3 bg = (st.b > 0.5 || prev.a < 0.5) ? x : prev.rgb + clamp(x - prev.rgb, -step, step);
    fragColor = vec4(bg, 1.0);
}
