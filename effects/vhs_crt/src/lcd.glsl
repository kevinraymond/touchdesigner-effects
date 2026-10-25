// VHS + CRT (touchdesigner-effects, MIT). The LCD's face. Each pixel is three cells side by side behind red,
// green and blue filters, inside the black matrix that hides the wiring between them; a backlight shines through
// them all, and a little of it leaks through black, more toward the edges. How much light a twisted-nematic cell
// lets through also depends on the angle it is seen from, up and down: from above, the picture washes out (black
// grays, the middle tones lighten); from below, it darkens and the light tones invert, darker than the middle
// ones, blue first (so it turns yellow-brown). Even seen straight on, the top of the panel is seen a little from
// below and the bottom a little from above, so the top is darker. Viewing Angle moves the eye, -1 well below the
// panel, 1 well above. Last, the red guard (red_guard.glsl) on every pixel.
// Inputs: 0 the picture (for the output's size), 1 the crystal (lcd_state: linear, the same over each cell).
// Out: R'G'B' and 1.
uniform vec4 uLcd;   // x Mask Size, w Viewing Angle -1..1
out vec4 fragColor;
#define COLOR 0.3    // how much of the colors' stripes shows; the rest is even light
#define GAP 0.7      // and of the dark lines between rows
#define LIT_X 0.8    // each cell lit over this much of its width (the black matrix between them)
#define LIT_Y 0.7    // and of its height
#define TILT 0.35    // the angle seen from changes this much from the panel's top to its bottom
#define LEAK 0.004   // the backlight through black, of white, in the middle; 4 times as much at the edges

// A cell letting through t (linear) seen at angle a, -1 (below) to 1 (above).
float seen(float t, float a) {
    if (a >= 0.0)
        return mix(pow(t, 1.0 / (1.0 + 1.5 * a)), 1.0, 0.06 * a) * (1.0 - 0.2 * a);
    float b = -a;
    return pow(t, 1.0 + 2.5 * b) * (1.0 - 0.9 * smoothstep(0.3, 1.0, b) * t * t);
}

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    float P = pitch(uLcd.x, res);
    vec3 t = clamp(texture(sTD2DInputs[1], vUV.st).rgb, 0.0, 1.0);
    float a = clamp(uLcd.w - TILT * (vUV.t - 0.5), -1.0, 1.0);
    vec3 strays = a > 0.0 ? vec3(0.95, 1.0, 1.1) : vec3(0.9, 1.0, 1.25);   // blue strays most
    vec3 lin = vec3(seen(t.r, clamp(a * strays.r, -1.0, 1.0)), seen(t.g, clamp(a * strays.g, -1.0, 1.0)),
                    seen(t.b, clamp(a * strays.b, -1.0, 1.0)));
    vec2 e = abs(vUV.st * 2.0 - 1.0);
    float leak = LEAK * (1.0 + 3.0 * pow(max(e.x, e.y), 6.0));
    lin = (leak + (1.0 - leak) * lin) * cells(gl_FragCoord.xy, P, LIT_X, LIT_Y, COLOR, GAP);
    fragColor = vec4(pow(redGuard(clamp(lin, 0.0, 1.0)), vec3(1.0 / GAMMA)), 1.0);
}
