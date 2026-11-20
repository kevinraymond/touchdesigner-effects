// Ferrofluid (touchdesigner-effects, MIT): the surface's height last frame, and a trace of noise. A flat surface
// under a field past the threshold needs something to grow from, as a real one has its ripples: each frame adds noise
// a hundredth of a spike's height, too little to see, from which spikes grow wherever the field lets them. On the
// first frame (the feedback's alpha is 0) the surface starts flat, with only the noise.
// Inputs: 0 the field (drive.glsl: only its size, the grid's), 1 the height last frame (Feedback TOP, read by UV, so a
// new Spike Size starts from it).
// Out: r the height, a 1.
uniform vec4 uN;   // x the noise's size, y the clock (s)
out vec4 fragColor;

void main() {
    vec4 last = texture(sTD2DInputs[1], vUV.st);
    float h = last.a > 0.0 ? last.r : 0.0;
    ivec2 c = ivec2(gl_FragCoord.xy);
    uint salt = ihash(floatBitsToUint(uN.y));
    float n = float(ihash(uint(c.x) + 8192u * uint(c.y) + salt)) / 4294967295.0 - 0.5;
    fragColor = vec4(h + uN.x * n, 0.0, 0.0, 1.0);
}
