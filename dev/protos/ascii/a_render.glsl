// DEV ONLY (ASCII round 1), variant A: luminance picks a glyph from an atlas a Text TOP drew
// (input 1: one cell-sized slot per glyph, darkest first); one ink color on a dark paper.
uniform vec2 uCell;
#define STATS 2
//@LEVELS
uniform vec3 uInk;
uniform vec3 uPaper;
uniform float uCount;   // glyphs in the atlas
out vec4 fragColor;
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
    ivec2 cell = ivec2(floor(p / uCell));
    ivec2 local = ivec2(floor(p - vec2(cell) * uCell));
    vec4 c = texelFetch(sTD2DInputs[0], cell, 0);
    float l = level(c.a);
    int n = int(uCount);
    int g = clamp(int(l * float(n)), 0, n - 1);
    ivec2 cs = ivec2(uCell);
    float ink = texelFetch(sTD2DInputs[1], ivec2(g * cs.x + local.x, cs.y - 1 - local.y), 0).r;
    vec3 col = mix(uPaper, uInk * (0.45 + 0.55 * l), ink);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
