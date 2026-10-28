// touchdesigner-effects (MIT), Voxel Space: the land's colors, the picture eased over time as the heights are, so the
// land and its hills move together. Seen in perspective the near ground is the picture enlarged, and a dancer's
// every turn, which changes little of the picture, swept large areas of the view between light and dark: even the
// picture lying flat, the camera still, flashed a second more than the clip. Eased over a quarter of a second, a
// turn is a slow sweep of her colors over the ground.
// Inputs: 0 the picture, 1 this pass's last frame. Out: the colors, eased.
uniform vec4 uE;   // x seconds since the last frame, y the time it eases over
out vec4 fragColor;

void main() {
    vec4 now = texture(sTD2DInputs[0], vUV.st);
    vec4 was = texture(sTD2DInputs[1], vUV.st);
    fragColor = TDOutputSwizzle(was.a < 0.5 ? vec4(now.rgb, 1.0) : vec4(mix(was.rgb, now.rgb, 1.0 - exp(-uE.x / uE.y)), 1.0));
}
