// Point Cloud (touchdesigner-effects, MIT). The depth pos.glsl reads: input 3's when it carries any,
// else input 1's brightness. Picked once per point here, so pos.glsl's many reads per point each
// read one texture. Input 3 carries no depth when it is all black: a camera unplugged, or the
// Showreel with input 1 wired and nothing on input 3. Then every point stays (pos.glsl), rather than
// a flat picture or an empty frame.
// Inputs: 0 the depth at the grid's size (depth_near.glsl: r nearness, g how much had a reading);
// 1 the picture; 2 the depth's largest nearness (an Analyze TOP over a small copy).
// Out: r nearness, g how much had a reading, b 1 when the brightness stands in.
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    bool guess = texelFetch(sTD2DInputs[2], ivec2(0), 0).r <= 0.02;
    vec2 d = texelFetch(sTD2DInputs[0], p, 0).rg;
    if (guess)
        d = vec2(dot(texture(sTD2DInputs[1], vUV.st).rgb, vec3(0.2126, 0.7152, 0.0722)), 1.0);
    fragColor = vec4(d, guess ? 1.0 : 0.0, 1.0);
}
