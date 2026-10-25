// VHS + CRT (touchdesigner-effects, MIT). The LCD's liquid crystal. A cell lets light through by how far its
// crystal has turned, and the crystal follows the drive voltage over milliseconds rather than at once. In a
// twisted-nematic cell, the panels of the 1990s and 2000s, the voltage forces the crystal to block the light but
// only its own elastic pull turns it back to let light through, which is slower; and a small step between two
// grays, driven by a small change of voltage, is slower still. So a moving picture leaves trails, longer where
// cells have to turn lighter (behind a dark thing moving over a light one). Each color's cell follows here as a
// first-order lag whose time constant its step sets: Response 0 a later panel (4 ms), 1 an early one (44 ms).
// Inputs: 0 the picture (for the output's size), 1 the signal (R'G'B', one row a line), 2 this pass's last
// frame (Feedback TOP). Out: how much light each color's cell lets through (linear), the same over the cell.
uniform vec4 uLcd;   // x Mask Size, y Response 0-1, z this frame's step (s)
out vec4 fragColor;
#define TAU 0.004    // a step to lighter at Response 0, in seconds
#define TAU_R 0.04   // added at Response 1
#define DARKER 0.35  // a step to darker takes this much of that time
#define SMALL 1.5    // a step of nearly nothing takes 1 + SMALL times as long as one from black to white

void main() {
    vec2 res = uTD2DInfos[0].res.zw;
    vec2 c = cellUV(gl_FragCoord.xy, pitch(uLcd.x, res), res);
    vec3 want = pow(clamp(texture(sTD2DInputs[1], c).rgb, 0.0, 1.0), vec3(GAMMA));
    vec3 s = texture(sTD2DInputs[2], vUV.st).rgb;
    float tau = TAU + TAU_R * uLcd.y;
    for (int k = 0; k < 3; k++) {
        float d = want[k] - s[k];
        float t = tau * (d > 0.0 ? 1.0 : DARKER) * (1.0 + SMALL * (1.0 - abs(d)));
        s[k] += d * (1.0 - exp(-uLcd.z / t));
    }
    fragColor = vec4(s, 1.0);
}
