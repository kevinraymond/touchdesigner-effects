// touchdesigner-effects (MIT), Scan Processor: the raster's colors, and the red guard on every pixel shown.
//   Picture    the picture's own colors.
//   Colorizer  Scanimate's output was black and white and went through a colorizer, as Sandin's Image Processor
//              colored its pictures: each band of gray became a color. Here six colors, dark blue through teal, gray,
//              orange and gold to near white, twice over from dark to light, each pixel keeping its brightness and
//              taking its band's hue (so nothing is told by hue alone), the bands sliding through the tones with the low bands' level and slowly over
//              time. A band's change is then a change of hue alone, which WCAG doesn't count as a flash unless red.
// The deflection sways the picture's reds back and forth, and one near WCAG's saturated-red line crosses it more often
// as it sways further (Motion Magnify's lesson), so every pixel goes through lib red_guard.glsl.
// Inputs: 0 the raster (scan.glsl).
// Out: the picture.
uniform vec4 uC;    // Colors (0 Picture, 1 Colorizer), the bands' slide (0-1), 0, 0
out vec4 fragColor;

#define REPEAT 2.0   // the palette's times over the tones, dark to light: a face spans a few bands at any moment

const vec3 PALETTE[6] = vec3[6](vec3(0.10, 0.20, 0.85), vec3(0.10, 0.65, 0.85), vec3(0.55, 0.55, 0.60),
                                vec3(0.95, 0.55, 0.10), vec3(0.95, 0.80, 0.30), vec3(0.95, 0.95, 0.90));

vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
vec3 toSRGB(vec3 c) { return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }

void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    if (uC.x > 0.5) {
        float y = dot(c, vec3(0.299, 0.587, 0.114));
        float k = mod(y * 6.0 * REPEAT * 0.999 + uC.y * 6.0, 6.0);
        int i = int(k);
        float f = clamp((k - float(i) - 0.85) / 0.15, 0.0, 1.0);    // a soft edge into the next band
        vec3 p = mix(PALETTE[i], PALETTE[(i + 1) % 6], f);
        c = p * y / max(dot(p, vec3(0.299, 0.587, 0.114)), 1e-3);
        // A dark hue lifted to a bright pixel's brightness runs past 1: blend it toward gray of the same brightness
        // rather than clip it, so the brightness stays the pixel's exactly. Clipped, the brightest band's wrap to
        // dark blue dropped a pixel's brightness by a quarter, and noise at that edge flickered (6.5 flashes a second
        // in one cell of the flowers with Flashing Off).
        float top = max(c.r, max(c.g, c.b));
        if (top > 1.0)
            c = mix(c, vec3(y), (top - 1.0) / max(top - y, 1e-3));
        c = clamp(c, 0.0, 1.0);
    }
    fragColor = vec4(toSRGB(redGuard(toLinear(c))), 1.0);
}
