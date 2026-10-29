// Film Stock (touchdesigner-effects, MIT). The screen: the print's light, flickering as a projector's lamp and shutter
// make it (a slow breathing and a frame-to-frame unevenness, never more than 5% of the light, under the 10% WCAG
// counts as a change), with the dirt a print picks up: specks and hairs that land on one frame and are gone on the
// next (white, dirt on the negative when it was printed; black, dirt on the print), and scratches, lines down the
// picture that last a second or two and wander a little, light where the base is scratched and dark where the
// emulsion is. A cue mark, the circle at the top right that warned the projectionist of a reel's end, shows for a few
// frames on each section change. Then the red guard (a halo is red, and WCAG counts a saturated red flashing on its
// own) and sRGB.
// Inputs: 0 the print (linear). Out: the picture.
uniform vec4 uD;      // x Flicker 0-1, y Dirt 0-1, z the cue mark (0-1), w unused
out vec4 fragColor;
#define FLICKER 0.04      // at Flicker 1: the light swings this much, plus a quarter of it frame to frame
#define SPECKS 0.08       // specks a cell a frame at Dirt 1 (cells of 48 pixels at 720 high)
#define SCRATCHES 3       // scratches that may run at once
#define SCRATCH_S 2.0     // seconds a scratch's life is judged over

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 p = gl_FragCoord.xy, q = p * 720.0 / res.y;          // in pixels at 720 high
    float t = uF.y;
    uint f = frameSeed();
    vec3 L = max(texture(sTD2DInputs[0], vUV.st).rgb, 0.0);
    // Flicker.
    float fl = FLICKER * uD.x * (0.75 * (0.6 * wave(t * 2.5, 31u) + 0.4 * wave(t * 6.0, 32u)) + 0.25 * (die(f, 3u, 33u) * 2.0 - 1.0));
    L *= 1.0 + fl;
    // Specks and hairs: each cell may hold one this frame.
    float dirt = uD.y;
    if (dirt > 0.0) {
        ivec2 cell = ivec2(floor(q / 48.0));
        float mark = 0.0, light = 0.0;
        for (int j = -1; j <= 1; j++)
        for (int i = -1; i <= 1; i++) {
            ivec2 c = cell + ivec2(i, j);
            uint a = uint(c.x + 64) * 256u + uint(c.y + 64);
            if (die(a, f, 41u) >= SPECKS * dirt) continue;
            vec2 at = (vec2(c) + vec2(die(a, f, 42u), die(a, f, 43u))) * 48.0;
            float kind = die(a, f, 44u);
            float m;
            if (kind < 0.6) {                               // a speck
                float r = 0.7 + 2.5 * die(a, f, 45u) * die(a, f, 46u);
                vec2 e = vec2(1.0, 0.6 + 0.4 * die(a, f, 47u));
                m = 1.0 - smoothstep(r - 0.7, r + 0.7, length((q - at) * e));
            } else {                                        // a hair: a short bent line
                float ang = 2.0 * PI * die(a, f, 48u), len = 8.0 + 40.0 * die(a, f, 49u);
                vec2 dir = vec2(cos(ang), sin(ang)), rel = q - at;
                float s = clamp(dot(rel, dir), 0.0, len);
                vec2 along = at + dir * s + vec2(-dir.y, dir.x) * 6.0 * sin(s / len * PI) * (die(a, f, 50u) - 0.5);
                m = 1.0 - smoothstep(0.4, 1.2, length(q - along));
            }
            float lit = die(a, f, 51u) < 0.5 ? 1.0 : 0.0;
            mark = max(mark, m);
            light = max(light, m * lit);
        }
        L = mix(L, vec3(0.02), mark * (1.0 - light));
        L = mix(L, vec3(1.0), light);
    }
    // Scratches: a few lanes, each alive for a stretch of SCRATCH_S seconds when its die says so.
    if (dirt > 0.0) {
        for (int k = 0; k < SCRATCHES; k++) {
            uint ks = uint(k) + 60u;
            float epoch = floor(t / SCRATCH_S + float(k) * 0.37);
            uint es = uint(epoch);
            if (die(es, ks, 1u) >= 0.35 * dirt) continue;
            float x0 = die(es, ks, 2u) * res.x * 0.96 + 0.02 * res.x;
            float xw = x0 + (0.5 + 1.5 * die(es, ks, 3u)) * wave(t * 4.0, ks) * res.y / 720.0;
            float wd = (0.5 + 0.6 * die(es, ks, 4u)) * res.y / 720.0;
            float m = 1.0 - smoothstep(wd, wd + 0.8, abs(p.x - xw));
            m *= 0.4 + 0.6 * die(f, ks, 5u);                 // it flickers along its length frame to frame
            float lit = die(es, ks, 6u) < 0.6 ? 1.0 : 0.0;
            L = mix(L, lit > 0.5 ? L + vec3(0.6) : L * 0.25, m * (0.6 + 0.4 * dirt));
        }
    }
    // The cue mark: a circle at the top right.
    if (uD.z > 0.5) {
        vec2 at = vec2(res.x - 0.055 * res.y, res.y - 0.055 * res.y);
        float r = 0.02 * res.y;
        float m = 1.0 - smoothstep(r, r + 1.5, length(p - at));
        L = mix(L, vec3(0.03), 0.9 * m);
    }
    vec3 c = toSRGB(redGuard(clamp(L, 0.0, 1.0)));
    fragColor = vec4(c, 1.0);
}
