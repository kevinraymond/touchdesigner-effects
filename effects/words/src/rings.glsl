// touchdesigner-effects (MIT), Words: Lines' lines, ready to read: the slowed distance field (field.glsl's r) and its
// slope, per cell, so the layout reads where a word stands and which way its line runs with one filtered read
// (bilinear between the cells' middles) instead of a dozen.
// Input: 0 the field. Out: r the distance (cells, negative inside), g, b its slope across and down (cells per cell), a 1.
out vec4 fragColor;
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 n = textureSize(sTD2DInputs[0], 0) - 1;
    float l = texelFetch(sTD2DInputs[0], clamp(p - ivec2(1, 0), ivec2(0), n), 0).r;
    float r = texelFetch(sTD2DInputs[0], clamp(p + ivec2(1, 0), ivec2(0), n), 0).r;
    float d = texelFetch(sTD2DInputs[0], clamp(p - ivec2(0, 1), ivec2(0), n), 0).r;
    float u = texelFetch(sTD2DInputs[0], clamp(p + ivec2(0, 1), ivec2(0), n), 0).r;
    fragColor = vec4(texelFetch(sTD2DInputs[0], p, 0).r, 0.5 * (r - l), 0.5 * (u - d), 1.0);
}
