// touchdesigner-effects (MIT), Slit-Scan's Slit map: strip photography, as photo-finish cameras take it. A slit
// across the picture at Position sees one line of it; film runs past the slit, so each moment of that line is laid
// down beside the slit and carried away, and the strip is that line over time: still things smear into streaks,
// moving ones are drawn by how they cross the slit. On the other side of the slit, the live picture.
// Each frame the film moves on by how far it ran (uSlit.w); the newest stretch is filled from the history at the
// moments between this frame and the last (past.glsl), so a slow clip's slit lays smooth ribbons, not steps. A beat's
// tears land on the film laid while they are open and ride away with it.
// The film spreads one line's flicker over the whole strip, so a red petal waving across the slit, a pixel's worth in
// the input, becomes an area of red flicker (red flowers at Speed 120: 2 red flashes a second with Flashing Off, the
// clip 1): the red guard (lib red_guard.glsl) keeps every red Slit shows short of WCAG's saturated-red line, the live
// side's too (guarding only the film as it was laid still measured 2: resampling it as it moves can mix one pixel's
// red with another's green and blue).
// Inputs as past.glsl, and sTD2DInputs[2] this pass's previous output (Feedback TOP).
uniform vec4 uSlit;    // x, y: the way the film runs (a unit vector), z: the slit's position across the picture along
                       // it (0-1), w: how far the film ran this frame (picture heights)
uniform vec4 uSlit2;   // x: the film's speed (picture heights a second), y: Between Frames (0 Flow, 1 Blend, 2 Steps)
out vec4 fragColor;

vec4 guard(vec4 c) { return vec4(pow(redGuard(pow(max(c.rgb, 0.0), vec3(2.2))), vec3(1.0 / 2.2)), c.a); }

void main() {
    vec2 uv = vUV.st;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    vec2 q = vec2((uv.x - 0.5) * aspect, uv.y - 0.5);
    vec2 dir = uSlit.xy;
    float extent = 0.5 * (abs(dir.x) * aspect + abs(dir.y));
    float along = dot(q, dir) - (2.0 * uSlit.z - 1.0) * extent;   // picture heights past the slit
    if (along < 0.0) {
        fragColor = guard(texture(sTD2DInputs[0], uv));
        return;
    }
    if (along < uSlit.w) {
        vec2 at = q - along * dir;                                  // where on the slit this film was exposed
        vec2 on = vec2(at.x / aspect + 0.5, at.y + 0.5);
        float across = abs(dir.x) > abs(dir.y) ? 1.0 - on.y : on.x;   // where along the slit, so tears cut the film
        fragColor = guard(past(on, along / max(uSlit2.x, 1e-4) + tear(across), int(uSlit2.y + 0.5)));
        return;
    }
    vec2 was = q - uSlit.w * dir;
    fragColor = guard(sampleCR(2, vec2(was.x / aspect + 0.5, was.y + 0.5)));
}
