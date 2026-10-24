// Particles (touchdesigner-effects, MIT). How far the camera's exposure has drifted since Capture
// Background, for Find on Background: webcams adjust it by themselves, most of all when someone steps
// in and fills the frame, and without this the whole empty room would then differ from the picture.
// A histogram of log(brightness now / brightness in the empty room) over the frame: the room is most
// of the picture, so its ratio is the tallest bin (drift.glsl picks it), whatever the subject does.
// (An average over last frame's background drifted into calling the room the subject and calibrating
// on the subject instead, and stayed there.)
// Each output pixel counts one bin along one sampled row, so the work spreads over thousands of
// pixels (one pixel per bin looping over the whole frame took 5 ms); gain_sum adds up the rows.
// Inputs: 0 the picture, small (small.glsl: a is luma); 1 the empty room (plate.glsl).
// Out: x the bin (BINS across log ratios -RANGE to RANGE), y the row (every STEP-th); r how many
// sampled pixels of that row fall in that bin.
#define BINS 64
#define RANGE 2.0
#define STEP 2         // sample every STEP-th pixel each way
out vec4 fragColor;

void main() {
    int bin = int(gl_FragCoord.x);
    int y = int(gl_FragCoord.y) * STEP;
    int w = textureSize(sTD2DInputs[0], 0).x;
    float n = 0.0;
    for (int x = 0; x < w; x += STEP) {
        float now = texelFetch(sTD2DInputs[0], ivec2(x, y), 0).a;
        float room = dot(texelFetch(sTD2DInputs[1], ivec2(x, y), 0).rgb, vec3(0.2126, 0.7152, 0.0722));
        if (now < 0.03 || room < 0.03 || now > 0.97 || room > 0.97) continue;   // says little
        float r = log(now / room);
        if (int(floor((r / RANGE * 0.5 + 0.5) * float(BINS))) == bin) n += 1.0;
    }
    fragColor = vec4(n, 0.0, 0.0, 1.0);
}
