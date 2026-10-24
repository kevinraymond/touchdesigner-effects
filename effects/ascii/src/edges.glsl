// ASCII (touchdesigner-effects, MIT): edges, at half resolution. Input 0 is the luminance blurred a
// little, input 1 blurred more: their difference (a difference of Gaussians) marks edges, and a
// Sobel filter on input 0 gives each edge's direction, binned into the four line glyphs.
// Out: r the bin as (bin + 0.5) / 4, bins 0 |, 1 \, 2 -, 3 /; g the edge weight 0..1.
uniform float uThresh;   // the difference at which a pixel starts to count as edge
out vec4 fragColor;

float L(vec2 uv) { return texture(sTD2DInputs[0], uv).r; }

void main() {
    vec2 uv = vUV.st;
    vec2 t = uTD2DInfos[0].res.xy;
    float dog = L(uv) - texture(sTD2DInputs[1], uv).r;
    float tl = L(uv + t * vec2(-1, 1)), tc = L(uv + t * vec2(0, 1)), tr = L(uv + t * vec2(1, 1));
    float ml = L(uv + t * vec2(-1, 0)), mr = L(uv + t * vec2(1, 0));
    float bl = L(uv + t * vec2(-1, -1)), bc = L(uv + t * vec2(0, -1)), br = L(uv + t * vec2(1, -1));
    float gx = (tr + 2.0 * mr + br) - (tl + 2.0 * ml + bl);
    float gy = (tl + 2.0 * tc + tr) - (bl + 2.0 * bc + br);
    float w = smoothstep(uThresh, 2.0 * uThresh, abs(dog)) * step(1e-7, gx * gx + gy * gy);
    // The line runs across the gradient: a gradient along x (0 degrees) is a vertical edge, |;
    // one pointing up and right (45) is \; along y (90) is -; up and left (135) is /. Edges have no sign.
    float a = mod(atan(gy, gx), 3.14159265);
    int bin = int(floor(a / 0.78539816 + 0.5)) % 4;
    fragColor = TDOutputSwizzle(vec4((float(bin) + 0.5) / 4.0, w, 0.0, 1.0));
}
