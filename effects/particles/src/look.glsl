// Particles (touchdesigner-effects, MIT). The output: the particles (drawn additively, so where many
// overlap they glow) and their glow, over the picture dimmed to Backdrop; or with Show on Subject,
// what the effect emits from: the picture dimmed, the subject in orange, the depth beside it in blue
// when depth is in use, and a label in the top-left corner saying how it was found (Find), for tuning.
// The builder writes LABELS (every label's glyphs, one after another), LABEL_AT and LABEL_LEN above
// this, and the library's 5 x 7 font (glyph()).
// Inputs: 0 the picture; 1 the particles; 2 the particles, blurred; 3 the subject (subject.glsl).
uniform vec4 uLook;   // x Backdrop, y Glow, z Show (0 particles, 1 subject)
#define PAD 3         // font pixels of plate around the text
#define INK 0.9
out vec4 fragColor;

// Label k's ink (x) and plate (y) at q, pixels from the plate's bottom-left corner, s per font pixel.
vec2 labelAt(int k, vec2 q, float s) {
    int len = LABEL_LEN[k];
    vec2 size = vec2(float(len * 6 - 1 + 2 * PAD), float(7 + 2 * PAD)) * s;
    if (q.x < 0.0 || q.y < 0.0 || q.x >= size.x || q.y >= size.y) return vec2(0.0);
    ivec2 f = ivec2(floor(q / s)) - ivec2(PAD);
    if (f.x < 0 || f.y < 0 || f.y > 6) return vec2(0.0, 1.0);
    int ci = f.x / 6;
    if (ci >= len || f.x - ci * 6 > 4) return vec2(0.0, 1.0);
    return vec2(glyph(LABELS[LABEL_AT[k] + ci], ivec2(f.x - ci * 6, 6 - f.y)), 1.0);
}

void main() {
    vec2 uv = vUV.st;
    vec3 pic = texture(sTD2DInputs[0], uv).rgb;
    if (uLook.z > 0.5) {
        vec4 f = texture(sTD2DInputs[3], uv);
        vec3 c = pic * 0.3 + vec3(0.25, 0.55, 1.0) * 0.35 * f.g * (1.0 - f.r);
        c = mix(c, vec3(1.0, 0.55, 0.15), 0.85 * f.r);
        vec2 res = uTDOutputInfo.res.zw;
        float s = max(1.0, floor(2.0 * res.y / 720.0 + 0.5));
        int k = clamp(int(texelFetch(sTD2DInputs[3], ivec2(0), 0).b + 0.5), 0, N_LABELS - 1);
        vec2 a = labelAt(k, uv * res - vec2(6.0 * s, res.y - 6.0 * s - float(7 + 2 * PAD) * s), s);
        c = mix(mix(c, vec3(0.0), 0.6 * a.y), vec3(INK), a.x);
        fragColor = TDOutputSwizzle(vec4(c, 1.0));
        return;
    }
    vec3 lit = texture(sTD2DInputs[1], uv).rgb + uLook.y * texture(sTD2DInputs[2], uv).rgb;
    lit = 1.0 - exp(-1.5 * lit);                     // many overlapping particles saturate softly
    vec3 c = 1.0 - (1.0 - pic * uLook.x) * (1.0 - lit);
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
