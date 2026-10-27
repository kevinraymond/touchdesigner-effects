// touchdesigner-effects (MIT), Pixel Art: the art at the picture's size, each art pixel a square of S x S in its
// palette color as shown (palette.glsl's shown(): saturated, clear of the red line). Dither (ours) mixes in the next
// nearest color with an
// ordered dither on the art's own grid (B. E. Bayer, "An optimum method for two-level rendition of continuous-tone
// pictures", ICC 1973, the 4 x 4 matrix): an art pixel sitting halfway between two colors becomes a checkerboard of
// both, one sitting at its own color stays plain, and Dither below 1 leaves all but the nearest ties plain. Mosaic
// (the beat's kick): each block of M x M art pixels shows its top-left one, as the Super Nintendo's mosaic did.
// Inputs: 0 the picture, 1 each art pixel's color (index.glsl buffer 0), 2 the next nearest (buffer 1).
// Out: the picture.
uniform vec4 uS;   // x Pixel Size, y the grid's allocated size G, z Dither
uniform vec4 uM;   // x the mosaic's block (1: none)
out vec4 fragColor;

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void main() {
    ivec2 res = textureSize(sTD2DInputs[0], 0);
    int s = cell_size(res, uS.x, uS.y);
    ivec2 p = ivec2(gl_FragCoord.xy);
    int m = max(int(uM.x + 0.5), 1);
    // The grid counts up from the bottom (TouchDesigner's), the mosaic's blocks from the top, as on a screen.
    ivec2 n = grid_size(res, s);
    ivec2 cell = p / s;
    int top = (n.y - 1 - cell.y) / m * m;
    cell = ivec2(cell.x / m * m, n.y - 1 - top);
    vec4 a = texelFetch(sTD2DInputs[1], cell, 0);
    if (a.a <= 0.0) {   // no palette yet (the first frame)
        fragColor = texelFetch(sTD2DInputs[0], p, 0);
        return;
    }
    vec3 lab = a.rgb;
    if (uS.z > 0.0) {
        vec4 b = texelFetch(sTD2DInputs[2], cell, 0);
        float f = clamp((b.a - 0.5 * (1.0 - uS.z)) / uS.z, 0.0, 0.5);
        ivec2 q = ivec2(cell.x & 3, top & 3);
        if ((BAYER[q.y * 4 + q.x] + 0.5) / 16.0 < f) lab = b.rgb;
    }
    fragColor = vec4(clamp(linear_to_srgb(lab_to_linear(lab)), 0.0, 1.0), 1.0);
}
