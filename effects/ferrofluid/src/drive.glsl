// Ferrofluid (touchdesigner-effects, MIT): the field the liquid feels, at the height field's grid. A magnetic fluid
// under a field normal to its surface stays flat until the field passes a threshold, then rises in a lattice of spikes
// (R. E. Rosensweig's normal field instability: M. D. Cowley and R. E. Rosensweig, "The interfacial stability of a
// ferromagnetic fluid", J. Fluid Mech. 30, 1967). Here the field is strongest where the picture is bright (By
// Brightness) or what stands out in front in the depth map is (By Nearness), and where the magnet under the dish is;
// the music's bass sets how strong it is. It becomes r, the growth rate in field.glsl's equation: below 0 the surface
// lies flat, from about 0.05 to 0.3 it rises in hexagons, from about 0.5 in ridges (dev/out/ferrofluid/regimes.png).
// Inputs: 0 the picture (mipmapped; Output Resolution by Spike Size, so the grid follows the picture's shape), 1 what
// stands out or is inside the mask (lib depth_find.glsl: r 1 inside, read by UV).
// Out: r the growth rate r, g how strongly driven 0-1.
uniform vec4 uD;   // x By Brightness, y By Nearness (0 with nothing on input 3), z Magnet, w the picture's mip level
                   // whose texels are SOFT cells wide (a field doesn't stop at an edge)
uniform vec4 uM;   // xy the magnet's place (UV), z its radius (frame heights)
uniform vec4 uR;   // x r where nothing drives it, y r where fully driven, z how strong the field is now (Strength,
                   // the bass), w a beat's lift of r where driven
out vec4 fragColor;

#define BRIGHT vec2(0.25, 0.75)   // brightness from which the picture drives the field, and fully

float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

void main() {
    vec2 uv = vUV.st;
    vec2 o = uTD2DInfos[1].res.xy;
    float inside = 0.0;
    for (int k = -1; k <= 1; k++)
        for (int j = -1; j <= 1; j++)
            inside += (2.0 - abs(float(k))) * (2.0 - abs(float(j))) * texture(sTD2DInputs[1], uv + o * vec2(k, j)).r;
    inside /= 16.0;
    float bright = smoothstep(BRIGHT.x, BRIGHT.y, luma(textureLod(sTD2DInputs[0], uv, uD.w).rgb));
    vec2 d = (uv - uM.xy) * vec2(uTD2DInfos[0].res.z / uTD2DInfos[0].res.w, 1.0);
    float magnet = uD.z * exp(-dot(d, d) / (uM.z * uM.z));
    float drive = clamp(max(uD.x * bright, uD.y * inside) + magnet, 0.0, 1.0);
    float r = uR.x + (uR.y - uR.x) * drive * uR.z + uR.w * drive;
    fragColor = vec4(r, drive, 0.0, 1.0);
}
