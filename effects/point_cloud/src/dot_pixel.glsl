// Point Cloud (touchdesigner-effects, MIT). A dot. Points: round and solid, the nearest in front.
// Glow: round and soft, added up, so where many overlap it glows. Surface: a Gaussian splat whose
// color and weight are added up and divided out afterwards (splat_norm.glsl), so neighboring
// splats blend into one surface; its depth pass covers less than the splat, so the soft rims blend.
uniform vec4 uLook;   // z pass (0 Points, 1 Glow, 2 Surface, 3 Surface's depth pass)
in Vertex {
    vec3 color;
    vec2 uv;
    flat float keep;
} iVert;
out vec4 oFragColor;

void main() {
    TDCheckDiscard();
    if (iVert.keep <= 0.0)
        discard;
    float r2 = dot(iVert.uv, iVert.uv);
    int pass = int(uLook.z + 0.5);
    if (r2 > (pass == 3 ? 0.5 : 1.0))
        discard;
    vec4 c = vec4(iVert.color, 1.0);
    if (pass == 1)
        c.rgb *= 0.5 * (1.0 - r2);
    else if (pass == 2)
        c *= exp(-3.0 * r2);
    oFragColor = TDOutputSwizzle(c);
}
