// Datamosh-style (touchdesigner-effects, MIT): the decoder's clock, one pixel. Whether this frame
// brings a new input frame, and whether that frame is a cut: a change several times the running
// mean of the changes between frames (so a dancer's loop point in a still shot counts and a fast
// pan doesn't), never less than a floor, and not within a moment of the last cut (the frames
// right after a cut change a lot too). Experimental: a heuristic.
// Inputs: 0 the mean |luma change| since the last frame seen (1 x 1), 1 this pass's previous
// output (Feedback TOP). Out: r new frame (0/1), g cut (0/1), b the running mean, a when the
// last cut was (seconds).
uniform vec4 uS;    // x: change that makes a new frame, y: least change that is a cut,
                    // z: a cut is at least this many times the running mean, w: the mean's blend
uniform vec4 uC;    // x: seconds now (it also makes this pass cook every frame), y: seconds between cuts
out vec4 fragColor;
void main() {
    float d = texelFetch(sTD2DInputs[0], ivec2(0), 0).r;
    vec4 prev = texelFetch(sTD2DInputs[1], ivec2(0), 0);
    float mean = prev.b, last = prev.a;
    float fresh = step(uS.x, d);
    float cut = fresh * step(max(uS.y, uS.z * mean), d) * step(uC.y, abs(uC.x - last));
    if (fresh > 0.5 && cut < 0.5) mean = mix(mean, d, uS.w);
    if (cut > 0.5) last = uC.x;
    fragColor = vec4(fresh, cut, mean, last);
}
