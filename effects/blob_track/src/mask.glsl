// Blob Track (touchdesigner-effects, MIT). What the detectors look for, 0 to 1 (Track):
// movement (the picture against a background that follows it slowly; either polarity, so dark
// walkers on light stone and a pale dancer on black both count), or what stands out from its
// surroundings (brighter or darker; bright only; dark only), which also works on stills.
// Inputs: 0 state.glsl (r the current frame, g the background); 1 the small gray picture, blurred
// (the local mean).
uniform vec4 uMask;   // x Track (0 movement, 1 stand out, 2 bright, 3 dark), y contrast gain, z movement gain
out vec4 fragColor;

void main() {
    vec4 s = texture(sTD2DInputs[0], vUV.st);
    float mean = texture(sTD2DInputs[1], vUV.st).r;
    float lift = s.r - mean;
    float c = uMask.x < 1.5 ? abs(lift) : uMask.x < 2.5 ? lift : -lift;
    float m = uMask.x < 0.5 ? (abs(s.r - s.g) - 0.08) * uMask.z : (c - 0.03) * uMask.y;
    m = clamp(m, 0.0, 1.0);
    fragColor = TDOutputSwizzle(vec4(m, m, m, 1.0));
}
