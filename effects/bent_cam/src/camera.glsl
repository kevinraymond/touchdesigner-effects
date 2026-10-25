// Bent Cam (touchdesigner-effects, MIT). The camera films the screen. Its lens puts each sensor pixel on a point
// of the screen, set by Zoom and Rotate (how close the camera is and how it is tilted). Each sensor pixel sits
// under one color filter of the Bayer mosaic (red, green or blue, in an RGGB pattern), so it measures only that
// color of the screen's light. The screen has its own pixels, red, green and blue stripes with dark gaps between
// the rows, and the two grids beat against each other, which is moire. The lens blurs the screen (Focus) and with
// it the stripes. Last comes the sensor's noise, new every camera frame: shot noise, which grows with the light,
// and a little read noise. Light is linear in here.
// Inputs: 0 the screen (R'G'B', blurred by the lens). Out: r, the light on each sensor pixel through its filter.
uniform vec4 uCam;    // x Zoom, y Rotate (radians), z Moire 0-1, w Noise 0-1
uniform vec4 uCam2;   // x the lens blur (sigma, in texels of the screen picture), y the camera frame (seeds the noise)
out vec4 fragColor;
#define SCREEN 1.25           // the screen's pixels per sensor pixel (a 7-inch 800 x 480 panel before a 640 x 480 sensor)
#define FILL_X (1.0 / 3.0)    // each color's stripe is a third of a screen pixel wide
#define FILL_Y 0.8            // the dark gap between rows leaves 80% of each row lit
#define SENSOR_FILL 0.5       // a sensor pixel gathers light over half its width (the rest is wiring)
#define VIGNETTE 0.15         // a cheap lens darkens toward the corners: 1 - VIGNETTE x (distance from center in heights)^2

// The profile of a stripe fill of a period wide that starts at phase, at s (all in periods), with a mean of 1,
// softened by the lens (sigma) and by the width of the sensor pixel looking at it (foot), both in periods: its
// Fourier series to the 4th harmonic, each harmonic scaled down by the blur's Gaussian and the pixel's sinc.
float stripes(float s, float phase, float fill, float sigma, float foot) {
    float v = 1.0;
    for (int k = 1; k <= 4; k++) {
        float fk = float(k);
        float a = 2.0 * sin(PI * fk * fill) / (PI * fk * fill);
        float x = PI * fk * foot;
        float att = exp(-2.0 * PI * PI * sigma * sigma * fk * fk) * (x > 1e-4 ? sin(x) / x : 1.0);
        v += a * att * cos(2.0 * PI * fk * (s - phase - 0.5 * fill));
    }
    return max(v, 0.0);
}

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    vec2 S = uTDOutputInfo.res.zw;
    int ch = (p.x & 1) + (p.y & 1);                          // RGGB: 0 red, 1 green, 2 blue
    vec2 q = gl_FragCoord.xy - 0.5 * S;                      // from the center, in sensor pixels
    float c = cos(uCam.y), s = sin(uCam.y);
    vec2 uv = mat2(c, -s, s, c) * q / uCam.x / S + 0.5;     // where on the screen this pixel looks
    float light = 0.0;
    if (all(greaterThanEqual(uv, vec2(0.0))) && all(lessThanEqual(uv, vec2(1.0)))) {
        vec3 lin = pow(max(texture(sTD2DInputs[0], uv).rgb, 0.0), vec3(2.2));
        light = ch == 0 ? lin.r : ch == 1 ? lin.g : lin.b;
        vec2 sp = uv * S * SCREEN;                           // in the screen's pixels
        float foot = SENSOR_FILL * SCREEN / uCam.x, sigma = uCam2.x * SCREEN;
        float pat = stripes(sp.x, float(ch) / 3.0, FILL_X, sigma, foot) * stripes(sp.y, 0.0, FILL_Y, sigma, foot);
        light *= 1.0 + uCam.z * (pat - 1.0);
    }                                                        // past the screen's edge: its black bezel
    vec2 r = q / S.y;
    light *= 1.0 - VIGNETTE * dot(r, r);
    // Gaussian noise from two dice (Box-Muller), new each camera frame.
    uint f = uint(uCam2.y + 0.5);
    float u1 = max(die(uint(p.x), uint(p.y), f * 2u), 1e-7), u2 = die(uint(p.x), uint(p.y), f * 2u + 1u);
    float g = sqrt(-2.0 * log(u1)) * cos(2.0 * PI * u2);
    light += uCam.w * (0.05 * sqrt(max(light, 0.0)) + 0.008) * g;
    fragColor = vec4(max(light, 0.0), 0.0, 0.0, 1.0);
}
