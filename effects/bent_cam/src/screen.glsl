// Bent Cam (touchdesigner-effects, MIT). The screen the camera films. It shows the picture with the camera's
// own last picture over it, as much as Feedback says, so the camera films itself filming itself.
// Inputs: 0 the picture, 1 the camera's last picture (feed_fb; transparent before the first one).
// Out: R'G'B' as the screen shows it, at the sensor's size.
uniform vec4 uScr;    // x Feedback 0-1
out vec4 fragColor;

void main() {
    vec3 pic = clamp(texture(sTD2DInputs[0], vUV.st).rgb, 0.0, 1.0);
    vec4 fed = texture(sTD2DInputs[1], vUV.st);
    fragColor = vec4(mix(pic, clamp(fed.rgb, 0.0, 1.0), uScr.x * fed.a), 1.0);
}
