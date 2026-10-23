// DEV ONLY (ASCII round 1). One output pixel per glyph cell: the cell's mean color (rgb) and
// luminance (a). Output texel (x, y) is column x, row y counted from the top of the picture.
uniform vec2 uCell;   // cell size in pixels of the output picture
out vec4 fragColor;
void main() {
    vec2 src = uTD2DInfos[0].res.zw;
    vec2 origin = floor(gl_FragCoord.xy) * uCell;   // the cell's top-left corner, pixels from the top-left
    vec3 sum = vec3(0.0);
    const int N = 4;
    for (int j = 0; j < N; j++)
        for (int i = 0; i < N; i++) {
            vec2 p = origin + (vec2(i, j) + 0.5) / float(N) * uCell;
            sum += texture(sTD2DInputs[0], vec2(p.x, src.y - p.y) / src).rgb;
        }
    vec3 c = sum / float(N * N);
    fragColor = TDOutputSwizzle(vec4(c, dot(c, vec3(0.2126, 0.7152, 0.0722))));
}
