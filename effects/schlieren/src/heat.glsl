// Schlieren (touchdesigner-effects, MIT): the heat the air carries, at twice the air's size so its edges stay finer
// than the air's cells. It is carried by MacCormack's step (A. Selle, R. Fedkiw, B. Kim, Y. Liu, J. Rossignac, "An
// Unconditionally Stable MacCormack Method", J. Sci. Comput. 35, 2008): what was where the air came from, corrected by
// half the error a step back and forth makes, and kept within the four cells it came from. That keeps the heat's edges
// sharp where a plain step back (semi-Lagrangian) blurs them a little every frame, and the edges are what the camera
// sees. Then it is heated where the picture is warm, up to how warm it is there, and cools as the warm air mixes into
// the room. The music sets how fast it heats: louder is hotter, and each of its seven bands heats one height of the
// frame, the lowest at the bottom (the feet) and the highest at the top (the head). A beat's puff heats it faster for
// a moment. The heat is what the camera sees, and only through how it bends the light; it never pushes the air
// (lift.glsl).
// Inputs: 0 the picture (sets the size: Output Resolution Half), 1 the heat last frame (Feedback TOP), 2 the air's
// velocity (lib incompressible(): rg cells a second at its own size), 3 the warmth, smoothed (lift.glsl: b 0-1), 4 how
// much of the picture is warm (air.glsl: a puff is weaker where more of it is).
// Out: r the heat 0-1.
uniform vec4 uH;    // x this frame's step (s), y how fast a warm source heats the air (a second), z the heat's
                    // half-life once carried away (s), w a beat's puff now (how many times faster it heats)
uniform vec4 uB0;   // the bands: sub_bass, bass, low_mid, mid (0-1)
uniform vec4 uB1;   // upper_mid, presence, brilliance (0-1), w Band Heights 0-1
out vec4 fragColor;
#define PUFF_AREA 0.05   // as air.glsl

// The bands at a height (0 the bottom, 1 the top), each centered on its seventh of the frame.
float band(float y) {
    float b[7] = float[7](uB0.x, uB0.y, uB0.z, uB0.w, uB1.x, uB1.y, uB1.z);
    float k = clamp(y * 7.0 - 0.5, 0.0, 6.0);
    int i = int(floor(k));
    return mix(b[i], b[min(i + 1, 6)], k - float(i));
}

float last(vec2 p) { return texture(sTD2DInputs[1], p).r; }
vec2 travel(vec2 p, float dt) { return dt * texture(sTD2DInputs[2], p).rg * uTD2DInfos[2].res.xy; }

void main() {
    vec2 uv = vUV.st;
    float dt = uH.x;
    vec2 back = uv - travel(uv, dt);
    float ahead = last(back);                                  // a step back along the air
    vec2 fwd = uv + travel(uv, dt);
    float again = last(fwd - travel(fwd, dt));                   // ... and that step's own error, a step forward and back
    float heat = ahead + 0.5 * (last(uv) - again);
    // Within the four cells the step back read from, so the correction never overshoots (Selle et al.'s clamp).
    vec2 res = uTD2DInfos[1].res.zw;
    vec2 cell = (floor(back * res - 0.5) + 0.5) / res;
    vec2 o = 1.0 / res;
    float a = last(cell), b = last(cell + vec2(o.x, 0.0)), c = last(cell + vec2(0.0, o.y)), d = last(cell + o);
    heat = clamp(heat, min(min(a, b), min(c, d)), max(max(a, b), max(c, d)));
    // A warm source's edge sharpened, so the air it heats has an edge to see.
    float src = smoothstep(0.25, 0.55, texture(sTD2DInputs[3], uv).b);
    float puff = uH.w * min(1.0, PUFF_AREA / max(texelFetch(sTD2DInputs[4], ivec2(0), 0).r, 1e-4));
    float rate = uH.y * (1.0 + uB1.w * (2.0 * band(uv.y) - 1.0)) * (1.0 + puff);
    heat += (1.0 - exp(-dt * rate * src)) * max(src - heat, 0.0);
    heat *= exp2(-dt / uH.z);
    fragColor = vec4(heat, 0.0, 0.0, 1.0);
}
