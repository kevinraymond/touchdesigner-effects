// touchdesigner-effects (MIT), Voxel Space: the terrain the camera flies over, its height and the light on it. As
// Comanche's maps had the sun baked into their colors, each pixel is lit by a low sun from the left (Lambert, over
// flat ground's light, so flat ground keeps the picture's own colors), and the hills read where the picture is flat.
// The slope is taken over two pixels either side: the eased heights keep a fading trace of each of a clip's frames
// where something moves, too faint to see as height, and a slope over one pixel drew each trace as a line.
// Inputs: 0 the eased heights. Out: r the height, 0-1, g the light, 1 on flat ground.
uniform vec4 uT;   // x the terrain's height at 1 in world units, y the picture's width in world units, z Light
out vec4 fragColor;

const vec3 SUN = vec3(-0.55, -0.45, 0.70);

float at(ivec2 p, ivec2 n) {
    return texelFetch(sTD2DInputs[0], clamp(p, ivec2(0), n), 0).r;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 n = textureSize(sTD2DInputs[0], 0) - 1;
    float h = texelFetch(sTD2DInputs[0], p, 0).r;
    float l = at(p - ivec2(2, 0), n), r = at(p + ivec2(2, 0), n);
    float b = at(p - ivec2(0, 2), n), t = at(p + ivec2(0, 2), n);
    float unit = uT.y / float(n.x + 1);                 // world units a pixel
    vec2 slope = vec2(r - l, t - b) * uT.x / (4.0 * unit);
    vec3 normal = normalize(vec3(-slope, 1.0));
    vec3 sun = normalize(SUN);
    float lit = 0.35 + 0.65 * max(dot(normal, sun), 0.0) / sun.z;
    fragColor = vec4(h, mix(1.0, min(lit, 1.6), uT.z), 0.0, 1.0);
}
