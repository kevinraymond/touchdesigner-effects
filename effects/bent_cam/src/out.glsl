// Bent Cam (touchdesigner-effects, MIT). On the way out the camera's small picture is scaled up to the input's
// size, as the app on the computer showing it does, and Mirror can tile it: Left-Right mirrors the left half
// onto the right, Four Ways mirrors the top-left quarter into the other three, and Kaleidoscope folds it into
// Segments mirrored wedges around the middle. Last, the red guard on every pixel.
// Inputs: 0 the picture (for the output's size), 1 the camera's picture (idct). Out: R'G'B'.
uniform vec4 uOut;    // x Mirror (0 Off, 1 Left-Right, 2 Four Ways, 3 Kaleidoscope), y Segments
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    int m = int(uOut.x + 0.5);
    if (m == 1) uv.x = 0.5 - abs(uv.x - 0.5);
    else if (m == 2) uv = vec2(0.5 - abs(uv.x - 0.5), 0.5 + abs(uv.y - 0.5));
    else if (m == 3) {
        vec2 res = uTDOutputInfo.res.zw;
        vec2 d = (uv - 0.5) * vec2(res.x / res.y, 1.0);
        float seg = 2.0 * PI / max(uOut.y, 1.0);
        float a = mod(atan(d.y, d.x) - 0.5 * PI + 0.5 * seg, seg);   // the wedge pointing up is the first
        a = abs(a - 0.5 * seg) + 0.5 * PI;
        uv = 0.5 + length(d) * vec2(cos(a), sin(a)) / vec2(res.x / res.y, 1.0);
        uv = 1.0 - abs(1.0 - mod(uv, 2.0));                     // beyond the edges, mirrored back in
    }
    vec3 c = pow(max(texture(sTD2DInputs[1], uv).rgb, 0.0), vec3(2.2));
    fragColor = vec4(pow(redGuard(c), vec3(1.0 / 2.2)), 1.0);
}
