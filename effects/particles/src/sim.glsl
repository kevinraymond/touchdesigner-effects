// Particles (touchdesigner-effects, MIT). The particles: one per pixel of three 32-bit float
// buffers, which this shader reads back each frame through Feedback TOPs and moves on.
// A free particle is born with a chance that makes the frame's births come to the number asked for
// (Rate, more on a beat): it picks a random pixel of the subject (or its outline) and is born there
// if the pixel is one, takes the picture's color there, and leaves the body outward. A living one
// ages, rides the wind (Drift, its direction swung by the bars), swirls in the turbulence (curl
// noise: a swirling flow that never piles particles up), is kicked outward from the subject on each
// beat and by a drop's shockwave, fades in, and fades out over the second half of its life. Positions are in frame heights from the middle of the frame (x across, y up), which is
// how the Geometry COMP draws them; sizes are in frame heights too.
// Inputs: 0, 1, 2 this TOP's three buffers last frame; 3 where particles may be born (emit.glsl);
// 4 the subject, blurred (its outward direction); 5 the picture (their colors); 6 the average of
// buffer 1 last frame (a: how many are alive); 7 the average of input 3 (how much of the frame the
// emitters cover, and the subject's middle).
// Out: buffer 0 x, y, x speed, y speed; buffer 1 age (s), life (s), size, 1 alive or 0 free;
// buffer 2 color r, g, b, and a: how visible it is now.
uniform vec4 uClock;  // x seconds since the last frame, y seconds, z frame number (the dice), w aspect (width / height)
uniform vec4 uEmit;   // x births asked for this frame, y Life (s), z Speed, w 1 born on the outline only
uniform vec4 uMove;   // x Drift, y Turbulence, z Size (frame heights), w beat kick 0-1
uniform vec4 uWave;   // x shockwave radius (frame heights), y strength 0-1, z the wind's angle from straight up (radians)
uniform vec4 uLook;   // x Color (0 picture, 1 orange, 2 blue, 3 white)
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];
#define KICK 4.0   // a beat's push outward, frame heights per second per second at the beat's peak

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

void free_slot() {
    fragColor[0] = vec4(0.0);
    fragColor[1] = vec4(0.0);
    fragColor[2] = vec4(0.0);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float dt = min(uClock.x, 0.1);           // after a stall, don't jump
    vec4 s0 = texelFetch(sTD2DInputs[0], p, 0);
    vec4 s1 = texelFetch(sTD2DInputs[1], p, 0);
    vec4 s2 = texelFetch(sTD2DInputs[2], p, 0);
    uint dice = hash(uint(p.x) + 4096u * uint(p.y) + hash(uint(uClock.z)));

    if (s1.a < 0.5) {
        // Free: born this frame? Births asked for / free slots whose random pixel is an emitter.
        vec2 slots = vec2(textureSize(sTD2DInputs[0], 0));
        float free_share = 1.0 - texelFetch(sTD2DInputs[6], ivec2(0), 0).a;
        vec4 cover = texelFetch(sTD2DInputs[7], ivec2(0), 0);
        float chances = slots.x * slots.y * free_share * (uEmit.w > 0.5 ? cover.g : cover.r);
        if (roll(dice) >= uEmit.x / max(chances, 1.0)) {
            free_slot();
            return;
        }
        vec2 esize = vec2(textureSize(sTD2DInputs[3], 0));
        vec2 uv = (floor(vec2(roll(dice), roll(dice)) * esize) + vec2(roll(dice), roll(dice))) / esize;
        vec4 e = texture(sTD2DInputs[3], uv);
        if ((uEmit.w > 0.5 ? e.g : e.r) < 0.5) {
            free_slot();
            return;
        }
        // Outward: down the slope of the blurred subject; where it's flat, any way.
        vec2 px = 1.0 / vec2(textureSize(sTD2DInputs[4], 0));
        vec2 slope = vec2(texture(sTD2DInputs[4], uv + vec2(px.x, 0.0)).r - texture(sTD2DInputs[4], uv - vec2(px.x, 0.0)).r,
                          texture(sTD2DInputs[4], uv + vec2(0.0, px.y)).r - texture(sTD2DInputs[4], uv - vec2(0.0, px.y)).r);
        float a = 6.2831853 * roll(dice);
        vec2 any_way = vec2(cos(a), sin(a));
        vec2 out_dir = length(slope) > 1e-4 ? -normalize(slope) : any_way;
        vec2 dir = normalize(mix(out_dir, any_way, 0.4) + 1e-5);
        float speed = uEmit.z * (0.3 + 0.9 * roll(dice)) * (1.0 + 2.0 * uMove.w);
        vec3 c = texture(sTD2DInputs[5], uv).rgb;
        if (uLook.x < 0.5) {
            // The picture's color, lifted so dark clothes still glow: brightest channel to at least 0.6.
            c *= max(0.6, max(c.r, max(c.g, c.b))) / max(max(c.r, max(c.g, c.b)), 0.02);
        } else {
            c = uLook.x < 1.5 ? vec3(1.0, 0.55, 0.15) : uLook.x < 2.5 ? vec3(0.25, 0.55, 1.0) : vec3(1.0);
        }
        float life = uEmit.y * (0.5 + roll(dice));
        float size = uMove.z * (0.6 + 0.8 * roll(dice));
        fragColor[0] = vec4(to_world(uv), dir * speed);
        fragColor[1] = vec4(0.0, life, size, 1.0);
        fragColor[2] = vec4(min(c, vec3(1.0)), 0.0);
        return;
    }

    // Alive: age, move, fade.
    float age = s1.x + dt, life = s1.y;
    vec2 w = s0.xy, v = s0.zw;
    if (age >= life) {
        free_slot();
        return;
    }
    // Drift is the speed the wind blows at (up, swung aside on each bar): a particle eases to it over
    // about a second, and the turbulence pushes it around on top.
    v = mix(v, uMove.x * vec2(sin(uWave.z), cos(uWave.z)), 1.0 - exp(-dt / 0.8));
    v += swirl(w, uClock.y) * uMove.y * 0.3 * dt;
    // Outward from the subject's middle: every particle on a beat, and a drop's shockwave, a ring
    // leaving the middle that shoves what it passes.
    vec4 cover = texelFetch(sTD2DInputs[7], ivec2(0), 0);
    vec2 mid = cover.r > 1e-4 ? to_world(cover.ba / cover.r) : vec2(0.0);
    vec2 r = w - mid;
    float d = length(r);
    float band = exp(-pow((d - uWave.x) / 0.08, 2.0));
    v += (d > 1e-4 ? r / d : vec2(0.0)) * (band * uWave.y * 6.0 + uMove.w * KICK) * dt;
    w += v * dt;
    if (abs(w.x) > 0.5 * uClock.w + 0.1 || abs(w.y) > 0.6) {
        free_slot();
        return;
    }
    float seen = smoothstep(0.0, 0.12, age) * (1.0 - smoothstep(0.5, 1.0, age / life));
    fragColor[0] = vec4(w, v);
    fragColor[1] = vec4(age, life, s1.z, 1.0);
    fragColor[2] = vec4(s2.rgb, seen);
}
