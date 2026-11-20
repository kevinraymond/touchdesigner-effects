// Marbling (touchdesigner-effects, MIT): the live picture floated on the size with the tray's inks and combed. Every
// tool is a closed-form map of the tray onto itself that keeps areas, from S. Lu, A. Jaffer, X. Jin, H. Zhao and
// X. Mao, "Mathematical Marbling" (IEEE CG&A 32(6), 2012), and each is easy to undo. So a pixel's color is found by
// undoing the tools one by one, newest first: if the point lands inside a drop, it is that drop's ink; if it gets past
// every tool, it is the picture where the point started. That is the paper's second way to draw a marbling (after
// K. Sims, "Choreographed Image Flow", 1992): all the tools at once, from scratch, so nothing blurs however many there
// are, and nothing is carried over from the last frame.
//   drop: a drop of radius r at C pushes every point out, P' = C + (P - C) sqrt(1 + r^2 / |P - C|^2); undone,
//         Q -> C + (Q - C) sqrt(1 - r^2 / |Q - C|^2) for Q outside the drop. Its area grows with its strength, as
//         ink spreading from a dropper does.
//   comb: tines drawn along M pull the points near them along, P' = P + a l / (d + l) M, d the distance to the
//         nearest tine (the paper's equation 1, with its fmod for a comb); points move along M only, so undoing it
//         subtracts the same pull. Less its mean over a tine's spacing, (2 l / s) ln(1 + s / (2 l)), so a comb moves
//         the inks past each other without carrying the whole tray along (pst-marble's shift).
//   wave: P' = P + h sin(k (P . N) + phase) M, the paper's wavy pattern: with a comb, a comb drawn along a wave.
// Each tool's strength rises as it is made, holds, then relaxes to nothing (tray.py says when). Each pixel is four
// samples on a rotated grid (2 x 2 RGSS, as the paper's raster output), since the inks' edges and the combs' threads
// come out sharper than a pixel; each tool is worked out once a pixel and moves all four at once (as vectors: kept
// in arrays indexed in a loop, a full tray cost 8 ms). The tray runs on past
// the picture's edges, mirrored. With Keep Subject on and something on input 3, what stands out in front (or inside
// the mask) is the live picture.
// Inputs: 0 the picture, 1 the inks (ink.glsl), 2 what stands out (depth_find).
// Uniform arrays (tray.py's channels, a tool an element, newest first): uTa (kind, t0, rise, hold), uTb (relax, a, b,
// c), uTc (d, e, serial).
uniform vec4 uTa[64];
uniform vec4 uTb[64];
uniform vec3 uTc[64];
uniform vec4 uM;   // x the clock now (s, wrapped every CLOCK), y a drop's radius at full size (frame heights, Drop
                   // Size), z a comb's pull at full pull (frame heights, Comb), w how sharply a pull falls off from its
                   // tine (the paper's lambda, frame heights)
uniform vec4 uK;   // x Inks (0 Picture, 1 Ebru), y how much of the subject is kept clear (0 or 1)
out vec4 fragColor;

#define N 64
#define CLOCK 16384.0
const vec2 RGSS[4] = vec2[4](vec2(0.125, 0.375), vec2(-0.375, 0.125), vec2(-0.125, -0.375), vec2(0.375, -0.125));
// Ebru: traditional marbling pigments, in sRGB: indigo, ochre, rose madder (well short of WCAG's red line), an
// off-white, umber, a sea green.
const vec3 EBRU[6] = vec3[6](vec3(0.16, 0.20, 0.42), vec3(0.80, 0.62, 0.25), vec3(0.75, 0.38, 0.42),
                             vec3(0.93, 0.90, 0.82), vec3(0.33, 0.24, 0.17), vec3(0.25, 0.48, 0.45));

vec3 ink(int serial) {
    if (uK.x > 0.5)
        return EBRU[serial % 6];
    return texelFetch(sTD2DInputs[1], ivec2(serial % N, 0), 0).rgb;
}

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    float aspect = res.x / res.y;
    // The four samples side by side in vectors, x in px and y in py, so each tool moves all four at once.
    vec4 px = (gl_FragCoord.x + vec4(RGSS[0].x, RGSS[1].x, RGSS[2].x, RGSS[3].x)) / res.y;
    vec4 py = (gl_FragCoord.y + vec4(RGSS[0].y, RGSS[1].y, RGSS[2].y, RGSS[3].y)) / res.y;
    vec4 left = vec4(1.0);     // 1 for a sample still undoing tools, 0 once it has landed in a drop
    vec3 sum = vec3(0.0);      // the inks the samples landed in
    float lam = uM.w;
    for (int i = 0; i < N; i++) {
        vec4 ta = uTa[i];
        if (ta.x == 0.0 || left == vec4(0.0))
            break;
        float age = mod(uM.x - ta.y + CLOCK, CLOCK);
        vec4 tb = uTb[i];
        float s = smoothstep(0.0, max(ta.z, 1e-3), age) * (1.0 - smoothstep(ta.w, ta.w + max(tb.x, 1e-3), age));
        if (s <= 0.0)
            continue;
        vec3 tc = uTc[i];
        if (ta.x == 1.0) {
            float cx = tb.y * aspect, cy = tb.z;
            float r = uM.y * tb.w, r2 = r * r * s;
            vec4 qx = px - cx, qy = py - cy;
            vec4 q2 = qx * qx + qy * qy;
            vec4 hit = left * step(q2, vec4(r2));
            float hits = dot(hit, vec4(1.0));
            if (hits > 0.0) {
                sum += hits * ink(int(tc.z));
                left -= hit;
            }
            vec4 k = sqrt(max(1.0 - r2 / max(q2, 1e-12), 0.0));
            px = cx + qx * k;
            py = cy + qy * k;
        } else if (ta.x == 2.0) {
            float mx = tb.y, my = tb.z;
            float sp = tb.w, pull = uM.z * tc.y * s;
            float mean = 2.0 * lam / sp * log(1.0 + sp / (2.0 * lam));
            vec4 d = mod(px * -my + py * mx + tc.x, sp);
            d = 0.5 * sp - abs(d - 0.5 * sp);
            vec4 shift = pull * (lam / (d + lam) - mean);
            px -= shift * mx;
            py -= shift * my;
        } else {
            float mx = tb.y, my = tb.z;
            float h = tb.w * s, kw = 6.2831853 / max(tc.x, 1e-3);
            vec4 shift = h * sin(kw * (px * -my + py * mx) + tc.y);
            px -= shift * mx;
            py -= shift * my;
        }
    }
    // The samples that got past every tool take the picture where they started.
    vec4 u = 1.0 - abs(mod(px / aspect, 2.0) - 1.0), v = 1.0 - abs(mod(py, 2.0) - 1.0);
    for (int k = 0; k < 4; k++)
        sum += left[k] * texture(sTD2DInputs[0], vec2(u[k], v[k])).rgb;
    vec3 c = 0.25 * sum;
    if (uK.y > 0.0) {
        float keep = uK.y * texture(sTD2DInputs[2], vUV.st).r;
        c = mix(c, texture(sTD2DInputs[0], vUV.st).rgb, keep);
    }
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}
