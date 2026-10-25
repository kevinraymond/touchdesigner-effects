// Fluid (touchdesigner-effects, MIT): what the fluid carries, at the input's size: ink, smoke or heat.
// rgb is its color times its amount (premultiplied, so colors mix as they should), a the amount, 0 to 1.
// Each frame it is carried along the velocity (semi-Lagrangian, Stam 1999) with a clamped Catmull-Rom
// sample (lib common.glsl's sampleCR), so it stays sharp where bilinear would blur it within seconds,
// fades by its half-life, and the input pours more in where emit says, in the picture's colors or one
// color. Fire's heat pours in unevenly, flickering (simplex noise), so flames lick rather than stream.
// Inputs: 0 the picture (sets the size), 1 the dye last frame (Feedback TOP), 2 the velocity (cells per
// second, at the grid), 3 where the input emits (emit.glsl).
uniform vec4 uT;   // x: this frame's step (s), y: seconds now
uniform vec4 uD;   // x: amount poured in per second where emit is 1, y: half-life (s), z: Look (0 Ink, 1 Smoke, 2 Fire), w: Color
out vec4 fragColor;

// The color poured in: the picture's (for Smoke lifted, so dark clothes still show) or one color.
vec3 color_at(vec2 uv) {
    vec3 c = texture(sTD2DInputs[0], uv).rgb;
    if (uD.w < 0.5) {
        if (uD.z < 0.5) return c;
        float m = max(c.r, max(c.g, c.b));
        return min(c * max(0.6, m) / max(m, 0.02), vec3(1.0));
    }
    return uD.w < 1.5 ? vec3(1.0, 0.55, 0.15) : uD.w < 2.5 ? vec3(0.25, 0.55, 1.0) : vec3(1.0);
}

void main() {
    float dt = uT.x;
    vec2 uv = vUV.st;
    vec2 v = texture(sTD2DInputs[2], uv).rg * uTD2DInfos[2].res.xy;   // UV per second
    // Ink stays sharp (Catmull-Rom); Smoke and Fire take plain bilinear samples, whose slight blur over
    // seconds reads as the smoke spreading out.
    vec4 d = (uD.z < 0.5 ? sampleCR(1, uv - dt * v) : texture(sTD2DInputs[1], uv - dt * v)) * exp2(-dt / uD.y);
    float e = texture(sTD2DInputs[3], uv).r;
    if (uD.z > 1.5) {
        vec2 res = uTD2DInfos[0].res.zw;
        e *= clamp(0.3 + 1.4 * TDSimplexNoise(vec3(uv * vec2(res.x / res.y, 1.0) * 8.0, uT.y * 1.7)), 0.0, 1.5);
    }
    float add = e * uD.x * dt;
    d += vec4(color_at(uv) * add, add);
    if (d.a > 1.0) d /= d.a;
    fragColor = max(d, vec4(0.0));
}
