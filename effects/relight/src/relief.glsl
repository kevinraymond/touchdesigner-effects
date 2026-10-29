// touchdesigner-effects (MIT), Relight: the depth map's nearness as the surface's shape, half finely smoothed (its
// detail, without the steps of an 8-bit map) and half averaged broadly with a triangle filter (Roundness), so a figure
// cut out of a flat depth map rounds off at its edges like a relief instead of standing as a slab. Only inward: a blur
// also spreads a figure's nearness out over what lies behind it, a slope of a few pixels from the figure down to a
// backdrop meters away, which shadowed itself and outlined every figure in black. So neither smoothing is more than
// EDGE nearer than the depth itself, and the backdrop stays down right up to the figure's edge, while the steps of an
// 8-bit map (a few 255ths each) stay smoothed: held to the depth exactly, they stood up as terraces on every wall.
// Inputs: 0 the nearness finely smoothed, 1 averaged broadly with a triangle filter, 2 as it is (depth_near.glsl's r).
// Out: r the shape's nearness, 0-1.
out vec4 fragColor;
#define EDGE 0.03

void main() {
    float d = texture(sTD2DInputs[2], vUV.st).r + EDGE;
    float fine = min(texture(sTD2DInputs[0], vUV.st).r, d), broad = min(texture(sTD2DInputs[1], vUV.st).r, d);
    fragColor = vec4(0.5 * (fine + min(fine, broad)), 0.0, 0.0, 1.0);
}
