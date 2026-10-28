// touchdesigner-effects (MIT), Voxel Space: the view eased over a tenth of a second, as a camera's shutter blurs what
// moves. Flown over, a bright and busy picture (a plaza seen from above, a field of flowers) slides its many small hills,
// each lit on one side and shaded on the other, past each other in the middle distance, and each that passes a part
// of the view is a swing between light and dark. A beat's dip moves the whole view on purpose, as often as the flash
// gate allows, and eased as much it smeared into a blur, so the view eases less while the camera dips.
// Inputs: 0 the view, 1 this pass's last frame. Out: the view, eased.
uniform vec4 uE;   // x seconds since the last frame, y the time it eases over (less during a dip)
out vec4 fragColor;

void main() {
    vec4 now = texture(sTD2DInputs[0], vUV.st);
    vec4 was = texture(sTD2DInputs[1], vUV.st);
    fragColor = TDOutputSwizzle(was.a < 0.5 ? vec4(now.rgb, 1.0) : vec4(mix(was.rgb, now.rgb, 1.0 - exp(-uE.x / uE.y)), 1.0));
}
