// touchdesigner-effects (MIT), Lens Flare: a ghost's light at this pixel (ghost_vertex.glsl), each color channel its
// own iris shape cut by the front element's circle, both edges softened by the light's blur. The three colors share
// the angle (green's): they differ by a pixel or two, and atan is the costly part.
uniform vec4 uIris;   // x blades, y angle (radians), z roundness

in vec2 vP;
flat in vec3 vQx;
flat in vec3 vQy;
flat in vec3 vRho;
flat in vec3 vBlur;
flat in vec3 vLevel;
flat in vec3 vClipX;
flat in vec3 vClipY;
flat in vec3 vClipR;

out vec4 oFragColor;
void main() {
    TDCheckDiscard();
    vec3 sum = vec3(0.0);
    vec2 g = (vP - vec2(vQx.g, vQy.g)) / vRho.g;
    float cos_t = iris_cos(atan(g.y, g.x), uIris.x, uIris.y);
    for (int ch = 0; ch < 3; ch++) {
        vec2 a = (vP - vec2(vQx[ch], vQy[ch])) / vRho[ch];   // in the iris's units
        float scale = abs(vRho[ch]) / (2.0 * vBlur[ch]);
        float open = clamp(0.5 - iris_at(length(a), cos_t, uIris.x, uIris.z) * scale, 0.0, 1.0);
        float front = clamp(0.5 - (length(a - vec2(vClipX[ch], vClipY[ch])) - vClipR[ch]) * scale, 0.0, 1.0);
        sum[ch] = vLevel[ch] * open * front;
    }
    oFragColor = TDOutputSwizzle(vec4(sum, 0.0));
}
