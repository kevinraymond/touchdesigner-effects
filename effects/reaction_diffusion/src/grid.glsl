// Reaction-Diffusion (touchdesigner-effects, MIT): the picture at the grid's size (Size: the picture's own, a half
// or a quarter), each cell the mean of the pixels it covers, from the mipmap level that averages them (the GLSL
// TOP's Input Smoothness is Mipmap).
// Inputs: 0 the picture. Out: the picture, smaller.
out vec4 fragColor;

void main() {
    float lod = log2(max(uTD2DInfos[0].res.w / uTDOutputInfo.res.w, 1.0));
    fragColor = vec4(textureLod(sTD2DInputs[0], vUV.st, lod).rgb, 1.0);
}
