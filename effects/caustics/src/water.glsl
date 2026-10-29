// touchdesigner-effects (MIT), Caustics: the water's surface, a height field stepped by the damped wave equation once
// a frame, as Evan Wallace's WebGL Water steps it (github.com/evanw/webgl-water, MIT, Copyright 2011 Evan Wallace):
// each point's velocity is pulled toward the average height of its four neighbors, damped, and moves the point. A
// little viscosity besides, so the finest ripples (the grid's own checkerboard, which focused light into a fine
// grating) die first. The picture's movement pushes it (push.glsl, blurred), and each beat drops a raindrop into it.
// Inputs: 0 the push (blurred), 1 this pass's previous output (Feedback TOP: alpha 0 on its first frame).
// Out: r the height, g the velocity (in this map's pixels), a 1.
uniform vec4 uW;   // x the pull toward the neighbors this frame, y the damping this frame, z the viscosity this frame,
                   // w how hard movement pushes
uniform vec4 uD;   // a drop this frame: xy where (0-1 across and up), z its radius (a share of the height), w how much it
                   // adds this frame (0 none)
out vec4 fragColor;
void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    ivec2 size = textureSize(sTD2DInputs[1], 0);
    vec4 here = texelFetch(sTD2DInputs[1], p, 0);
    if (here.a < 0.5) {             // the first frame: still water
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }
    // the edges hold their neighbor, so waves reflect off the pool's sides
    float l = texelFetch(sTD2DInputs[1], clamp(p - ivec2(1, 0), ivec2(0), size - 1), 0).r;
    float r = texelFetch(sTD2DInputs[1], clamp(p + ivec2(1, 0), ivec2(0), size - 1), 0).r;
    float d = texelFetch(sTD2DInputs[1], clamp(p - ivec2(0, 1), ivec2(0), size - 1), 0).r;
    float u = texelFetch(sTD2DInputs[1], clamp(p + ivec2(0, 1), ivec2(0), size - 1), 0).r;
    float avg = 0.25 * (l + r + d + u);
    float h = here.r, v = here.g;
    v += (avg - h) * uW.x;
    v *= uW.y;
    h += v;
    h += uW.z * (avg - h);
    h += uW.w * texelFetch(sTD2DInputs[0], p, 0).r;
    if (uD.w > 0.0) {
        vec2 at = (vec2(p) + 0.5) / float(size.y);
        vec2 c = uD.xy * vec2(size) / float(size.y);
        float k = max(0.0, 1.0 - length(at - c) / uD.z);
        h += (0.5 - 0.5 * cos(k * 3.14159265)) * uD.w;
    }
    h *= 0.999;                     // a slow leak, so pushes that don't balance don't tilt the pool for good
    fragColor = vec4(h, v, 0.0, 1.0);
}
