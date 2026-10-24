// Glitch (touchdesigner-effects, MIT). Digital corruption in bursts: for the length of a burst,
// blocks shift, freeze, smear or lose their colors and rows tear sideways, all from one seed (the
// burst's number), so the damage holds still while it lasts instead of flickering frame to frame;
// between bursts the picture is whole but for the RGB split. Each burst is one flash, and only the
// bursts the Flashing gate lets through reach here. On every beat, besides, a few thin slivers of
// rows jump sideways and a few single blocks glitch for a moment, and the split kicks: too small an
// area to count as a flash (WCAG counts a flash only over a quarter of a 10-degree field), so they
// need no gate and follow every beat.
// Inputs: 0 the picture; 1 hold.glsl (the picture from just before the burst, for frozen blocks).
uniform vec4 uBurst;   // x 1 during a burst, y its number (the seed), z 1 if it is a drop's, w build 0-1
uniform vec4 uLook;    // x Amount, y Block Size (pixels at 720 high), z RGB Split, w input 2's level
uniform vec4 uOn;      // x Blocks, y Tears, z Song Moments
uniform vec4 uBeat;    // x the beat's envelope (1 at the beat, falling), y beats so far (their seed),
                       // z beat glitches on (0 with Flashing or Bursts Off)
#define BEAT_BLOCKS 5  // single blocks a beat glitches, scattered: together well under a flash's area
#define BEAT_SLIVERS 5 // thin slivers of rows (8-16 px high, 200-500 px long at 720) a beat tears
#define BEAT_HOLD 0.5  // they show while the beat's envelope is above this (its first 0.15 s)
out vec4 fragColor;

// Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
uint hash(uint x) {
    x ^= x >> 16; x *= 0x7feb352du;
    x ^= x >> 15; x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}
float rnd(uint a, uint b, uint c) { return float(hash(a * 0x9E3779B9u ^ hash(b ^ hash(c)))) / 4294967296.0; }

// The picture at uv with red and blue pulled apart by sp (a fraction of the width).
vec3 splitAt(sampler2D t, vec2 uv, float sp) {
    return vec3(texture(t, fract(uv + vec2(sp, 0.0))).r, texture(t, uv).g, texture(t, fract(uv - vec2(sp, 0.0))).b);
}

void main() {
    vec2 res = uTDOutputInfo.res.zw;
    vec2 px = vUV.st * res;
    float s = res.y / 720.0;
    uint seed = uint(uBurst.y + 0.5);
    bool burst = uBurst.x > 0.5;
    bool drop = burst && uBurst.z > 0.5 && uOn.z > 0.5;
    // How much a burst breaks: Amount, more through a build (Song Moments), everything on a drop.
    float amt = clamp(uLook.x * (1.0 + 1.5 * uBurst.w * uOn.z), 0.0, 1.0);
    float sp = uLook.z * 0.006 * (1.0 + 0.5 * uLook.w);
    vec2 uv = vUV.st;
    bool held = false, corrupt = false;
    sp *= 1.0 + 2.0 * uBeat.x * uBeat.x;
    if (!burst && uBeat.z > 0.5 && uBeat.x > BEAT_HOLD) {
        // A beat: BEAT_BLOCKS blocks, each placed by the beat's number, shift, smear or lose colors.
        float b = max(4.0, uLook.y * s);
        uvec2 cell = uvec2(px / b), cells = uvec2(res / b) + 1u;
        uint beat = uint(uBeat.y + 0.5);
        for (uint i = 0u; i < uint(BEAT_BLOCKS); i++) {
            uvec2 at = uvec2(vec2(rnd(beat, i, 21u), rnd(beat, i, 22u)) * vec2(cells));
            if (at != cell) continue;
            float kind = rnd(beat, i, 23u);
            if (kind < 0.4) uv = fract(uv + floor((vec2(rnd(beat, i, 24u), rnd(beat, i, 25u)) - 0.5) * vec2(10.0, 3.0)) * b / res);
            else if (kind < 0.7) uv.x = (floor(px.x / b) * b + 0.5) / res.x;
            else corrupt = true;
        }
        for (uint j = 0u; j < uint(BEAT_SLIVERS); j++) {
            vec2 o = vec2(rnd(beat, j, 31u), rnd(beat, j, 32u)) * res;
            vec2 size = vec2(200.0 + 300.0 * rnd(beat, j, 33u), 8.0 + 8.0 * rnd(beat, j, 34u)) * s;
            if (all(greaterThanEqual(px, o)) && all(lessThan(px, o + size)))
                uv.x = fract(uv.x + (rnd(beat, j, 35u) - 0.5) * 160.0 * s / res.x);
        }
    }
    if (burst) {
        sp *= 3.0;
        if (uOn.y > 0.5) {
            // Tears: bands of rows 12 px high slide sideways; neighbors often go together.
            uint band = uint(px.y / (12.0 * s));
            uint group = band / (1u + uint(rnd(seed, band / 4u, 11u) * 4.0));
            if (drop || rnd(seed, group, 12u) < 0.35 * amt) uv.x = fract(uv.x + (rnd(seed, group, 13u) - 0.5) * 0.4);
        }
        if (uOn.x > 0.5) {
            float b = max(4.0, uLook.y * s);
            uvec2 cell = uvec2(px / b);
            uint id = cell.x * 7919u + cell.y;
            if (drop ? rnd(seed, id, 1u) < 0.75 : rnd(seed, id, 1u) < 0.3 * amt) {
                float kind = rnd(seed, id, 2u);
                if (kind < 0.35) {          // shift: the block shows another part of the picture
                    vec2 off = floor((vec2(rnd(seed, id, 3u), rnd(seed, id, 4u)) - 0.5) * vec2(10.0, 3.0));
                    uv = fract(uv + off * b / res);
                } else if (kind < 0.6) {    // freeze: the block keeps the picture from before the burst
                    held = true;
                } else if (kind < 0.8) {    // smear: the block's left column dragged across it
                    uv.x = (floor(px.x / b) * b + 0.5) / res.x;
                } else {                     // corrupt: channels swapped, colors crushed
                    corrupt = true;
                }
            }
        }
    }
    vec3 c = held ? splitAt(sTD2DInputs[1], uv, sp) : splitAt(sTD2DInputs[0], uv, sp);
    if (corrupt) c = floor(c.brg * 5.0 + 0.5) / 5.0;
    fragColor = TDOutputSwizzle(vec4(c, texture(sTD2DInputs[0], vUV.st).a));
}
