// Point cloud prototype. A dot: round and solid (depth-tested), round and soft (added up, a glow),
// square (a disc lying in the surface), or a splat: a Gaussian whose color and weight are added up
// and divided out afterwards (splat_norm.glsl), so neighboring splats blend into one surface.
uniform vec4 uLook;   // x 0 solid round, 1 soft added, 2 square, 3 splat (color x weight, weight), 4 splat depth
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
    int look = int(uLook.x + 0.5);
    if (look != 2 && r2 > (look == 4 ? 0.5 : 1.0))
        discard;   // the splats' depth pass covers less than they do, so their soft rims blend
    vec4 c = vec4(iVert.color, 1.0);
    if (look == 1)
        c.rgb *= 0.5 * (1.0 - r2);
    else if (look == 3)
        c = vec4(iVert.color, 1.0) * exp(-3.0 * r2);
    oFragColor = TDOutputSwizzle(c);
}
