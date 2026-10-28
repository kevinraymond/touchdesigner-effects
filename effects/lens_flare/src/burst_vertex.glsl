// touchdesigner-effects (MIT), Lens Flare: one light's starburst (burst.glsl), a square Starburst Size across (in half
// diagonals) on the light, as bright as the light's energy against a small lamp's (REF). Nothing where no light is.
#define REF 0.001
#define FAINTEST 0.0005
uniform vec4 uRes;     // x, y the picture's size (pixels)
uniform vec4 uBurst;   // x gain (Starburst, beat, swell), y Starburst Size
uniform sampler2D sLights;

out vec2 vUV;
flat out vec3 vLevel;

void main() {
    int l = TDInstanceID();
    vec4 light = texelFetch(sLights, ivec2(l, 0), 0);
    vec3 color = texelFetch(sLights, ivec2(l, 1), 0).rgb;
    float hd = 0.5 * length(uRes.xy);
    vLevel = uBurst.x * light.z / REF * color;
    vUV = TDPos().xy + 0.5;
    vec2 p = light.xy + TDPos().xy * uBurst.y;
    if (max(max(vLevel.r, vLevel.g), vLevel.b) < FAINTEST) p = vec2(-4.0);
    gl_Position = vec4(p * hd / (0.5 * uRes.xy), 0.0, 1.0);
}
