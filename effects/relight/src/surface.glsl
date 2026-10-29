// touchdesigner-effects (MIT), Relight: the surface the lights fall on, at half the picture's size. Its height is the
// shape's nearness times Relief (as a share of the picture's height), in this pass's pixels; its normal comes from the
// height's slope, at most MAX_SLOPE steep. Ambient occlusion after Luft, Colditz and Deussen's unsharp masking of the
// depth buffer (2006), sampled: a pixel lying below what surrounds it, at 3 radii in 8 directions, is darker. A
// neighbor far higher is something standing in front, not a wall around the pixel (a dancer meters before the back
// wall), so its rise counts only up to the radius and fades out by twice it (the range check screen-space occlusion
// makes); without it, every figure wore a black halo.
// Inputs: 0 the picture (its size only), 1 the shape (relief.glsl or bumps.glsl, r nearness).
// Out: r the height (pixels), g and b the normal's x and y (z is the rest of a unit vector), a the occlusion (1 open).
uniform vec4 uS;   // x Relief, y Occlusion
out vec4 fragColor;
#define TAU 6.28318531

float heightAt(vec2 p, vec2 res) { return uS.x * res.y * texture(sTD2DInputs[1], p / res).r; }

void main() {
    vec2 res = uTDOutputInfo.res.zw, p = gl_FragCoord.xy;
    float h = heightAt(p, res);
    // Each slope is taken toward whichever neighbor is nearer in height, so a pixel at a depth edge keeps the normal of
    // its own side: the backdrop's pixels beside a figure, taking the cliff's sideways normal, lost the backdrop's
    // sheen and ringed the figure in black. And the normal sees at most MAX_SLOPE of a slope (the shadows see the whole
    // height).
    float l = heightAt(p - vec2(1.0, 0.0), res) - h, r = heightAt(p + vec2(1.0, 0.0), res) - h;
    float d = heightAt(p - vec2(0.0, 1.0), res) - h, u = heightAt(p + vec2(0.0, 1.0), res) - h;
    vec2 g = vec2(abs(r) < abs(l) ? r : -l, abs(u) < abs(d) ? u : -d);
    g *= min(1.0, MAX_SLOPE / max(length(g), 1e-6));
    vec3 n = normalize(vec3(-g, 1.0));
    float scale = res.y / 360.0, occ = 0.0;
    for (int ring = 0; ring < 3; ring++) {
        float r = scale * (ring == 0 ? 3.0 : ring == 1 ? 8.0 : 16.0);
        for (int k = 0; k < 8; k++) {
            float a = TAU * (float(k) + (ring == 1 ? 0.5 : 0.0)) / 8.0;
            float rise = (heightAt(p + r * vec2(cos(a), sin(a)), res) - h) / r;
            occ += clamp(rise, 0.0, 1.0) * clamp(2.0 - rise, 0.0, 1.0);
        }
    }
    fragColor = vec4(h, n.x, n.y, clamp(1.0 - uS.y * occ / 12.0, 0.0, 1.0));
}
