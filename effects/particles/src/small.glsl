// Particles (touchdesigner-effects, MIT). The picture, small, for finding what moves or what differs
// from the empty room: each output pixel averages a 4 x 4 grid of samples across the input pixels it
// covers, so it doesn't shimmer as fine detail slides past.
// Inputs: 0 the picture (input 1).
// Out: rgb the picture, a its luma.
out vec4 fragColor;

void main() {
    vec2 src = vec2(textureSize(sTD2DInputs[0], 0));
    vec2 out_size = uTDOutputInfo.res.zw;
    vec2 base = floor(gl_FragCoord.xy) / out_size;
    vec3 sum = vec3(0.0);
    for (int y = 0; y < 4; y++) {
        for (int x = 0; x < 4; x++) {
            vec2 uv = base + (vec2(x, y) + 0.5) / (4.0 * out_size);
            sum += texelFetch(sTD2DInputs[0], ivec2(uv * src), 0).rgb;
        }
    }
    vec3 c = sum / 16.0;
    fragColor = vec4(c, dot(c, vec3(0.2126, 0.7152, 0.0722)));
}
