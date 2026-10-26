// Reaction-Diffusion (touchdesigner-effects, MIT): the picture's darkest and brightest, eased over uX.y seconds, one
// pixel. where.glsl stretches the picture's brightness between them, so a gray river comes out as a picture in lines
// rather than an even maze, while a dark stage keeps its black. They are read from a 16 x 9 grid of a small mipmap
// level of the picture (Input Smoothness Mipmap), each sample the mean of a patch about a sixteenth of the picture
// across, which follows its large shapes and leaves out fine texture and small highlights. Easing them keeps a cut
// or a flash in the input from swinging the whole pattern at once.
// It also counts the seconds since the pattern started (on load, and again on Reset, which restarts this pass),
// which look.glsl fades the pattern in by.
// Inputs: 0 the picture at the grid's size, 1 this pass last frame (r the darkest, g the brightest, b the seconds,
// a 1 once set).
// Out: r the darkest, g the brightest, b the seconds since the pattern started (up to 60), a 1.
uniform vec4 uX;   // x the frame step (s), y how long the easing takes (s)
out vec4 fragColor;

void main() {
    float lod = max(log2(uTD2DInfos[0].res.w / 9.0) - 1.0, 0.0);
    vec2 now = vec2(1.0, 0.0);
    for (int y = 0; y < 9; y++)
        for (int x = 0; x < 16; x++) {
            float l = luma(textureLod(sTD2DInputs[0], (vec2(x, y) + 0.5) / vec2(16.0, 9.0), lod).rgb);
            now = vec2(min(now.x, l), max(now.y, l));
        }
    vec4 last = texture(sTD2DInputs[1], vec2(0.5));
    bool set = last.a > 0.5;
    vec2 m = set ? mix(last.rg, now, 1.0 - exp(-uX.x / uX.y)) : now;
    fragColor = vec4(m, set ? min(last.b + uX.x, 60.0) : 0.0, 1.0);
}
