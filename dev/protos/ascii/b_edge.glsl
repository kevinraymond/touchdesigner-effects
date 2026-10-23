// DEV ONLY (ASCII round 1), variant B, pass 1: difference of Gaussians (input 0: narrow blur,
// input 1: wide blur of the luminance) marks edges; a Sobel filter on the narrow blur gives their
// direction. Out: gradient x, gradient y, edge weight 0..1, luminance.
uniform float uTau;    // weight of the wide blur
uniform float uEdge;   // |DoG| at which a pixel starts to count as edge
out vec4 fragColor;
float L(vec2 uv) { return texture(sTD2DInputs[0], uv).r; }
void main() {
    vec2 uv = vUV.st;
    vec2 t = uTD2DInfos[0].res.xy;
    float g1 = L(uv);
    float dog = g1 - uTau * texture(sTD2DInputs[1], uv).r;
    float tl = L(uv + t * vec2(-1, 1)), tc = L(uv + t * vec2(0, 1)), tr = L(uv + t * vec2(1, 1));
    float ml = L(uv + t * vec2(-1, 0)), mr = L(uv + t * vec2(1, 0));
    float bl = L(uv + t * vec2(-1, -1)), bc = L(uv + t * vec2(0, -1)), br = L(uv + t * vec2(1, -1));
    float gx = (tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl);
    float gy = (tl + 2.0 * tc + tr) - (bl + 2.0 * bc + br);
    float e = smoothstep(uEdge, 2.0 * uEdge, abs(dog));
    fragColor = vec4(gx, gy, e, g1);
}
