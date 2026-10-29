// Film Stock (touchdesigner-effects, MIT). Day for night, after Thompson, Shirley and Ferwerda ("A Spatial
// Post-Processing Algorithm for Images of Night Scenes", JGT 2002): a night scene seen by rods is a scotopic
// brightness, bluish and dim, not the scene's colors. The scotopic luminance V comes from XYZ by Larson, Rushmeier and
// Piatko's formula (1997), V = Y (1.33 (1 + (Y + Z) / X) - 1.68), which favors blues as the rods do; the night color is
// k V times a bluish gray (the paper: a blue a little below the white point; day-for-night films shoot through a
// stronger blue, and this is between). What is bright enough to be seen by the cones (a lamp, a lit window) keeps its
// own color: the scotopic share s falls from 1 to 0 as V rises past the level a lamp has. Written here at full size;
// night_fine and night_wide blur it and night.glsl puts the detail back.
// Inputs: 0 the exposure (linear). Out: the night color (linear) and s in alpha.
out vec4 fragColor;
#define K_NIGHT 0.18      // the night image's brightness: V of white comes out at about this (two and a half stops under)
#define BLUE vec3(0.62, 0.78, 1.0)

void main() {
    vec3 c = max(texture(sTD2DInputs[0], vUV.st).rgb, 0.0);
    // sRGB's primaries to XYZ (D65).
    float X = dot(c, vec3(0.4124, 0.3576, 0.1805)), Y = dot(c, vec3(0.2126, 0.7152, 0.0722)),
          Z = dot(c, vec3(0.0193, 0.1192, 0.9505));
    float V = Y * (1.33 * (1.0 + (Y + Z) / max(X, 1e-4)) - 1.68);
    V = max(V, 0.0);
    float s = 1.0 - smoothstep(1.2, 3.0, V);                 // a white wall (V about 1) stays scotopic; a lamp doesn't
    fragColor = vec4(K_NIGHT * V * BLUE, s);
}
