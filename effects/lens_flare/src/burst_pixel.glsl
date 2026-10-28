// touchdesigner-effects (MIT), Lens Flare: the starburst texture (burst.glsl) on its square, in the light's color.
uniform sampler2D sBurst;

in vec2 vUV;
flat in vec3 vLevel;

out vec4 oFragColor;
void main() {
    TDCheckDiscard();
    oFragColor = TDOutputSwizzle(vec4(texture(sBurst, vUV).rgb * vLevel, 0.0));
}
