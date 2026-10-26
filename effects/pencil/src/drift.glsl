// touchdesigner-effects (MIT), Pencil: how far the pencil strokes have moved with the picture, so they travel with
// what moves instead of staying on the screen while the picture slides under them (Lu, Xu and Jia name that as their
// method's limit on video). Two offsets are carried along by the picture's motion each frame (semi-Lagrangian: each
// pixel takes the offset from where its content came from, plus this frame's motion), and each starts again from 0
// every uD.w seconds, half a period apart, so draw.glsl can always fade to the younger one before the older has
// stretched far: the advected textures of Max and Becker ("Flow Visualization Using Moving Textures", 1995) and
// Neyret ("Advected Textures", SCA 2003). Where nothing moves both stay at 0 and the strokes stay put.
// Inputs: 0 the motion (lib speed.glsl: rg cells per second at a quarter of the picture's size, b confidence), 1 this
// pass last frame (read by UV).
// Out: rg the first offset, ba the second (UV units: the strokes at a pixel are those that were drawn that far back).
uniform vec4 uD;   // x the frame step (s), y the first offset's age (0-1 of its period), z Follow Movement (0-1),
                   // w the period (s)
out vec4 fragColor;

void main() {
    vec2 uv = vUV.st;
    // The motion averaged over blocks of 4 x 4 cells (a mipmap level): only motion that holds together over an area
    // carries the strokes, so drifting smoke and the flow's noise don't stir them like marbled paper.
    vec4 m = textureLod(sTD2DInputs[0], uv, uD.z > 0.0 ? 2.0 : 0.0);
    vec2 v = m.rg / uTD2DInfos[0].res.zw * uD.x * uD.z * smoothstep(2e-4, 1e-3, m.b);
    vec4 d = texture(sTD2DInputs[1], uv - v) + vec4(v, v);
    // An offset starts again on the frame its age wraps past 0 (the second's is half a period on).
    float step = uD.x / uD.w;
    if (uD.y < step) d.rg = vec2(0.0);
    if (fract(uD.y + 0.5) < step) d.ba = vec2(0.0);
    fragColor = d;
}
