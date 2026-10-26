// touchdesigner-effects (MIT), Pencil: the gradient the lines are drawn from, as Lu, Xu and Jia compute it ("Combining
// Sketch and Tone for Pencil Drawing Production", NPAR 2012, eq. 1): the magnitude of the grayscale picture's forward
// differences, G = ((dx I)^2 + (dy I)^2)^(1/2). The picture is read between pixels first (bilinear at a pixel's
// corner averages a 2 x 2 block), which takes the edge off a video's noise without softening its edges much.
// G is then eased over uE.y seconds: the lines multiply small changes in the gradient many times over (a faint edge
// in drifting smoke comes out a dark line), so a video's noise and flicker, followed at once, swung the lines in
// the smoke between dark and light, a flash (dev/flash.py); eased, a lasting edge still comes through within a
// fraction of a second.
// Inputs: 0 the picture, 1 this pass last frame (read by UV; g 1 once set, so the first frame takes G at once).
// Out: r G (the picture's values 0-1 per pixel), g 1.
uniform vec4 uE;   // x the frame step (s), y how long the easing takes (s)
out vec4 fragColor;

float at(vec2 uv) {
    return dot(texture(sTD2DInputs[0], uv).rgb, vec3(0.2126, 0.7152, 0.0722));
}

void main() {
    vec2 px = uTD2DInfos[0].res.xy;
    vec2 uv = vUV.st + 0.5 * px;
    float c = at(uv);
    float dx = at(uv + vec2(px.x, 0.0)) - c, dy = at(uv + vec2(0.0, px.y)) - c;
    float g = sqrt(dx * dx + dy * dy);
    vec4 last = texture(sTD2DInputs[1], vUV.st);
    fragColor = vec4(last.g > 0.5 ? mix(last.r, g, 1.0 - exp(-uE.x / uE.y)) : g, 1.0, 0.0, 1.0);
}
