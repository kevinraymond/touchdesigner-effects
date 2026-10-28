// touchdesigner-effects (MIT), Words: the subject's signed distance field, in cells: how far each cell is from the
// subject's outline, negative inside. Cloud fills it deepest first (ShapeWordle), and Lines' lines are its level sets.
// Taken straight from the jump flood it has creases along the shape's middles and every jag of the outline; smoothed
// over 5 x 5 cells (a Gaussian, sigma 1.25 cells) Lines' lines round them off.
// Lines' lines move only as fast as uSlew allows (a line's spacing a second): its lines are about as far apart as the
// flash test's cells, so lines sweeping through a part of the picture swing it between text and the gaps between lines,
// a flash for each line that passes; after a cut too, they crawl to their new places. The first frame, and a subject
// appearing or vanishing (a cell going from no outline to one or back), take the field as it is.
// Inputs: 0 each cell's nearest outline cell (jfa.glsl), 1 the subject (region.glsl), 2 this pass's last frame (a
// Feedback TOP). Out: r the distance smoothed and slowed (Lines), g smoothed (Cloud), a 1. With
// no outline at all, every cell is FAR.
#define FAR 1000.0
uniform vec4 uSlew;   // x the most a cell's distance may change this frame (cells)
out vec4 fragColor;

float signedAt(ivec2 c) {
    ivec2 n = textureSize(sTD2DInputs[0], 0) - 1;
    c = clamp(c, ivec2(0), n);
    vec2 s = texelFetch(sTD2DInputs[0], c, 0).rg;
    float d = s.x < 0.0 ? FAR : min(distance(s, vec2(c)) + 0.5, FAR);
    return texelFetch(sTD2DInputs[1], c, 0).r > 0.5 ? -d : d;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float sum = 0.0, w = 0.0;
    for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++) {
        float g = exp(-float(i * i + j * j) / (2.0 * 1.5625));
        sum += g * signedAt(p + ivec2(i, j));
        w += g;
    }
    float now = sum / w;
    vec4 was = texelFetch(sTD2DInputs[2], p, 0);
    bool snap = was.a < 0.5 || textureSize(sTD2DInputs[2], 0) != textureSize(sTD2DInputs[0], 0) ||
                abs(was.r) > 0.5 * FAR || abs(now) > 0.5 * FAR;
    float slow = snap ? now : was.r + clamp(now - was.r, -uSlew.x, uSlew.x);
    fragColor = vec4(slow, now, 0.0, 1.0);
}
