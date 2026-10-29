// Film Stock (touchdesigner-effects, MIT). The light that halates: what is brighter than a diffuse white goes through
// the emulsion, reflects off the back of the base and comes back up into the red-sensitive layer, the lowest, around
// where it struck. A lamp or the sun is tens of times brighter than white, but video clips it at white, so what rises
// past the knee counts for more the nearer it is to white, a lamp's clipped core for GAIN times a white. This pass
// takes that at an eighth of the size, each pixel the mean of the 8 x 8 it covers; the halo Blur TOP spreads it as
// far as the base is thick, and negative.glsl adds it to the layers' exposure, red most.
// Inputs: 0 the exposure (linear). Out: the light over the knee, linear.
out vec4 fragColor;
#define KNEE 0.5
#define GAIN 12.0

void main() {
    vec2 px = uTDOutputInfo.res.xy;                          // one output pixel, in UV
    vec3 acc = vec3(0.0);
    for (int i = 0; i < 8; i++)
    for (int j = 0; j < 8; j++) {
        vec2 uv = vUV.st + px * ((vec2(float(i), float(j)) + 0.5) / 8.0 - 0.5);
        vec3 over = max(texture(sTD2DInputs[0], uv).rgb - KNEE, 0.0) / (1.0 - KNEE);
        acc += GAIN * over * over;
    }
    fragColor = vec4(acc / 64.0, 1.0);
}
