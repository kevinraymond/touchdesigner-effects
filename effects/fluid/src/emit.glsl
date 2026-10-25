// Fluid (touchdesigner-effects, MIT): where the input pours ink, smoke or heat into the fluid, 0 to 1,
// at the fluid's grid. Emit From: Movement, what moves (motion.glsl's speed, where the flow is sure
// of it); Brightness, what is bright; Depth, what stands out in front of its surroundings in the depth
// map on input 3 (lib depth_find.glsl); Mask, what is inside the mask on input 3. Sensitivity lowers
// the bar in each (for Depth, through depth_find's Far Limit).
// Inputs: 0 the motion (rg cells per second, b confidence; sets the size), 1 the picture, 2 for Depth
// the subject (r 1 inside), for Mask the mask (r), else black. Out: r how much emits here, gba 0.
uniform vec4 uE;   // x: Emit From (0 Movement, 1 Brightness, 2 Depth, 3 Mask), y: Sensitivity (0-1)
out vec4 fragColor;

// The mean over the 4 x 4 input pixels this grid cell covers: four bilinear taps on texel corners.
vec4 cell(int i, vec2 uv) {
    vec2 o = uTD2DInfos[i].res.xy;
    return 0.25 * (texture(sTD2DInputs[i], uv + vec2(-o.x, -o.y)) + texture(sTD2DInputs[i], uv + vec2(o.x, -o.y))
                 + texture(sTD2DInputs[i], uv + vec2(-o.x, o.y)) + texture(sTD2DInputs[i], uv + vec2(o.x, o.y)));
}

void main() {
    vec2 uv = vUV.st;
    float s = uE.y, e = 0.0;
    if (uE.x < 0.5) {
        vec4 m = texture(sTD2DInputs[0], uv);
        float speed = length(m.rg) * uTD2DInfos[0].res.y;       // frame heights per second
        float lo = 0.4 * pow(1.0 / 20.0, s);                     // 0.4 frame heights per second at 0, 0.02 at 1
        e = smoothstep(lo, 3.0 * lo, speed) * smoothstep(2e-4, 1e-3, m.b);
    } else if (uE.x < 1.5) {
        float l = dot(cell(1, uv).rgb, vec3(0.2126, 0.7152, 0.0722));
        float lo = mix(0.9, 0.2, s);
        e = smoothstep(lo, lo + 0.1, l);
    } else if (uE.x < 2.5) {
        e = texture(sTD2DInputs[2], uv).r;
    } else {
        float lo = mix(0.9, 0.1, s);
        e = smoothstep(lo, lo + 0.05, texture(sTD2DInputs[2], uv).r);
    }
    fragColor = vec4(e, 0.0, 0.0, 1.0);
}
