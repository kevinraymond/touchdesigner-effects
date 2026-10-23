// Levels, with an optional automatic white point: input STATS is f_stats, 1 x 1, whose blue
// channel is min(brightest cell, 2.5 x mean cell luminance), clamped to 0.3..1.
uniform vec3 uLevels;   // black point, white point, gamma
uniform float uAuto;    // 0: the white point above; 1: the automatic one
float level(float v) {
    float hi = mix(uLevels.y, texelFetch(sTD2DInputs[STATS], ivec2(0), 0).b, uAuto);
    return pow(clamp((v - uLevels.x) / max(hi - uLevels.x, 1e-3), 0.0, 1.0), uLevels.z);
}
