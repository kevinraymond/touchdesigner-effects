// Particles (touchdesigner-effects, MIT). The subject: where particles may come from, by Find.
// Auto takes the depth on input 3 (Stand Out) when input 3 carries any, and what moves when it
// doesn't (nothing wired, or a black picture there); while TouchDesigner's sample movie shows
// (nothing on input 1), which barely moves, it reads the sample's brightness as depth instead.
// Stand Out and Nearer Than read the depth (input 1's brightness with nothing on input 3); Movement
// what moves; Background what differs from the empty room, once Capture Background has been pressed
// (until then, what moves). Every pixel also carries
// which of these is in use, for the label in the Subject view.
// Inputs: 0 the people in the depth (find.glsl); 1 what moves (motion.glsl); 2 the empty room
// (plate.glsl); 3 the picture, small (small.glsl); 4 the depth's largest nearness (an Analyze TOP);
// 5 the camera's exposure drift since the capture (drift.glsl: r a log brightness ratio).
// Out: r 1 inside the subject, else 0; g the depth's nearness where the depth is in use; b which way
// it was found (look.glsl's labels: 0 Auto, depth; 1 Auto, no depth; 2 Stand Out; 3 Nearer Than; 4
// and 5 the same on brightness; 6 Movement; 7 Background; 8 Background before a capture; 9 input 3
// all black; 10 Auto on the sample movie, brightness as depth).
uniform vec4 uFind;   // x Find (0 Auto, 1 Stand Out, 2 Nearer Than, 3 Movement, 4 Background), y 1 when
                      // something is wired into input 3, z how far from the background or the empty
                      // room counts (luma), w 1 when something is wired into input 1
out vec4 fragColor;

float moving(ivec2 p) {          // what moved lately, here or next door (joins up specks)
    ivec2 size = textureSize(sTD2DInputs[1], 0);
    float m = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            m = max(m, texelFetch(sTD2DInputs[1], clamp(p + ivec2(x, y), ivec2(0), size - 1), 0).b);
    return m > 0.5 ? 1.0 : 0.0;
}

float in_depth(ivec2 p) {        // the depth's subject, without lone specks: a pixel stays when most of
    ivec2 size = textureSize(sTD2DInputs[0], 0);   // its 3 x 3 does, so a depth camera's stray "flying
    float n = 0.0;                                  // pixels" at edges drop out but a finger 2 wide stays
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++)
            n += texelFetch(sTD2DInputs[0], clamp(p + ivec2(x, y), ivec2(0), size - 1), 0).r;
    return n >= 4.5 ? 1.0 : 0.0;
}

// How far a color is from the empty room's: its hue (the share of each channel, which exposure leaves
// alone) and its brightness once the camera's exposure drift is divided out, whichever differs more.
float apart(vec3 now, vec3 room, float drift) {
    float ln = dot(now, vec3(0.2126, 0.7152, 0.0722)), lr = dot(room, vec3(0.2126, 0.7152, 0.0722));
    float bright = abs(log(max(ln, 0.01) / max(lr, 0.01)) - drift);
    // Dark colors have noisy hues: the floor under the sums keeps their hue from counting much.
    float hue = length(now / max(now.r + now.g + now.b, 0.3) - room / max(room.r + room.g + room.b, 0.3));
    return max(0.5 * bright, 2.0 * hue);
}

float changed(ivec2 p) {         // differs from the empty room, averaged over 3 x 3 against noise
    ivec2 size = textureSize(sTD2DInputs[3], 0);
    float drift = texelFetch(sTD2DInputs[5], ivec2(0), 0).r;
    float d = 0.0;
    for (int y = -1; y <= 1; y++)
        for (int x = -1; x <= 1; x++) {
            ivec2 q = clamp(p + ivec2(x, y), ivec2(0), size - 1);
            d += apart(texelFetch(sTD2DInputs[3], q, 0).rgb, texelFetch(sTD2DInputs[2], q, 0).rgb, drift);
        }
    return d / 9.0 > 1.5 * uFind.z ? 1.0 : 0.0;
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    int mode = int(uFind.x + 0.5);
    bool wired = uFind.y > 0.5;
    bool has_depth = wired && texelFetch(sTD2DInputs[4], ivec2(0), 0).r > 0.02;
    bool captured = texelFetch(sTD2DInputs[2], ivec2(0), 0).a > 0.5;
    int how;
    if (mode == 0) how = has_depth ? 0 : (uFind.w > 0.5 ? 1 : 10);
    else if (mode == 1 || mode == 2) how = wired ? (has_depth ? mode + 1 : 9) : mode + 3;
    else if (mode == 3) how = 6;
    else how = captured ? 7 : 8;
    vec4 f = texelFetch(sTD2DInputs[0], p, 0);
    float inside;
    if (how == 1 || how == 6 || how == 8) inside = moving(p);
    else if (how == 7) inside = changed(p);
    else inside = in_depth(p);
    bool depth_used = how == 0 || (how >= 2 && how <= 5) || how == 10;
    fragColor = vec4(inside, depth_used ? f.g : 0.0, float(how), 1.0);
}
