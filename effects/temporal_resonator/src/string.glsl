// touchdesigner-effects (MIT), Temporal Resonator: every pixel a plucked string, after Karplus and Strong ("Digital
// Synthesis of Plucked-String and Drum Timbres", Computer Music Journal 7(2), 1983) and Jaffe and Smith's extensions
// ("Extensions of the Karplus-Strong Plucked-String Algorithm", same issue). A string's state runs round a delay line
// one period long; what comes back is averaged with its neighbor in time, which takes the high harmonics away first,
// and scaled by the loop's gain, so the tone repeats every period, fainter and softer each time. Here the period is a
// beat (or Length of one), the averaging spans a little time either side (taps.glsl) and a little of the picture
// around each pixel (Softness), and the pluck is what differs from the background, fed in for the beat after each beat
// (or all the time): so whatever moves comes round again on the next beat, and the next, softer and fainter. A
// negative gain inverts every trip round (Alternating), as a pipe closed at one end reflects a wave, so the echoes
// alternate between the picture's difference and its opposite.
// Inputs: sTD2DInputs[0] the picture, [1] the background (background.glsl), [2] the taps (taps.glsl), [3] the stamp
// (stamp.glsl); sTD2DArrayInputs[0] the ring of the string's states.
// Out, at the ring's size: buffer 0 the string's state this cook (rgb, signed; a 1), which goes round the ring; buffer
// 1 rgb the echo coming back this cook (signed), a how much stands out from the background here now (0-1), which the
// echoes go behind.
uniform vec4 uS;   // x the loop's gain (negative: Alternating), y the pluck now (0-1.5), z Softness: the spread across
                   // the picture (pixels of the ring), w Threshold
out vec4 fragColor[TD_NUM_COLOR_BUFFERS];

vec3 stateAt(float slot, vec2 uv, vec2 o) {
    vec3 c = 0.4 * texture(sTD2DArrayInputs[0], vec3(uv, slot)).rgb;
    c += 0.15 * texture(sTD2DArrayInputs[0], vec3(uv + o, slot)).rgb;
    c += 0.15 * texture(sTD2DArrayInputs[0], vec3(uv - o, slot)).rgb;
    c += 0.15 * texture(sTD2DArrayInputs[0], vec3(uv + vec2(o.x, -o.y), slot)).rgb;
    c += 0.15 * texture(sTD2DArrayInputs[0], vec3(uv - vec2(o.x, -o.y), slot)).rgb;
    return c;
}

vec3 tap(int i, vec2 uv, vec2 o) {
    vec4 t = texelFetch(sTD2DInputs[2], ivec2(i, 0), 0);
    if (t.a < 0.5) return vec3(0.0);
    return mix(stateAt(t.r, uv, o), stateAt(t.g, uv, o), t.b);
}

float differs(vec2 uv) {
    vec3 e = texture(sTD2DInputs[0], uv).rgb - texture(sTD2DInputs[1], uv).rgb;
    return max(abs(e.r), max(abs(e.g), abs(e.b)));
}

void main() {
    vec2 uv = vUV.st;
    vec2 o = uS.z * uTDOutputInfo.res.xy;
    vec4 st = texelFetch(sTD2DInputs[3], ivec2(0), 0);
    vec3 e = texture(sTD2DInputs[0], uv).rgb - texture(sTD2DInputs[1], uv).rgb;
    float mag = max(abs(e.r), max(abs(e.g), abs(e.b)));
    // Faint differences (drifting smoke, the picture's noise) don't pluck the string.
    float core = smoothstep(uS.w, uS.w + 0.08, mag);
    // What stands out now, a pixel and a half wider all round, so no echo shows inside its edge.
    vec2 w = 1.5 * uTDOutputInfo.res.xy;
    float near = max(max(differs(uv + w), differs(uv - w)), max(differs(uv + vec2(w.x, -w.y)), differs(uv - vec2(w.x, -w.y))));
    float live = smoothstep(uS.w, uS.w + 0.1, max(mag, near));
    // Input 3's subject, an eighth-size pixel wider all round, its edge softened by reading between pixels.
    vec2 q = 1.0 / vec2(textureSize(sTD2DInputs[4], 0));
    float front = max(max(texture(sTD2DInputs[4], uv + q).r, texture(sTD2DInputs[4], uv - q).r),
                      max(texture(sTD2DInputs[4], uv + vec2(q.x, -q.y)).r, texture(sTD2DInputs[4], uv - vec2(q.x, -q.y)).r));
    live = max(live, front);
    vec3 r = vec3(0.0);
    if (st.b < 0.5) r = uS.x * (0.25 * tap(0, uv, o) + 0.5 * tap(1, uv, o) + 0.25 * tap(2, uv, o));
    vec3 s = st.b > 0.5 ? vec3(0.0) : clamp(uS.y * core * e + r, -2.0, 2.0);
    fragColor[0] = vec4(s, 1.0);
    fragColor[1] = vec4(r, live);
}
