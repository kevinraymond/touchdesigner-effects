// touchdesigner-effects (MIT), Relight: each light's shadow, one channel a light. From every pixel the height field is
// marched toward the light, STEPS samples spread more thinly further out, along a ray rising from the surface to the
// lamp (or at the sun's elevation). Each sample where the field rises above the ray takes away light by how far it
// rises over how far away it is (Softness widens that, as a cone's penumbra), so nearer occluders cast sharper shadows;
// the samples' light let through is multiplied, and the march stops once nothing gets through. It never looks for the
// highest point seen from the pixel to shade by (see the patent notes on the docs page). A lamp's march stops at the
// lamp or REACH of the picture's width, whichever is nearer. Its samples start a fraction of a step further on at each
// pixel (Jimenez's interleaved gradient noise, fixed in place so nothing flickers), which turns the steps that a far
// shadow's edge showed as a comb into a fine grain that shadows_soft smooths away. At half the surface's size (a
// quarter of the picture's), which the penumbra hides, it costs a quarter as much; heights are in this pass's pixels.
// Inputs: 0 the surface (surface.glsl, r height, in its own pixels), 1 the lights.
// Out: rgba the four lights' light let through, 1 lit, 0 in shadow (Shadows of the way there).
uniform vec4 uH;   // x Shadows, y Softness, z REACH, w STEPS
out vec4 fragColor;

void main() {
    vec2 res = uTDOutputInfo.res.zw, p = gl_FragCoord.xy;
    float scale = res.y / float(textureSize(sTD2DInputs[0], 0).y);   // the surface's pixels to this pass's
    float h = texture(sTD2DInputs[0], p / res).r * scale;
    vec4 lit = vec4(1.0);
    int steps = int(uH.w);
    for (int i = 0; i < 4; i++) {
        if (max(max(lightColor(i).r, lightColor(i).g), lightColor(i).b) <= 0.0) continue;
        vec4 l = lightPlace(i);
        vec2 e;
        float slope, reach;
        if (l.w > 0.5) {
            vec2 d = l.xy * res - p;
            float dxy = max(length(d), 1e-3);
            e = d / dxy;
            slope = (l.z * res.y - h) / dxy;
            reach = min(dxy, uH.z * res.x);
        } else {
            float dxy = max(length(l.xy), 1e-4);
            e = l.xy / dxy;
            slope = l.z / dxy;
            reach = uH.z * res.x;
        }
        float through = 1.0, j = fract(52.9829189 * fract(dot(floor(p), vec2(0.06711056, 0.00583715))));
        for (int k = 1; k <= steps; k++) {
            float t = reach * pow((float(k) - j) / float(steps), 1.5);
            float above = texture(sTD2DInputs[0], (p + e * t) / res).r * scale - (h + slope * t) - 0.25;
            through *= clamp(1.0 - above / max(t * uH.y, 0.25), 0.0, 1.0);
            if (through < 0.004) break;
        }
        lit[i] = mix(1.0, through, uH.x);
    }
    fragColor = lit;
}
