// Particles (touchdesigner-effects, MIT). What moves, for Find on Movement (and Auto with no depth):
// each pixel keeps a background that follows the picture a couple of seconds behind, and counts as
// moving while the picture differs from it by more than Sensitivity allows. Where a pixel has stayed
// still for a moment the background catches up quickly, so the place someone has just left stops
// counting within about a second instead of trailing them as a ghost; someone who holds still fades
// out the same way. A pixel that moved keeps counting for TRAIL seconds, so particles keep coming off
// a gesture rather than flickering with it.
// Inputs: 0 the picture, small (small.glsl: a is luma); 1 this TOP's last frame (a Feedback TOP).
// Out: r the luma last frame, g the background, b how much it moved lately (0-1), a seconds it has
// stayed still (-1 before the first frame).
uniform vec4 uMotion;  // x seconds since the last frame, y how far from the background counts as moving (luma)
#define SLOW 2.0       // seconds the background takes to follow the picture
#define FAST 0.25      // the same, where a pixel has stayed still STILL_FOR seconds
#define STILL 0.02     // a pixel that changes less than this between frames is still
#define STILL_FOR 0.5
#define TRAIL 0.5      // seconds a pixel keeps counting after it last moved
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    float dt = min(uMotion.x, 0.1);
    float cur = texelFetch(sTD2DInputs[0], p, 0).a;
    vec4 old = texelFetch(sTD2DInputs[1], p, 0);
    if (old.a < -0.5) {                       // the first frame: the picture is the background
        fragColor = vec4(cur, cur, 0.0, 0.0);
        return;
    }
    float still = abs(cur - old.r) < STILL ? old.a + dt : 0.0;
    float bg = mix(old.g, cur, 1.0 - exp(-dt / (still >= STILL_FOR ? FAST : SLOW)));
    float d = abs(cur - bg);
    float moved = max(old.b * exp(-3.0 * dt / TRAIL), smoothstep(uMotion.y, 2.0 * uMotion.y, d));
    fragColor = vec4(cur, bg, moved, still);
}
