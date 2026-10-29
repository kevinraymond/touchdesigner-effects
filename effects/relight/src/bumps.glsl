// touchdesigner-effects (MIT), Relight: with nothing on input 3, the surface is a plane with the picture's brighter
// parts bulging out of it, Bumps high: its brightness blurred, less its broad triangle average, so a cheek, a brow or a
// lit arm rounds out while a sky or a wall, bright all over, stays flat. Only up: what is darker than its surroundings
// stays on the plane, where sinking it dug a moat round everything bright. The picture's brightness as a whole stood in
// badly, making a landscape's sky the nearest thing in it, and its finest detail made skin look pitted.
// Inputs: 0 the brightness blurred, 1 averaged broadly with a triangle filter (luma.glsl's g).
// Out: r the stand-in's nearness, about 0.5.
uniform vec4 uB;   // x Bumps
out vec4 fragColor;

void main() {
    float d = texture(sTD2DInputs[0], vUV.st).g - texture(sTD2DInputs[1], vUV.st).g;
    fragColor = vec4(0.5 + uB.x * max(d, 0.0), 0.0, 0.0, 1.0);
}
