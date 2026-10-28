// touchdesigner-effects (MIT), Words: one word, from its slot (layout.glsl) by its instance number, on a quad just
// bigger than its ink, cut from the atlas where ink.glsl found its ink.
#define EDGE 1.5                      // atlas pixels around the ink, so the letters' soft edges fit
uniform vec4 uRes;                    // x, y the picture's size (pixels), z how much bigger (a beat: Beat Pump)
uniform sampler2D sState;
uniform sampler2D sInk;
uniform sampler2D sAtlas;
uniform sampler2D sPicture;

out vec2 vUV;
flat out float vAlpha;
flat out float vScale;
flat out vec3 vColor;

void main() {
    int i = TDInstanceID();
    vec4 box = texelFetch(sState, ivec2(i, 0), 0);
    vec4 info = texelFetch(sState, ivec2(i, 1), 0);
    vec4 more = texelFetch(sState, ivec2(i, 2), 0);
    vec4 ink = texelFetch(sInk, ivec2(int(info.x + 0.5), 0), 0);
    vec2 inkSize = max(ink.zw - ink.xy, vec2(1.0));
    box.zw *= 1.0 + uRes.z;                           // a beat swells every word about its middle
    vec2 k = box.zw / inkSize;                        // picture pixels per atlas pixel
    vec2 q = TDPos().xy;                              // -0.5 to 0.5 across the quad
    vec2 half_ = 0.5 * box.zw + EDGE * k;
    float c = cos(more.y), s = sin(more.y);
    vec2 p = box.xy + mat2(c, s, -s, c) * (2.0 * q * half_);
    vUV = (0.5 * (ink.xy + ink.zw) + 2.0 * q * (0.5 * inkSize + EDGE)) / vec2(textureSize(sAtlas, 0));
    vAlpha = info.w != 0.0 ? info.z : 0.0;
    vScale = k.y;
    // Color: Word takes the picture's color across the word: its middle and four points toward its ends and edges
    vec2 ax = mat2(c, s, -s, c) * vec2(0.3 * box.z, 0.0), ay = mat2(c, s, -s, c) * vec2(0.0, 0.25 * box.w);
    vColor = (texture(sPicture, box.xy / uRes.xy).rgb + texture(sPicture, (box.xy + ax) / uRes.xy).rgb +
              texture(sPicture, (box.xy - ax) / uRes.xy).rgb + texture(sPicture, (box.xy + ay) / uRes.xy).rgb +
              texture(sPicture, (box.xy - ay) / uRes.xy).rgb) / 5.0;
    if (vAlpha <= 0.0 || box.w <= 0.0) p = vec2(-1e5);
    gl_Position = vec4(p / uRes.xy * 2.0 - 1.0, 0.0, 1.0);
}
