// touchdesigner-effects (MIT), Voxel Space: the camera, carried from frame to frame. World units: the picture is
// WORLD wide and as tall as its shape makes it, x across it and y up it (away from the camera at heading 0), z up.
//   Fly    up the picture, mirrored at its edges, weaving along a seam, banking into its turns, and keeping clear
//          of the ground ahead (climbing slowly, sinking more slowly), as Comanche's helicopter flew
//   Orbit  circling the picture, an island in a flat sea, looking down at its middle
//   Hover  standing off the picture's near edge and looking across it, swaying
// A beat dips the camera (uH.y, through the flash gate).
// Inputs: 0 the size (a 3 x 1 Constant TOP), 1 this pass's last frame, 2 the picture (for its shape), 3 the terrain
// (r height), 4 the picture's mean color (an Analyze TOP). Out: pixel 0 x, y, height, heading (radians); pixel 1 where the horizon is (a share of
// the view's height from its top), roll (radians), the distance flown (Fly) or the orbit's or the sway's phase, 1 once started; pixel 2 the sky's
// color at the horizon, eased over a second, and the beat's dip in world units (kept out of the height, which eases).
uniform vec4 uF;   // x Flight (0 Fly, 1 Orbit, 2 Hover), y the pace (Speed times the tempo's), z seconds since the
                   // last frame, w the clock (clock_seconds())
uniform vec4 uH;   // x the terrain's height at 1 (world units), y the beat's dip (0-1), z tan of half the view's
                   // width
out vec4 fragColor;

#define WORLD 1024.0
#define PI 3.14159265
// At pace 1: Fly's world units a second, Orbit's along its circle, Hover's sway in radians a second. Fly at 45 and
// then 70 streamed a bright, busy picture (a plaza from above) past fast enough to flash a second more than the clip.
#define FLY 28.0
#define ORBIT 45.0
#define SWAY 0.3

float ground(vec2 p, vec2 world) {
    vec2 uv = 1.0 - abs(mod(p / world, 2.0) - 1.0);   // mirrored, as Fly sees it
    return texture(sTD2DInputs[3], uv).r * uH.x;
}

void main() {
    int px = int(gl_FragCoord.x);
    vec2 pic = vec2(textureSize(sTD2DInputs[2], 0));
    float aspect = pic.x / pic.y;
    vec2 world = vec2(WORLD, WORLD * pic.y / pic.x);
    vec4 cam = texelFetch(sTD2DInputs[1], ivec2(0, 0), 0);
    vec4 aux = texelFetch(sTD2DInputs[1], ivec2(1, 0), 0);
    vec4 sky = texelFetch(sTD2DInputs[1], ivec2(2, 0), 0);
    bool first = aux.a < 0.5;
    float dt = uF.z, t = uF.w;
    float peak = uH.x;
    float dip = uH.y * (0.15 * peak + 15.0);
    float tanHalf = uH.z;
    float slope = aspect / (2.0 * tanHalf);      // rows (a share of the height) a unit of height drops at unit distance
    vec4 c0, c1;
    if (uF.x < 0.5) {
        // Fly: up the picture along a weave about the seam where it meets its mirror image, so what stands in the
        // middle of the picture passes on both sides at a distance, like an avenue (weaving about the middle itself
        // brushed past it, a blurred wall filling half the view), the weave a function of the distance flown (aux.z,
        // wrapped where the path repeats) and the heading along it.
        float period = 16.0 * world.y;             // the mirrored picture repeats every two; the weave every sixteen
        float s = first ? 0.0 : mod(aux.z + FLY * uF.y * dt, period);
        float a = 2.0 * PI / period;
        vec2 at = vec2(0.22 * WORLD * sin(5.0 * a * s) + 0.06 * WORLD * sin(13.0 * a * s + 1.0), s);
        float dx = 0.22 * WORLD * 5.0 * a * cos(5.0 * a * s) + 0.06 * WORLD * 13.0 * a * cos(13.0 * a * s + 1.0);
        float heading = atan(dx);
        float ddx = -0.22 * WORLD * 25.0 * a * a * sin(5.0 * a * s) - 0.06 * WORLD * 169.0 * a * a * sin(13.0 * a * s + 1.0);
        float turn = ddx / (1.0 + dx * dx) * FLY * uF.y;   // radians a second
        vec2 fwd = vec2(sin(heading), cos(heading)), side = vec2(fwd.y, -fwd.x);
        // Keep clear of the ground ahead, looking far ahead (about 23 s at the default speed) so the climbs can be
        // slow: on a bumpy land, climbing over each hill in half a second shifted the whole view down each time.
        float ahead = 0.0;
        for (int i = 0; i < 7; i++) {
            float d = 650.0 * float(i * i) / 36.0;
            for (int j = -1; j <= 1; j++) ahead = max(ahead, ground(at + fwd * d + side * (0.35 * d * float(j)), world));
        }
        float want = ahead + 0.3 * peak + 35.0;
        float alt = first ? want : cam.z;
        alt += (want - alt) * (1.0 - exp(-dt / (want > alt ? 1.2 : 3.0)));
        c0 = vec4(at, alt, heading);
        c1 = vec4(0.40, -0.6 * turn, s, 1.0);
    } else if (uF.x < 1.5) {
        // Orbit: around the island's middle at 0.62 of its width, looking down at it.
        float r = 0.62 * WORLD;
        float phase = first ? 0.0 : mod(aux.z + ORBIT * uF.y * dt / r, 2.0 * PI);
        vec2 fwd = vec2(sin(phase), cos(phase));
        float alt = 0.5 * peak + 240.0;
        c0 = vec4(world * 0.5 - fwd * r, alt, phase);
        c1 = vec4(0.55 - alt / r * slope, 0.0, phase, 1.0);
    } else {
        // Hover: just off the near edge, swaying from side to side (in about 20 s at pace 1).
        float phase = first ? 0.0 : mod(aux.z + SWAY * uF.y * dt, 2.0 * PI);
        float alt = 0.4 * peak + 90.0;
        float back = 0.1 * world.y;
        c0 = vec4(world.x * (0.5 + 0.12 * sin(phase)), -back, alt, -0.18 * sin(phase));
        c1 = vec4(0.5 - alt / (back + 0.5 * world.y) * slope, 0.05 * sin(phase), phase, 1.0);
    }
    if (px == 0) {
        fragColor = c0;
    } else if (px == 1) {
        fragColor = c1;
    } else {
        vec3 mean = texelFetch(sTD2DInputs[4], ivec2(0), 0).rgb;
        vec3 want = clamp(mean * 1.5 + 0.06, 0.0, 1.0);
        fragColor = vec4(first ? want : mix(sky.rgb, want, 1.0 - exp(-dt / 1.0)), dip);
    }
}
