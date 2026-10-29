// Film Stock (touchdesigner-effects, MIT): what its passes share, pasted after lib/glsl/common.glsl (ihash). Dice and
// smooth noise as VHS + CRT's common.glsl has them (the same library). The film's frame number (uF.x, counted in Python
// so it is exact) seeds everything that changes frame to frame on film: the grain, the dirt, the weave's jitter, the
// flicker. Lengths on the film are in micrometers; uF.w is the frame's height in micrometers (the Gauge), and um()
// gives how many micrometers one pixel of the picture covers.
uniform vec4 uF;      // x the film's frame number (0-65535), y seconds (lib clock_seconds()), z Grain (radius multiplier,
                      // with the loudness push), w the frame's height on the film in micrometers (Gauge)
#define PI 3.14159265
#define LN10 2.302585

float die(uint a, uint b, uint c) { return float(ihash(a * 0x9E3779B9u ^ ihash(b ^ ihash(c)))) / 4294967296.0; }
// Two dice from one hash: its low and high 16 bits.
vec2 dice2(uint a, uint b, uint c) {
    uint h = ihash(a * 0x9E3779B9u ^ ihash(b ^ ihash(c)));
    return vec2(float(h & 0xffffu), float(h >> 16)) / 65536.0;
}
// Smooth noise in -1..1 along t.
float wave(float t, uint seed) {
    float i = floor(t), f = fract(t);
    float a = die(uint(int(i) + 100000), seed, 7u), b = die(uint(int(i) + 100001), seed, 7u);
    return mix(a, b, f * f * (3.0 - 2.0 * f)) * 2.0 - 1.0;
}
uint frameSeed() { return uint(uF.x + 0.5); }
// Micrometers of film under one pixel of a picture h pixels high.
float um(float h) { return uF.w / h; }
float logistic(float z) { return 1.0 / (1.0 + exp(-z)); }
vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
