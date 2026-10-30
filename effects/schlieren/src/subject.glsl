// Schlieren (touchdesigner-effects, MIT): what warms the air, before lib warmth() eases it and adds what moves. What
// stands in front of its surroundings in the depth map on input 3 (or is inside the mask) warms it, and so do the
// picture's lights, as a lamp or a candle heats the air above it: what is bright and brighter than what is around it,
// so a bright sky doesn't count. What stands out, and a light, is also opaque: a schlieren camera sees the air around a
// person or a lamp, not through them (and a lamp's bright point, shifted by the air shaking over it on a beat, flashed
// the cells around it). The opacity is spread over a cell either way, so the silhouette's edge comes out smooth rather
// than stepped along the depth's cells.
// Inputs: 0 the picture (mipmapped: its brightness at this size comes from a smaller level; Output Resolution Quarter,
// so the air's grid follows the picture's shape, whatever the depth camera's), 1 what stands out or is inside the mask
// (lib depth_find.glsl: r 1 inside, read by UV).
// Out: r how much it warms the air 0-1, g how opaque it is 0-1.
uniform vec4 uS;   // x how much what stands out warms (Warm by Nearness, 0 with nothing on input 3), y how much what is
                   // bright warms (Warm by Light), z 1 when input 3 is wired, w the brightness from which a light warms
out vec4 fragColor;

#define AROUND 6.0       // what is around a light: this mip level of the picture (64 pixels to a texel)
#define BRIGHTER 0.15    // how much brighter than what is around it a light must be, and fully at twice that

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void main() {
    vec2 uv = vUV.st;
    vec2 o = uTD2DInfos[1].res.xy;
    float inside = 0.0;
    for (int k = -1; k <= 1; k++)
        for (int j = -1; j <= 1; j++)
            inside += (2.0 - abs(float(k))) * (2.0 - abs(float(j))) * texture(sTD2DInputs[1], uv + o * vec2(k, j)).r;
    inside *= uS.z / 16.0;
    float here = luma(textureLod(sTD2DInputs[0], uv, 2.0).rgb);
    float light = smoothstep(uS.w, 1.0, here) * smoothstep(BRIGHTER, 2.0 * BRIGHTER,
                                                           here - luma(textureLod(sTD2DInputs[0], uv, AROUND).rgb));
    fragColor = vec4(max(uS.x * inside, uS.y * light), max(inside, step(0.001, uS.y) * light), 0.0, 1.0);
}
