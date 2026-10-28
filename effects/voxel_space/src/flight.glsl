// touchdesigner-effects (MIT), Voxel Space: the camera, carried from frame to frame. World units: the picture is
// WORLD wide and as tall as its shape makes it, x across it and y up it (away from the camera at heading 0), z up.
//   Fly    up the picture, mirrored at its edges, weaving along a seam, banking into its turns, and keeping clear
//          of the ground ahead (climbing slowly, sinking more slowly), as Comanche's helicopter flew
//   Orbit  circling the picture, an island in a flat sea, looking down at its middle
//   Hover  standing off the picture's near edge and looking across it, swaying
// The camera's settings move and turn each flight's camera, eased toward them (uH.w): Position moves it across the
// land and Altitude scales its height above the ground, Yaw turns it, Pitch moves the horizon up or down and Roll
// slants it, as Comanche's did (the view is drawn in columns, so upright things stay upright), and Zoom narrows the
// view about its middle.
// A beat dips the camera (uH.y, through the flash gate).
// Inputs: 0 the size (a 5 x 1 Constant TOP), 1 this pass's last frame, 2 the picture (for its shape), 3 the terrain
// (r height), 4 the picture's mean color (an Analyze TOP). Out: pixel 0 x, y, height, heading (radians); pixel 1 where the horizon is (a share of
// the view's height from its top), roll (radians), the distance flown (Fly) or the orbit's or the sway's phase, 1 once started; pixel 2 the sky's
// color at the horizon, eased over a second, and the beat's dip in world units (kept out of the height, which eases);
// pixel 3 Yaw, Pitch and Roll (radians) and Zoom, eased; pixel 4 Position (picture widths and heights) and Altitude,
// eased.
uniform vec4 uF;   // x Flight (0 Fly, 1 Orbit, 2 Hover), y the pace (Speed times the tempo's), z seconds since the
                   // last frame, w the clock (clock_seconds())
uniform vec4 uH;   // x the terrain's height at 1 (world units), y the beat's dip (0-1), z tan of half the view's
                   // width at Zoom 1, w the time the camera's settings ease over (s)
uniform vec4 uC;   // Yaw, Pitch, Roll (degrees), Zoom
uniform vec4 uP;   // Position (x across the picture, y up it, in its widths and heights), Altitude
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

// The ground under the camera, the sea's (0) around Orbit's island.
float under(vec2 p, vec2 world, bool island) {
    vec2 uv = p / world;
    if (island && (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0))))) return 0.0;
    return ground(p, world);
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
    // The camera's settings, eased, Zoom by its logarithm so zooming in and out feel alike.
    vec4 aim = vec4(radians(uC.xyz), log(uC.w));
    vec3 place = uP.xyz;
    if (!first) {
        float k = 1.0 - exp(-dt / uH.w);
        vec4 was = texelFetch(sTD2DInputs[1], ivec2(3, 0), 0);
        aim = mix(vec4(was.xyz, log(was.w)), aim, k);
        place = mix(texelFetch(sTD2DInputs[1], ivec2(4, 0), 0).xyz, place, k);
    }
    float zoom = exp(aim.w);
    vec2 shift = place.xy * world;
    float tanHalf = uH.z / zoom;
    float slope = aspect / (2.0 * tanHalf);      // rows (a share of the height) a unit of height drops at unit distance
    float pitch = tan(aim.y) * slope;            // Pitch moves the horizon, as Comanche's did
    // Zoom slows the flight as it narrows the view, so the land crosses the view at the same pace: at Zoom 2, flying
    // as fast streamed a busy picture (a plaza from above) past fast enough to flash a second more than the clip.
    float pace = uF.y / max(zoom, 1.0);
    vec4 c0, c1;
    if (uF.x < 0.5) {
        // Fly: up the picture along a weave about the seam where it meets its mirror image, so what stands in the
        // middle of the picture passes on both sides at a distance, like an avenue (weaving about the middle itself
        // brushed past it, a blurred wall filling half the view), the weave a function of the distance flown (aux.z,
        // wrapped where the path repeats) and the heading along it.
        float period = 16.0 * world.y;             // the mirrored picture repeats every two; the weave every sixteen
        float s = first ? 0.0 : mod(aux.z + FLY * pace * dt, period);
        float a = 2.0 * PI / period;
        vec2 at = vec2(0.22 * WORLD * sin(5.0 * a * s) + 0.06 * WORLD * sin(13.0 * a * s + 1.0), s) + shift;
        float dx = 0.22 * WORLD * 5.0 * a * cos(5.0 * a * s) + 0.06 * WORLD * 13.0 * a * cos(13.0 * a * s + 1.0);
        float heading = atan(dx);
        float ddx = -0.22 * WORLD * 25.0 * a * a * sin(5.0 * a * s) - 0.06 * WORLD * 169.0 * a * a * sin(13.0 * a * s + 1.0);
        float turn = ddx / (1.0 + dx * dx) * FLY * pace;   // radians a second
        vec2 fwd = vec2(sin(heading), cos(heading)), side = vec2(fwd.y, -fwd.x);
        // Keep clear of the ground ahead, looking far ahead (about 23 s at the default speed) so the climbs can be
        // slow: on a bumpy land, climbing over each hill in half a second shifted the whole view down each time.
        float ahead = 0.0;
        for (int i = 0; i < 7; i++) {
            float d = 650.0 * float(i * i) / 36.0;
            for (int j = -1; j <= 1; j++) ahead = max(ahead, ground(at + fwd * d + side * (0.35 * d * float(j)), world));
        }
        float want = ahead + 8.0 + place.z * (0.3 * peak + 27.0);
        float alt = first ? want : cam.z;
        alt += (want - alt) * (1.0 - exp(-dt / (want > alt ? 1.2 : 3.0)));
        // A little below level (a tenth of the view at Zoom 1), so Zoom narrows the view about the same point.
        c0 = vec4(at, alt, heading + aim.x);
        c1 = vec4(0.5 - 0.1 * zoom + pitch, -0.6 * turn - aim.z, s, 1.0);
    } else if (uF.x < 1.5) {
        // Orbit: around the island's middle at 0.62 of its width, looking down at it, and never lower than just above
        // the ground under it, which Position can move it over (as it can Hover's).
        float r = 0.62 * WORLD;
        float phase = first ? 0.0 : mod(aux.z + ORBIT * pace * dt / r, 2.0 * PI);
        vec2 fwd = vec2(sin(phase), cos(phase));
        vec2 at = world * 0.5 + shift - fwd * r;
        float alt = max(8.0 + place.z * (0.5 * peak + 232.0), under(at, world, true) + 8.0);
        c0 = vec4(at, alt, phase + aim.x);
        c1 = vec4(0.55 - alt / r * slope + pitch, -aim.z, phase, 1.0);
    } else {
        // Hover: just off the near edge, swaying from side to side (in about 20 s at pace 1).
        float phase = first ? 0.0 : mod(aux.z + SWAY * pace * dt, 2.0 * PI);
        float back = 0.1 * world.y;
        vec2 at = vec2(world.x * (0.5 + 0.12 * sin(phase)), -back) + shift;
        float alt = max(8.0 + place.z * (0.4 * peak + 82.0), under(at, world, false) + 8.0);
        c0 = vec4(at, alt, -0.18 * sin(phase) + aim.x);
        c1 = vec4(0.5 - alt / (back + 0.5 * world.y) * slope + pitch, 0.05 * sin(phase) - aim.z, phase, 1.0);
    }
    if (px == 0) {
        fragColor = c0;
    } else if (px == 1) {
        fragColor = c1;
    } else if (px == 2) {
        vec3 mean = texelFetch(sTD2DInputs[4], ivec2(0), 0).rgb;
        vec3 want = clamp(mean * 1.5 + 0.06, 0.0, 1.0);
        fragColor = vec4(first ? want : mix(sky.rgb, want, 1.0 - exp(-dt / 1.0)), dip);
    } else if (px == 3) {
        fragColor = vec4(aim.xyz, zoom);
    } else {
        fragColor = vec4(place, 1.0);
    }
}
