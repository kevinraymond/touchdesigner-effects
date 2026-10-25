// Particles (touchdesigner-effects, MIT). The particles: one per pixel of four 32-bit float
// buffers, which this shader reads back each frame through Feedback TOPs and moves on.
// A free particle is born with a chance that makes the frame's births come to the number asked for.
// Behavior Emit: every birth (Rate, more on a beat) picks a random pixel of the subject (or its
// outline) and is born there if the pixel is one, takes the picture's color there, and leaves the body
// outward. A living one ages, rides the wind (Drift, along Direction, swung by the bars), swirls in the
// turbulence (curl noise: a swirling flow that never piles particles up), is kicked outward from the
// subject on each beat and by a drop's shockwave, fades in, and fades out over the second half of its
// life; one that leaves the frame is gone.
// Push and Flow: Rate's births land all over the frame (a beat's burst still leaves the subject's
// outline), and particles ride the air (air.glsl) exactly, which goes round the subject: still in Push,
// the wind in Flow; a shove or a drop's shockwave gives a particle speed of its own on top, which dies
// away. (Particles that only eased into the air couldn't follow it round a hand and left holes.) In
// Push the subject is solid and nothing is born on it: a particle it moves onto is put back on its edge
// and that move becomes the particle's speed, so a moving subject shoves what it touches and leaves a
// gap where it was, which fills as particles die and are born. The field glows dimly and a shoved
// particle lights up and swells, settling again as it slows. In Flow the subject is in front of the
// stream: particles it covers are hidden and wait, so it leaves no gap when it moves on. A particle
// that leaves the frame comes back on the far side, so a beat doesn't kick them outward (they would
// gather at the frame's edges): the whole field pulses out from the subject's middle and back.
// Positions are in frame heights from the middle of the frame (x across, y up), which is how the
// Geometry COMP draws them; sizes are in frame heights too.
// Inputs: 0, 1, 2, 3 this TOP's four buffers last frame; 4 where particles may be born (emit.glsl);
// 5 the subject, blurred (its edge, and which way is out); 6 the picture (their colors); 7 the average
// of buffer 1 last frame (a: how many are alive); 8 the average of input 4 (how much of the frame the
// subject and its outline cover, and the subject's middle); 9 the air (air.glsl, Push and Flow).
// Out: buffer 0 x, y, x speed, y speed (in Push and Flow its speed on top of the air's); buffer 1 age
// (s), life (s), size (as drawn), 1 alive or 0 free; buffer 2 color r, g, b, and a: how visible it is
// now; buffer 3 r how hard it was shoved lately (0-1), g its size at rest, b how much of a spark it
// still is (a beat's burst is born as sparks: drawn bigger, shrinking to its size at rest).
uniform vec4 uClock;  // x seconds since the last frame, y seconds, z frame number (the dice), w aspect (width / height)
uniform vec4 uEmit;   // x births asked for this frame, y Life (s), z Speed, w 1 born on the outline only
uniform vec4 uMove;   // x Drift, y Turbulence, z Size (frame heights), w beat kick 0-1
uniform vec4 uWave;   // x shockwave radius (frame heights), y strength 0-1, z the wind's direction from
                      // straight up (radians), w a beat's burst: births this frame on top of x
uniform vec4 uLook;   // x Color (0 picture, 1 orange, 2 blue, 3 white), y Behavior (0 Emit, 1 Push, 2 Flow),
                      // z the beat's pulse this frame (Push, Flow): how far the field moves out from the
                      // subject's middle (or back, below 0), as a share of its distance from it; w 1 while
                      // a burst's births are sparks (a beat the flash gate let through)
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
#define KICK 8.0          // a beat's push outward, frame heights per second per second at the beat's peak
#define SPARK 1.5         // a burst's particle is born 1 + SPARK times its size...
#define SPARK_FADE 0.3    // ...and shrinks back over about this many seconds
#define SETTLE_PUSH 0.6   // seconds a particle's own speed (a shove, a shockwave) takes to die away in Push
#define SETTLE_FLOW 0.15  // the same in Flow, where it keeps to the stream
#define FADE_IN 0.12      // seconds a particle takes to fade in: Emit
#define FADE_IN_FIELD 0.4 // the same in Push and Flow, where they appear all over the frame
#define CALM 0.25         // how visible a particle at rest is in Push; a shoved one is fully
#define SWELL 0.8         // how much bigger a shoved particle is drawn in Push, fully shoved
#define SHOVE_LIT 0.5     // a shove this fast (frame heights per second) lights a particle fully in Push
#define SHOVE_FADE 0.8    // seconds a shoved particle takes to settle
#define SHOVE_MAX 1.5     // the most speed one frame's shove gives (frame heights per second)

uint hash(uint v) {                    // PCG: a well-mixed 32-bit hash
    uint s = v * 747796405u + 2891336453u;
    uint w = ((s >> ((s >> 28u) + 4u)) ^ s) * 277803737u;
    return (w >> 22u) ^ w;
}

float roll(inout uint s) {
    s = hash(s);
    return float(s >> 8) / 16777216.0;
}

vec2 to_uv(vec2 w) { return vec2(w.x / uClock.w + 0.5, w.y + 0.5); }
vec2 to_world(vec2 uv) { return vec2((uv.x - 0.5) * uClock.w, uv.y - 0.5); }

// A swirling flow: the curl of a slowly changing noise field, about 2.5 swirls per frame height.
vec2 swirl(vec2 w, float t) {
    const float e = 0.01;
    vec3 q = vec3(w * 2.5, t * 0.15);
    float dy = TDSimplexNoise(q + vec3(0.0, e, 0.0)) - TDSimplexNoise(q - vec3(0.0, e, 0.0));
    float dx = TDSimplexNoise(q + vec3(e, 0.0, 0.0)) - TDSimplexNoise(q - vec3(e, 0.0, 0.0));
    return vec2(dy, -dx) / (2.0 * e);
}

// The air's velocity at w (Push and Flow), from air.glsl's stream function, whose pixels are the
// corners of a cell: across it, each component blends the two values on the cell's sides it crosses
// (each side's from the two corners on it), so as much air leaves every cell as enters it and
// particles neither gather nor thin out. (Blending the stream function and differencing it drained
// patches beside the subject, where it bends sharply.)
vec2 air(vec2 w) {
    ivec2 size = textureSize(sTD2DInputs[9], 0);
    vec2 q = clamp(to_uv(w) * vec2(size) - 0.5, vec2(0.0), vec2(size) - 1.001);
    ivec2 i = ivec2(floor(q));
    vec2 f = q - vec2(i);
    float a = texelFetch(sTD2DInputs[9], i, 0).r;
    float b = texelFetch(sTD2DInputs[9], i + ivec2(1, 0), 0).r;
    float c = texelFetch(sTD2DInputs[9], i + ivec2(0, 1), 0).r;
    float d = texelFetch(sTD2DInputs[9], i + ivec2(1, 1), 0).r;
    vec2 cell = vec2(uClock.w / float(size.x), 1.0 / float(size.y));   // in frame heights
    return vec2(mix(c - a, d - b, f.x) / cell.y, -mix(b - a, d - c, f.y) / cell.x);
}

// The blurred subject at w (x) and its slope, per frame height (y, z): it rises into the subject.
vec3 subject(vec2 w) {
    vec2 uv = to_uv(w), px = 1.0 / vec2(textureSize(sTD2DInputs[5], 0));
    float b = texture(sTD2DInputs[5], uv).r;
    float dx = texture(sTD2DInputs[5], uv + vec2(px.x, 0.0)).r - texture(sTD2DInputs[5], uv - vec2(px.x, 0.0)).r;
    float dy = texture(sTD2DInputs[5], uv + vec2(0.0, px.y)).r - texture(sTD2DInputs[5], uv - vec2(0.0, px.y)).r;
    return vec3(b, dx / (2.0 * px.x * uClock.w), dy / (2.0 * px.y));
}

void free_slot() {
    fragColor[0] = vec4(0.0);
    fragColor[1] = vec4(0.0);
    fragColor[2] = vec4(0.0);
    fragColor[3] = vec4(0.0);
}

// A new particle's color: the picture's at uv, lifted so dark clothes still glow (brightest channel to
// at least 0.6), or one color.
vec3 color_at(vec2 uv) {
    vec3 c = texture(sTD2DInputs[6], uv).rgb;
    if (uLook.x < 0.5)
        return min(c * max(0.6, max(c.r, max(c.g, c.b))) / max(max(c.r, max(c.g, c.b)), 0.02), vec3(1.0));
    return uLook.x < 1.5 ? vec3(1.0, 0.55, 0.15) : uLook.x < 2.5 ? vec3(0.25, 0.55, 1.0) : vec3(1.0);
}

void born(vec2 uv, vec2 v, float spark, inout uint dice) {
    float life = uEmit.y * (0.5 + roll(dice));
    float size = uMove.z * (0.6 + 0.8 * roll(dice));
    fragColor[0] = vec4(to_world(uv), v);
    fragColor[1] = vec4(0.0, life, size * (1.0 + SPARK * spark), 1.0);
    fragColor[2] = vec4(color_at(uv), 0.0);
    fragColor[3] = vec4(0.0, size, spark, 0.0);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float dt = min(uClock.x, 0.1);           // after a stall, don't jump
    int mode = int(uLook.y + 0.5);
    vec4 s0 = texelFetch(sTD2DInputs[0], p, 0);
    vec4 s1 = texelFetch(sTD2DInputs[1], p, 0);
    vec4 s2 = texelFetch(sTD2DInputs[2], p, 0);
    vec4 s3 = texelFetch(sTD2DInputs[3], p, 0);
    vec4 cover = texelFetch(sTD2DInputs[8], ivec2(0), 0);
    uint dice = hash(uint(p.x) + 4096u * uint(p.y) + hash(uint(uClock.z)));

    if (s1.a < 0.5) {
        // Free: born this frame? Births asked for / free slots whose random pick would take. In Emit
        // every birth comes off the subject; in Push Rate's land off it, in Flow anywhere; in both a
        // burst's leave its outline.
        vec2 slots = vec2(textureSize(sTD2DInputs[0], 0));
        float free_slots = slots.x * slots.y * (1.0 - texelFetch(sTD2DInputs[7], ivec2(0), 0).a);
        bool outline = mode != 0 || uEmit.w > 0.5;
        float off = mode == 0 ? 0.0 : uEmit.x / max(free_slots * (mode == 1 ? 1.0 - cover.r : 1.0), 1.0);
        float on = (mode == 0 ? uEmit.x + uWave.w : uWave.w) / max(free_slots * (outline ? cover.g : cover.r), 1.0);
        float r = roll(dice);
        if (r < off) {
            vec2 uv = vec2(roll(dice), roll(dice));
            if (mode == 1 && texture(sTD2DInputs[4], uv).r >= 0.5) {
                free_slot();
                return;
            }
            born(uv, vec2(0.0), 0.0, dice);
            return;
        }
        if (r >= off + on) {
            free_slot();
            return;
        }
        vec2 esize = vec2(textureSize(sTD2DInputs[4], 0));
        vec2 uv = (floor(vec2(roll(dice), roll(dice)) * esize) + vec2(roll(dice), roll(dice))) / esize;
        vec4 e = texture(sTD2DInputs[4], uv);
        if ((outline ? e.g : e.r) < 0.5) {
            free_slot();
            return;
        }
        // Outward: down the slope of the blurred subject; where it's flat, any way.
        vec2 slope = subject(to_world(uv)).yz;
        float a = 6.2831853 * roll(dice);
        vec2 any_way = vec2(cos(a), sin(a));
        vec2 out_dir = length(slope) > 1e-3 ? -normalize(slope) : any_way;
        vec2 dir = normalize(mix(out_dir, any_way, 0.4) + 1e-5);
        // A burst's share of these births are sparks (all of them in Push and Flow), on the beats the
        // flash gate let through.
        float spark = uLook.w > 0.5 && roll(dice) * (mode == 0 ? uEmit.x + uWave.w : uWave.w) < uWave.w ? 1.0 : 0.0;
        born(uv, dir * uEmit.z * (0.3 + 0.9 * roll(dice)) * (1.0 + 2.0 * uMove.w), spark, dice);
        return;
    }

    // Alive: age, move, fade.
    float age = s1.x + dt, life = s1.y;
    vec2 w = s0.xy, v = s0.zw;
    if (age >= life) {
        free_slot();
        return;
    }
    // Outward from the subject's middle: a drop's shockwave, a ring leaving the middle that shoves what
    // it passes, and in Emit every particle on a beat.
    vec2 mid = cover.r > 1e-4 ? to_world(cover.ba / cover.r) : vec2(0.0);
    vec2 r = w - mid;
    float d = length(r);
    float band = exp(-pow((d - uWave.x) / 0.08, 2.0));
    vec2 outward = (d > 1e-4 ? r / d : vec2(0.0)) * (band * uWave.y * 6.0 + (mode == 0 ? uMove.w * KICK : 0.0));
    float shove = s3.r * exp(-dt / SHOVE_FADE);
    float behind = 0.0;   // Flow: how far the subject covers it
    if (mode == 0) {
        // Drift is the speed the wind blows at (along Direction, swung aside on each bar): a particle
        // eases to it over about a second, and the turbulence pushes it around on top.
        v = mix(v, uMove.x * vec2(sin(uWave.z), cos(uWave.z)), 1.0 - exp(-dt / 0.8));
        v += swirl(w, uClock.y) * uMove.y * 0.3 * dt;
        v += outward * dt;
        w += v * dt;
        if (abs(w.x) > 0.5 * uClock.w + 0.1 || abs(w.y) > 0.6) {
            free_slot();
            return;
        }
    } else {
        // The air's speed halfway along this frame's step, so particles keep to curving streamlines.
        v = v * exp(-dt / (mode == 1 ? SETTLE_PUSH : SETTLE_FLOW)) + outward * dt;
        vec2 half_way = air(w + (air(w) + v) * 0.5 * dt);
        w += (half_way + v) * dt + r * uLook.z;
        // Push: inside the subject's edge, back onto it, straight out (down the slope); deep inside,
        // where there is no slope to follow, the particle is gone.
        vec3 s = subject(w);
        if (mode == 1 && s.x > 0.5) {
            float g = length(s.yz);
            if (g < 0.5) {
                free_slot();
                return;
            }
            vec2 n = -s.yz / g;
            float back = min((s.x - 0.5) / g, 0.05);
            w += n * back;
            float speed = min(back / max(dt, 1e-3), SHOVE_MAX);
            v += n * speed;
            shove = max(shove, min(speed / SHOVE_LIT, 1.0));
        }
        behind = mode == 2 ? smoothstep(0.4, 0.6, s.x) : 0.0;
        vec2 half_frame = vec2(0.5 * uClock.w, 0.5);
        w = mod(w + half_frame, 2.0 * half_frame) - half_frame;
    }
    float seen = smoothstep(0.0, mode == 0 ? FADE_IN : FADE_IN_FIELD, age) * (1.0 - smoothstep(0.5, 1.0, age / life));
    float spark = s3.b * exp(-dt / SPARK_FADE);
    float size = s3.g * (1.0 + SPARK * spark);
    if (mode == 1) {
        seen *= CALM + (1.0 - CALM) * max(shove, spark);
        size *= 1.0 + SWELL * shove;
    }
    seen *= 1.0 - behind;
    fragColor[0] = vec4(w, v);
    fragColor[1] = vec4(age, life, size, 1.0);
    fragColor[2] = vec4(s2.rgb, seen);
    fragColor[3] = vec4(shove, s3.g, spark, 0.0);
}
