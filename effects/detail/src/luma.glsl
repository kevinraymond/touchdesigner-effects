// touchdesigner-effects (MIT), Detail: the picture's brightness, the one channel the filter works on. Its luma: the
// sRGB-encoded channels weighted as Rec. 709 weights them, so a step in it looks about as large in a dark part of
// the picture as in a light one. Paris, Hasinoff and Kautz filter the brightness alone to keep the picture's colors
// (2011, Fig. 9); collapse.glsl adds the change in it to every channel.
// Inputs: 0 the picture. Out: r its luma, 0-1.
out vec4 fragColor;

void main() {
    vec3 c = clamp(texture(sTD2DInputs[0], vUV.st).rgb, 0.0, 1.0);
    fragColor = vec4(dot(c, vec3(0.2126, 0.7152, 0.0722)));
}
