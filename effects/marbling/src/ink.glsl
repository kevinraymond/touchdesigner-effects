// Marbling (touchdesigner-effects, MIT): each drop's ink, taken from the picture where the drop falls, the moment it
// falls, and kept for as long as the drop lasts: a drop of the picture's own color. The inks sit in a ring, a drop's
// at its number mod the ring's width; a slot holds its drop's number in alpha, so a new drop is seen by its number.
// Inputs: 0 the picture (mipmapped: a drop takes the color of the few pixels where it falls; averaged over the drop's
// own size, the dancer's inks all came out gray), 1 the ring last frame (Feedback TOP; alpha 0 on the first frame).
// Uniform arrays (tray.py's channels, a tool an element): uTa (kind, t0, rise, hold), uTb (relax, a, b, c), uTc (d, e,
// serial); a drop's a and b are its center, 0-1 across and up the picture.
// Out: one texel a slot, rgb the ink, a the drop's number.
uniform vec4 uTa[64];
uniform vec4 uTb[64];
uniform vec3 uTc[64];
out vec4 fragColor;

#define N 64
#define LOD 1.5    // the picture's mip level a drop's color is taken from

void main() {
    int j = int(gl_FragCoord.x);
    vec4 kept = texture(sTD2DInputs[1], vec2((float(j) + 0.5) / float(N), 0.5));
    for (int i = 0; i < N; i++) {
        if (uTa[i].x == 0.0)
            break;
        float serial = uTc[i].z;
        if (uTa[i].x != 1.0 || int(serial) % N != j)
            continue;
        if (abs(kept.a - serial) > 0.5)
            kept = vec4(textureLod(sTD2DInputs[0], uTb[i].yz, LOD).rgb, serial);
        break;
    }
    fragColor = kept;
}
