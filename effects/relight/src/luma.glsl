// touchdesigner-effects (MIT), Relight: the picture's brightness, r in linear light (relative luminance), g its square
// root (close to how bright it looks).
out vec4 fragColor;

void main() {
    vec3 c = texture(sTD2DInputs[0], vUV.st).rgb;
    c = mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c));
    float y = dot(c, vec3(0.2126, 0.7152, 0.0722));
    fragColor = vec4(y, sqrt(y), 0.0, 1.0);
}
