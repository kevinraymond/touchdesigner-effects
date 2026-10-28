// touchdesigner-effects (MIT), Words: the subject on the grid, steadied. A depth map, a mask or a key flickers at its
// edges from frame to frame; words judged against it would come and go there, and Lines' lines, which follow its
// outline, would shake. So the subject's share of each cell is smoothed over its neighbors (1 2 1 across and down)
// and eased over time.
// Inputs: 0 the cells (cells.glsl), 1 this pass's last frame (a Feedback TOP). Out: r the subject's share, steadied;
// g, b the cells' detail and brightness, as they are.
uniform vec4 uEase;   // x how far toward the new share this frame (1 - e^(-step / ease))
out vec4 fragColor;
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 n = textureSize(sTD2DInputs[0], 0) - 1;
    float s = 0.0;
    for (int j = -1; j <= 1; j++)
    for (int i = -1; i <= 1; i++)
        s += texelFetch(sTD2DInputs[0], clamp(p + ivec2(i, j), ivec2(0), n), 0).r * float((2 - abs(i)) * (2 - abs(j)));
    s /= 16.0;
    vec4 c = texelFetch(sTD2DInputs[0], p, 0);
    float was = texture(sTD2DInputs[1], vUV.st).r;
    fragColor = vec4(mix(was, s, uEase.x), c.g, c.b, 1.0);
}
