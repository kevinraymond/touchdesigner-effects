// touchdesigner-effects (MIT), Pencil: the picture's histogram, 256 levels, each capped, for tone.glsl. Each pixel of
// this pass is a level b: the share of the picture near b, every sample spread over a few levels (a triangle uH.x
// levels wide) so that a flat area piling into one level doesn't make neighboring levels jump apart.
// The share is then capped at uH.y times an even share (1/256), as contrast-limited histogram equalization caps its
// histogram (Pizer et al., "Adaptive Histogram Equalization and Its Variations", 1987; Zuiderveld, "Contrast Limited
// Adaptive Histogram Equalization", Graphics Gems IV, 1994), here over the whole picture: matching a picture whose
// tones crowd into a narrow band (a dark pond, a gray square) would stretch that band over every tone, and its
// ripples, noise and compression blocks with it (the koi's worst cell flashed 4 times a second uncapped, 3 capped;
// dev/flash.py). tone.glsl spreads what the cap took off evenly over all levels.
// The picture is read on a 64 x 36 grid of a small mipmap level (Input Smoothness Mipmap), each sample the mean of a
// few pixels.
// Inputs: 0 the picture.
// Out: r the share of the picture at this pixel's level (along x, 0-255), capped; g what the cap took off; a 1.
uniform vec4 uH;   // x the spread (levels), y the cap (times an even share), z 1 for Light on Dark (the brightness
                   // turned over: the drawing's marks are the picture's light)
out vec4 fragColor;

void main() {
    float b = floor(gl_FragCoord.x);
    float lod = max(log2(uTD2DInfos[0].res.w / 36.0) - 1.0, 0.0);
    float w = max(uH.x, 1.0);
    float share = 0.0;
    for (int y = 0; y < 36; y++)
        for (int x = 0; x < 64; x++) {
            vec3 c = textureLod(sTD2DInputs[0], (vec2(x, y) + 0.5) / vec2(64.0, 36.0), lod).rgb;
            float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
            l = 255.0 * clamp(uH.z > 0.5 ? 1.0 - l : l, 0.0, 1.0);
            share += max(1.0 - abs(l - b) / w, 0.0) / w;
        }
    share /= 64.0 * 36.0;
    float cap = uH.y / 256.0;
    fragColor = vec4(min(share, cap), max(share - cap, 0.0), 0.0, 1.0);
}
