// touchdesigner-effects (MIT), Lens Flare: the flare eased over time. A light's place and brightness wobble a little
// from frame to frame (noise, a car's lamp in and out of a reflection), and its ghosts, big and far from it, turn that
// into edges sweeping back and forth across large areas, which counts as flashing. Eased over EASE seconds, a wobble
// becomes a soft edge; a ghost that moves trails a little.
// Inputs: 0 this frame's flare (render), 1 last frame's eased flare (flare_fb). Out: the eased flare.
uniform vec4 uEase;   // x how far to ease this frame (0-1)

out vec4 fragColor;
void main() {
    vec4 now = texture(sTD2DInputs[0], vUV.st);
    if (textureSize(sTD2DInputs[1], 0) == textureSize(sTD2DInputs[0], 0)) {
        now = mix(texture(sTD2DInputs[1], vUV.st), now, uEase.x);
    }
    fragColor = TDOutputSwizzle(now);
}
