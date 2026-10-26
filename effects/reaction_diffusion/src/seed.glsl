// Reaction-Diffusion (touchdesigner-effects, MIT): the pattern where react.glsl takes it up this frame. The state
// last frame, read by UV (so a new Size scales it, and Reset's empty 1 x 1 state fills the grid), with this frame's
// feed and kill rates per cell, and seeds: where the pattern may grow but nothing has (V near 0), now and then a
// spot of V, from which it spreads (one 4 cells across or more: smaller ones died where the diffusion is
// stretched). Each block of uS.z x uS.z cells draws uS.w times a second, and a draw seeds it with chance uS.y.
// The kill rate follows the ink the picture asks for here (where.glsl's g): k_ink where it asks for all ink, k_none
// where it asks for none (the same for Lines, which draws the picture by line width instead), and k_dead where the
// pattern may not grow (where.glsl's r 0), so it breaks up and fades there.
// Inputs: 0 the picture at the grid's size (only its size), 1 the state last frame (r U, g V), 2 where (r where it
// may grow, 0-1; g the ink the picture asks for, 0-1).
// Out: r U, g V, b k, a F.
uniform vec4 uK;   // x F, y k_ink, z k_none, w k_dead
uniform vec4 uS;   // x the clock (s), y a seed's chance per draw, z the block's size (cells), w draws a second
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    vec2 s = texture(sTD2DInputs[1], uv).rg;
    vec2 w = texture(sTD2DInputs[2], uv).rg;
    float k = mix(uK.w, mix(uK.z, uK.y, w.g), w.r);
    vec2 block = floor(gl_FragCoord.xy / uS.z);
    float draw = floor(uS.x * uS.w);
    float h = float(ihash(uint(block.x) + 8192u * uint(block.y) + ihash(uint(draw)))) / 4294967295.0;
    if (w.r > 0.5 && s.g < 0.05 && h < uS.y) {
        float d = length(gl_FragCoord.xy - (block + 0.5) * uS.z);
        float spot = 1.0 - smoothstep(3.5, 4.5, d);
        s = vec2(min(s.r, 1.0 - 0.5 * spot), max(s.g, 0.25 * spot));
    }
    fragColor = vec4(s, k, uK.x);
}
