// Film Stock (touchdesigner-effects, MIT). The camera's frame rate: film runs at 24 frames a second (Super 8 at 18,
// silent 16 mm at 16), so each frame holds for a 24th of a second and the picture steps, where video glides. This
// pass keeps the last frame taken and takes a new one when the film's frame number changes (uF.x, counted in Python so
// a cook missed or repeated never loses or doubles one); the number it holds is in its alpha (mod 2048, exact in 16-bit
// float). With Frame Rate at Source the pass is skipped.
// Inputs: 0 the picture, 1 this pass's last frame (Feedback TOP). Out: the frame held, its number in alpha.
out vec4 fragColor;
void main() {
    vec4 held = texture(sTD2DInputs[1], vUV.st);
    float id = mod(uF.x, 2048.0);
    if (abs(held.a - id) > 0.5) held = vec4(texture(sTD2DInputs[0], vUV.st).rgb, id);
    fragColor = held;
}
