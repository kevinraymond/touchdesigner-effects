// Frost (touchdesigner-effects, MIT): the pane at the ice's grid. How cold the glass is, which follows how far
// (input 3's depth) or how dark (with nothing there, the picture's brightness stands in, as for every effect
// that reads depth) the picture is, so the room behind freezes first, eased over a second; how warm it is (lib
// warmth.glsl: what stands out and what moves), from WARM_FROM up (a faint warmth, the edge of what stands out or
// haze drifting, wore Stars' ice down to specks); and where new crystals start: on the picture's edges, where it is
// cold and not warm.
// Inputs: 0 the picture at the grid's size (only its size), 1 the flow at the same size (lib tensor_flow.glsl:
// a how strongly the picture changes, squared), 2 nearness (lib depth_near.glsl: r 0-1), 3 the warmth (lib
// warmth.glsl: r 0-1), 4 this pass's last output (Feedback TOP).
// Out: r cold 0-1, g warm 0-1, b where crystals may start 0-1, a 1.
uniform vec4 uC;   // x this frame's step (s), y how long the cold takes to follow the picture (s), z Freeze Evenly
                   // (0: the far or dark freezes, 1: all of it alike)
uniform vec4 uE;   // xy the change (squared gradient) from which an edge starts crystals, and from which fully
out vec4 fragColor;

#define WARM_FROM vec2(0.15, 0.5)   // the warmth from which the glass counts as warm, and from which fully

void main() {
    vec2 uv = vUV.st;
    vec4 last = texture(sTD2DInputs[4], uv);
    float change = texture(sTD2DInputs[1], uv).a;
    float near = texture(sTD2DInputs[2], uv).r;
    float warm = smoothstep(WARM_FROM.x, WARM_FROM.y, texture(sTD2DInputs[3], uv).r);
    float cold = mix(1.0 - near, 1.0, uC.z);
    // The first frame (the feedback's alpha is 0) takes the picture as it is.
    cold = last.a > 0.0 ? mix(cold, last.r, exp(-uC.x / uC.y)) : cold;
    float edge = smoothstep(uE.x, uE.y, change) * cold * (1.0 - warm);
    fragColor = vec4(cold, warm, edge, 1.0);
}
