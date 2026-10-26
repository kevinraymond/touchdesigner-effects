// touchdesigner-effects (MIT), Motion Magnify: the displacement made larger (Amount, the music) and how much that would
// stretch the picture: where one pixel's displacement differs from its neighbor's by a pixel or more, warp.glsl would
// fold the picture over itself there (a dancer melting into the smoke behind her). guard.glsl holds it back.
// Inputs: 0 the displacement, spread (spread.glsl: rg UV units), 1 nearness (lib depth_near.glsl: r 0 far to 1 near).
// Out: rg the displacement made larger (UV units), b the stretch: its largest change from one pixel to the next, in
// pixels per pixel.
uniform vec4 uA;   // x how many times further (Amount and the music), y Depth Focus (0 without input 3)
out vec4 fragColor;

vec2 larger(vec2 uv) {
    float near = texture(sTD2DInputs[1], uv).r;
    return uA.x * mix(1.0, near, uA.y) * texture(sTD2DInputs[0], uv).rg;
}

void main() {
    vec2 uv = vUV.st;
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 dx = (larger(uv + vec2(px.x, 0.0)) - larger(uv - vec2(px.x, 0.0))) * 0.5 * res;
    vec2 dy = (larger(uv + vec2(0.0, px.y)) - larger(uv - vec2(0.0, px.y))) * 0.5 * res;
    float g = max(max(abs(dx.x), abs(dx.y)), max(abs(dy.x), abs(dy.y)));
    fragColor = vec4(larger(uv), g, 1.0);
}
