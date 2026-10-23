// DEV ONLY (ASCII round 1), variant B, pass 3: glyphs drawn as antialiased strokes (distance to
// line segments), no font. Cells with enough edge get the edge's direction, | \ - /, in orange;
// the rest get a luminance ramp, . : + x * o # @, in blue.
uniform vec2 uCell;
#define STATS 1
//@LEVELS
uniform float uMinEdge;   // share of the cell that must vote for one direction
uniform float uWidth;     // stroke half-width in pixels
uniform vec3 uEdgeInk;
uniform vec3 uFillInk;
uniform vec3 uPaper;
out vec4 fragColor;

float seg(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0));
}
// distance in pixels from p (pixels from the cell's bottom-left) to glyph g; cs is the cell size
float strokes(int g, vec2 p, vec2 cs) {
    vec2 q = p / cs;                       // 0..1 in the cell
    float d = 1e6;
    float r = 0.09 * cs.x;
    #define S(ax, ay, bx, by) d = min(d, seg(p, vec2(ax, ay) * cs, vec2(bx, by) * cs))
    #define DOT(cx, cy, rad) d = min(d, length(p - vec2(cx, cy) * cs) - (rad))
    #define RING(cx, cy, rad) d = min(d, abs(length(p - vec2(cx, cy) * cs) - (rad)))
    if (g == 0) S(0.5, 0.06, 0.5, 0.94);                       // |
    else if (g == 1) S(0.1, 0.94, 0.9, 0.06);                  // backslash
    else if (g == 2) S(0.04, 0.5, 0.96, 0.5);                  // -
    else if (g == 3) S(0.1, 0.06, 0.9, 0.94);                  // /
    else if (g == 10) DOT(0.5, 0.2, r);                        // .
    else if (g == 11) { DOT(0.5, 0.3, r); DOT(0.5, 0.68, r); } // :
    else if (g == 12) { S(0.2, 0.5, 0.8, 0.5); S(0.5, 0.3, 0.5, 0.7); }               // +
    else if (g == 13) { S(0.22, 0.3, 0.78, 0.7); S(0.22, 0.7, 0.78, 0.3); }           // x
    else if (g == 14) { S(0.2, 0.5, 0.8, 0.5); S(0.5, 0.25, 0.5, 0.75); S(0.25, 0.32, 0.75, 0.68); S(0.25, 0.68, 0.75, 0.32); } // *
    else if (g == 15) RING(0.5, 0.42, 0.3 * cs.x);             // o
    else if (g == 16) { S(0.36, 0.15, 0.36, 0.85); S(0.64, 0.15, 0.64, 0.85); S(0.12, 0.38, 0.88, 0.38); S(0.12, 0.62, 0.88, 0.62); } // #
    else if (g == 17) { RING(0.5, 0.5, 0.4 * cs.x); DOT(0.5, 0.5, 0.15 * cs.x); S(0.9, 0.5, 0.9, 0.3); } // @
    return d;
}
void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 p = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
    ivec2 cell = ivec2(floor(p / uCell));
    vec2 local = vec2(gl_FragCoord.x - float(cell.x) * uCell.x, uCell.y - (p.y - float(cell.y) * uCell.y));
    vec4 c = texelFetch(sTD2DInputs[0], cell, 0);
    float l = level(c.r);
    bool isEdge = c.b > uMinEdge;
    int g = isEdge ? int(c.g + 0.5) : (l < 0.08 ? -1 : 10 + clamp(int((l - 0.08) / 0.92 * 8.0), 0, 7));
    float d = g < 0 ? 1e6 : strokes(g, local, uCell);
    float ink = 1.0 - smoothstep(uWidth - 0.6, uWidth + 0.6, d);
    vec3 col = isEdge ? uEdgeInk * (0.55 + 0.45 * l) : uFillInk * (0.35 + 0.65 * l);
    fragColor = TDOutputSwizzle(vec4(mix(uPaper, col, ink), 1.0));
}
