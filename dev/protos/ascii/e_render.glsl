// DEV ONLY (ASCII round 1), variant E: audio. Luminance picks a glyph from one of three sets
// (symbols, digits, letters; each ordered by how many pixels it lights, so a swap keeps the
// picture's brightness); each beat moves to the next set and briefly steepens the contrast.
// Ink runs from blue (dark) to orange (bright), brightness rising with it, on a dark paper.
uniform float uScale;
#define STATS 1
//@LEVELS
uniform float uBeat;    // 0..1 envelope (Trigger CHOP, re-trigger delay = the flash interval)
uniform float uSet;     // beat count (Count CHOP)
uniform vec3 uLow;
uniform vec3 uHigh;
uniform vec3 uPaper;
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
    l = mix(l, smoothstep(0.15, 0.85, l), uBeat);
    int s = int(mod(uSet, 3.0));
    int n = SET_LEN[s];
    int g = SETS[SET_START[s] + clamp(int(l * float(n)), 0, n - 1)];
    vec3 col = mix(uLow, uHigh, smoothstep(0.2, 0.8, l)) * (0.3 + 0.7 * l) * (1.0 + 0.3 * uBeat);
    fragColor = TDOutputSwizzle(vec4(mix(uPaper, col, glyph(g, fp)), 1.0));
}
