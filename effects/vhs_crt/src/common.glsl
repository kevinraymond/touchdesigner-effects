// VHS + CRT (touchdesigner-effects, MIT): what the tape's passes share, pasted after lib/glsl/common.glsl.
//
// Lengths along a line are in picture heights (H). NTSC's active line lasts 52.6 us and spans 4/3 H, so one
// H of width passes in 39.45 us and a frequency of f MHz is f x 39.45 cycles per H. The raster holds one
// texel per sample: as wide as the picture, Lines tall, each line one row, line 0 at the top.
uniform vec4 uT;      // x seconds (lib clock_seconds(): wrapped every 16384 s), y Lines, z the beat's kick (0-1), w a drop's slip (of a frame)
uniform vec4 uTape;   // x Tape on, y Wear 0-1, z Tracking 0-1 (with a build), w Head Switching on
uniform vec4 uBurst;  // x the burst's envelope (0-1), y its number (the seed), z level 0-1
#define US_PER_H 39.45
#define FIELD_RATE 59.94
#define PI 3.14159265
#define HEAD_SWITCH 0.025  // the head switch comes this far from the bottom (NTSC: about 6 of 240 lines)
#define FLAGGING 0.05      // the top of the frame bends sideways this far down
// The steady band is at most 2 x (0.012 + BAND_H) of the height, its strong middle much less. Its streaks
// change every field, so it stays under a twelfth of the height: a band across the picture that tall covers
// a quarter of a 10-degree field (a third of the screen high), WCAG's least area for a flash.
#define BAND_H 0.025

float cycH(float mhz) { return mhz * US_PER_H; }
uint field() { return uint(floor(uT.x * FIELD_RATE)); }
// A die in 0-1 from three numbers.
float die(uint a, uint b, uint c) { return float(ihash(a * 0x9E3779B9u ^ ihash(b ^ ihash(c)))) / 4294967296.0; }
// Smooth noise in -1..1 along t.
float wave(float t, uint seed) {
    float i = floor(t), f = fract(t);
    float a = die(uint(int(i) + 100000), seed, 7u), b = die(uint(int(i) + 100001), seed, 7u);
    return mix(a, b, f * f * (3.0 - 2.0 * f)) * 2.0 - 1.0;
}
// How strongly the heads mistrack on line y (0 top, 1 bottom): x the steady band that crawls up the
// picture (Tracking sets it), y a burst's big one, placed by the burst's number.
vec2 bands(float y) {
    float t = uT.x, tr = uTape.z;
    float c0 = fract(0.85 - 0.021 * t), h0 = 0.012 + BAND_H * tr;
    float d0 = abs(y - c0);
    d0 = min(d0, 1.0 - d0);                                   // it wraps from the top to the bottom
    float s0 = smoothstep(0.0, 0.12, tr) * (0.35 + 0.65 * tr);
    uint seed = uint(uBurst.y + 0.5);
    float cb = 0.15 + 0.7 * die(seed, 1u, 91u), hb = 0.08 + 0.12 * die(seed, 2u, 91u);
    float slipped = uT.w > 0.0 ? 0.0 : 1.0;                 // a drop's burst slips the picture, no band
    return vec2(s0 * pow(clamp(1.0 - d0 / h0, 0.0, 1.0), 1.5),
                slipped * uBurst.x * pow(clamp(1.0 - abs(y - cb) / hb, 0.0, 1.0), 0.7));
}
float band(float y) { vec2 b = bands(y); return clamp(max(b.x, b.y), 0.0, 1.0); }
// What the band's tearing and streaks are drawn from on line y: a new draw every field in the steady band,
// one draw for the whole of a burst, so a burst's damage holds still while it lasts (one flash, not one
// a field) as the picture under it moves on.
uint bandSeed(float y) { vec2 b = bands(y); return b.y > b.x ? 0x40000000u + uint(uBurst.y + 0.5) : field(); }
