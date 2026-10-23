// DEV ONLY (ASCII round 1), variant C: the 5 x 7 bitmap font defined in this shader, each glyph
// in its cell's own hue (brightness from luminance) over a dim wash of the same color.
uniform float uScale;      // screen pixels per font pixel; a cell is 6 x 9 font pixels
#define STATS 1
//@LEVELS
uniform float uPaperMix;   // how much of the cell's color tints the space around its glyph
out vec4 fragColor;
//@FONT
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 cs = vec2(6.0, 9.0) * uScale;
    vec2 p = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
    ivec2 cell = ivec2(floor(p / cs));
    ivec2 fp = ivec2(floor((p - vec2(cell) * cs) / uScale)) - ivec2(0, 1);
    vec4 c = texelFetch(sTD2DInputs[0], cell, 0);
    float l = level(c.a);
    int g = RAMP[clamp(int(l * float(RAMP.length())), 0, RAMP.length() - 1)];
    float m = max(max(c.r, c.g), max(c.b, 1e-3));
    vec3 fg = c.rgb / m * (0.3 + 0.7 * sqrt(l));
    fragColor = TDOutputSwizzle(vec4(mix(c.rgb * uPaperMix, fg, glyph(g, fp)), 1.0));
}
