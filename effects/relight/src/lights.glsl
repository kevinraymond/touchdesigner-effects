// touchdesigner-effects (MIT), Relight: where each light is this frame and what color, from the look's table (the
// builder writes LOOK_COLOR, LOOK_PATH and LOOK_TIME in front of this, four lights a look). A lamp sways about its
// place on a slow Lissajous path: x and y each a sine of the lights' clock with its own period. A sun swings its
// heading the same way at its elevation. Height scales every lamp's height above the top of the relief (Relief), so a
// low lamp grazes the shapes rather than hiding below them, and every sun's elevation.
// Out (4 x 2): row 0 a lamp's place (x, y as a share of the picture, z its height as a share of its height, w 1) or a
// sun's direction (w 0); row 1 its color times its intensity, times Brightness, the loudness and the beat's flare.
uniform vec4 uT;   // x the lights' clock (s), y the look, z the beat's flare (0 none), w Brightness times the loudness
uniform vec4 uH;   // x Height, y Relief
out vec4 fragColor;
#define TAU 6.28318531

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    int k = int(uT.y + 0.5) * 4 + c.x;
    vec4 col = LOOK_COLOR[k], path = LOOK_PATH[k], time = LOOK_TIME[k];
    if (c.y == 1) {
        fragColor = vec4(col.rgb * col.a * uT.w * (1.0 + uT.z), 1.0);
        return;
    }
    float t = uT.x;
    if (time.w < 0.0) {   // a sun: path.y its heading (radians), swinging path.x either side; -time.w its elevation
        float heading = path.y + path.x * sin(TAU * t / time.x + time.z);
        float el = radians(clamp(-time.w * uH.x, 5.0, 85.0));
        fragColor = vec4(cos(el) * cos(heading), cos(el) * sin(heading), sin(el), 0.0);
    } else {
        fragColor = vec4(path.x + path.z * sin(TAU * t / time.x + time.z),
                         path.y + path.w * sin(TAU * t / time.y + 1.3 * time.z), uH.y + time.w * uH.x, 1.0);
    }
}
