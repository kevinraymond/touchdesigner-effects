// touchdesigner-effects (MIT), Words: the picture in cells, the grid the layout packs words on: 8 x 8 pixels a cell,
// bigger for a picture past 1280 on a side (the layout holds at most 160 x 160). Per cell: whether the subject is there
// (Shape From), how much detail the picture holds there and how bright it is.
// Inputs: 0 the picture, 1 the subject (a quarter size: r inside, for Depth and Mask), 2 the motion (an eighth of the
// size: rg its pixels per second there).
// Out: r the subject's share of the cell (0-1), g detail (the luma's mean slope, per pixel), b mean luma, a 1.
uniform vec4 uShape;   // x Shape From (0 depth, 1 mask, 2 brightness, 3 movement), y Sensitivity
out vec4 fragColor;

float luma(vec2 uv) {
    return dot(texture(sTD2DInputs[0], uv).rgb, vec3(0.2126, 0.7152, 0.0722));
}

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    float l = 0.0, g = 0.0;
    for (int j = 0; j < 4; j++)
    for (int i = 0; i < 4; i++) {
        vec2 q = uv + vec2(float(i) - 1.5, float(j) - 1.5) * 2.0 * px;
        float c = luma(q);
        l += c;
        g += length(vec2(luma(q + vec2(px.x, 0.0)) - luma(q - vec2(px.x, 0.0)),
                         luma(q + vec2(0.0, px.y)) - luma(q - vec2(0.0, px.y)))) * 0.5;
    }
    l /= 16.0;
    g /= 16.0;
    int from = int(uShape.x + 0.5);
    float inside;
    if (from <= 1) {
        inside = texture(sTD2DInputs[1], uv).r;
    } else if (from == 2) {
        inside = smoothstep(0.0, 0.1, l - mix(0.85, 0.15, uShape.y));
    } else {
        vec2 v = texture(sTD2DInputs[2], uv).rg * uTD2DInfos[2].res.xy;     // UV per second
        inside = smoothstep(0.0, 0.5, length(v) / mix(0.4, 0.02, uShape.y) - 1.0);
    }
    fragColor = vec4(inside, g, l, 1.0);
}
