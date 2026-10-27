// touchdesigner-effects (MIT), Detail: four of the eight remapped copies of the picture's brightness that the fast
// local Laplacian filter interpolates between (M. Aubry, S. Paris, S. W. Hasinoff, J. Kautz and F. Durand, "Fast
// Local Laplacian Filters: Theory and Applications", ACM TOG 33(5), 2014, after S. Paris, S. W. Hasinoff and J. Kautz,
// "Local Laplacian Filters: Edge-aware Image Processing with a Laplacian Pyramid", SIGGRAPH 2011).
// A local Laplacian filter builds each coefficient of the output's Laplacian pyramid from the picture remapped around
// the brightness g there (its Gaussian pyramid's value): differences from g smaller than about Edge Contrast are
// detail, made Detail times stronger, and larger ones are edges, kept, or made Tone times as large. The fast filter
// remaps the whole picture around a few values of g spread over 0 to 1 instead, one copy each, and takes a
// coefficient between the two copies whose g brackets the picture's there. The remapping here is the smooth form the
// fast paper uses, the difference from g weighted by a Gaussian of it, which eight copies sample closely (within
// 37 dB of 64 copies at Edge Contrast 0.1, 44 dB at 0.3, dev/protos/detail/offline.py). Paris et al. keep the
// smallest differences from being boosted with a smooth step at 1 to 2%; here that is Noise Floor, in collapse.glsl,
// since a step that narrow falls between eight copies (it acted around each copy's value of g rather than the
// picture's, and boosted differences on its slope up to 7 times where it should have left them alone).
// Inputs: 0 the picture's brightness (luma.glsl). Out: rgba the brightness remapped around uG's four values of g.
uniform vec4 uR;   // x Detail with the music (-1 to 4: 1 + it is the slope through g), y Tone (the slope far from
                   // g), z Edge Contrast (the Gaussian's width)
uniform vec4 uG;   // the four values of g this pass remaps around
out vec4 fragColor;

vec4 remap(float i, vec4 g) {
    vec4 d = i - g;
    vec4 near = exp(-d * d / (2.0 * uR.z * uR.z));
    return g + d * (uR.y + (1.0 - uR.y) * near + uR.x * near);
}

void main() {
    fragColor = remap(texture(sTD2DInputs[0], vUV.st).r, uG);
}
