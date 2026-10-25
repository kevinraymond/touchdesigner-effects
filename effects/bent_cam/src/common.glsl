// Bent Cam (touchdesigner-effects, MIT): what the camera's passes share, pasted after lib/glsl/common.glsl.
//
// Lines are counted from the top, as the sensor sends them (line 0 first); a texel's row is H - 1 - line.
// A burst is a wire touching for a moment. Which wire it is comes from the burst's number, so the bus and the
// compressor agree on it and its damage holds still while it lasts: one flash, not one a frame.
#define PI 3.14159265
#define BURST_SLIP 1      // the bridge takes the bytes one late: color read as brightness, the frame turns green and pink
#define BURST_SHORTS 2    // every short the camera has, at once
#define BURST_FRAME 3     // the frame starts in the wrong place: the picture jumps down a third (a drop's burst)
#define BURST_BLOCKS 4    // the compressed stream breaks from a block on, to the end of the frame

// A die in 0-1 from three numbers.
float die(uint a, uint b, uint c) { return float(ihash(a * 0x9E3779B9u ^ ihash(b ^ ihash(c)))) / 4294967296.0; }

// Which wire a burst touches: 0 while none does. number is the burst's count, drop whether it was a drop's.
int burstKind(float envelope, float number, float drop) {
    if (envelope <= 0.0) return 0;
    if (drop > 0.5) return BURST_FRAME;
    float d = die(uint(number + 0.5), 5u, 71u);
    return d < 0.4 ? BURST_SLIP : d < 0.7 ? BURST_SHORTS : BURST_BLOCKS;
}

// A texel's line, counted from the top.
int lineOf(ivec2 p, int H) { return H - 1 - p.y; }
