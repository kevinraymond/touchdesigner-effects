// touchdesigner-effects (MIT), Words: the subject's outline on the grid, where the distance field starts: a cell is
// on it when it and a neighbor (left, right, below, above) lie on different sides of the subject's edge.
// Input: 0 the cells (r the subject's share). Out: rg the cell itself when it is on the outline, else -1; a 1.
out vec4 fragColor;

bool inside(ivec2 p) {
    ivec2 n = textureSize(sTD2DInputs[0], 0);
    return texelFetch(sTD2DInputs[0], clamp(p, ivec2(0), n - 1), 0).r > 0.5;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    bool here = inside(p);
    bool edge = inside(p + ivec2(1, 0)) != here || inside(p - ivec2(1, 0)) != here ||
                inside(p + ivec2(0, 1)) != here || inside(p - ivec2(0, 1)) != here;
    fragColor = edge ? vec4(vec2(p), 0.0, 1.0) : vec4(-1.0, -1.0, 0.0, 1.0);
}
