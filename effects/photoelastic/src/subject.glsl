// Photoelastic (touchdesigner-effects, MIT): what warms the plastic, before lib warmth() eases it and adds what moves.
// What stands in front of its surroundings in the depth map on input 3 (or is inside the mask) warms it, and so does the
// picture's light, as light falling on a plate warms it: the brighter, the warmer. A bright area evenly warm is stressed
// only at its outline, so the fringes follow the picture's bright shapes (each koi on dark water, the flowers against
// the sky). Spread over a cell, so the outline comes out smooth rather than stepped along the depth's cells.
// Inputs: 0 the picture (mipmapped; Output Resolution Quarter), 1 what stands out or is inside the mask (lib
// depth_find.glsl: r 1 inside).
// Out: r how much it warms the plastic 0-1.
uniform vec4 uS;   // x how much what stands out warms (Warm by Nearness, 0 with nothing on input 3), y how much the
                   // light warms (Warm by Light), z 1 when input 3 is wired
out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void main() {
    vec2 uv = vUV.st;
    vec2 o = uTD2DInfos[1].res.xy;
    float inside = 0.0;
    for (int k = -1; k <= 1; k++)
        for (int j = -1; j <= 1; j++)
            inside += (2.0 - abs(float(k))) * (2.0 - abs(float(j))) * texture(sTD2DInputs[1], uv + o * vec2(k, j)).r;
    inside *= uS.z / 16.0;
    float light = luma(textureLod(sTD2DInputs[0], uv, 2.0).rgb);
    fragColor = vec4(max(uS.x * inside, uS.y * light), 0.0, 0.0, 1.0);
}
