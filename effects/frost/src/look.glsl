// Frost (touchdesigner-effects, MIT): Fern's and Stars' ice drawn over the picture as frost looks on a window. Its
// body is translucent: it blurs the picture behind it, bent a little by the ice's slope, and whitens it with the
// light it scatters, the picture's light spread wide plus a little of the room's, so frost glows where a lamp is
// behind it and stays faint gray-white where the room is dark. Broad ice and ice frozen longer (thicker) whiten more,
// a fern's arms (frozen before the ice between them) stay whiter, a relief lit from the upper left shows the veins
// where it has frozen over, a fine grain of small crystals mottles it, its edges and the middles of its arms catch
// the light, and a few of its crystals sparkle. On a beat its edges and sparkles glint. Every cell of the ice is all
// ice or all air (its interface is thinner than a cell), so its outline is read from a blend of its first two mip
// levels, about a cell and a half of blur, and comes out smooth at the picture's size rather than stepped along the
// cells. Stars' cells lie on a hexagonal lattice (seed.glsl): each pixel reads the three cell middles nearest it and
// blends them by where it lies between them, so needles one cell wide come out as smooth lines.
// Inputs: 0 the picture (mipmapped: its blur and its light spread wide come from its smaller levels), 1 the ice at
// the grid's size (Fern: r p; Stars: r s, ice at 1 or more; b seconds frozen; mipmapped).
uniform vec4 uL;   // x Ice (how much the body hides the picture, 0-1), y Glow (how much the light behind shows through,
                   // 0-1), z 0 Fern, 1 Stars, w how long ice takes to thicken (s)
uniform vec4 uTint;   // rgb the ice's color
uniform vec4 uX;   // x the room's light the ice scatters, y edges, z the arms' middles, w the grain
uniform vec4 uB;   // a beat's glint now: x more on the edges, y more on the sparkles
out vec4 fragColor;

#define HEX 1.1547005
#define BLUR 2.5        // the picture behind the ice: this many mip levels blurred
#define WIDE 6.0        // the light behind, spread wide: this level
#define BEND 1.5        // how far the ice's slope bends the picture behind (ice cells)
#define SOFT 0.6        // the mip level the ice's outline is read from (between its cells and their 2 x 2 means)
#define RELIEF 0.6      // how strongly the ice's relief is lit
#define ARMS 2.0        // seconds frozen longer than the ice around that make a whole arm

vec2 grid;

// Stars: s at a point of the grid, blended from the three nearest cell middles of the lattice.
vec2 hexread(vec2 g) {
    float j0 = floor(g.y - 0.5);
    vec3 best[4];
    int n = 0;
    for (int dj = 0; dj <= 1; dj++) {
        float j = j0 + float(dj);
        float shift = mod(j, 2.0) == 1.0 ? 0.5 : 0.0;
        float i0 = floor((g.x - 0.5) / HEX - shift);
        for (int di = 0; di <= 1; di++) {
            float i = i0 + float(di);
            vec2 mid = vec2((i + shift) * HEX + 0.5, j + 0.5);
            best[n++] = vec3(i, j, distance(g, mid));
        }
    }
    // the three nearest of the four
    for (int a = 0; a < 3; a++)
        for (int b = a + 1; b < 4; b++)
            if (best[b].z < best[a].z) { vec3 t = best[a]; best[a] = best[b]; best[b] = t; }
    vec2 acc = vec2(0.0);
    float wsum = 0.0;
    for (int k = 0; k < 3; k++) {
        float w = max(1.0 - best[k].z / HEX, 0.0);
        vec4 s = texelFetch(sTD2DInputs[1], clamp(ivec2(best[k].xy), ivec2(0), ivec2(grid) - 1), 0);
        acc += w * vec2(smoothstep(0.95, 1.05, s.r), s.b);
        wsum += w;
    }
    return acc / max(wsum, 1e-4);
}

// How much ice is at uv (0-1), and how long it has been frozen there.
vec2 ice(vec2 uv) {
    if (uL.z > 0.5) return hexread(uv * grid);
    vec4 s = textureLod(sTD2DInputs[1], uv, SOFT);
    return vec2(s.r, s.b);
}

void main() {
    vec2 uv = vUV.st;
    grid = uTD2DInfos[1].res.zw;
    vec2 o = uTD2DInfos[1].res.xy;
    vec2 here = ice(uv);
    // the ice's slope a cell, from its change between neighboring pixels (the GPU's screen-space derivatives: four
    // more reads of the ice a pixel cost Stars' lattice a millisecond)
    vec2 slope = vec2(dFdx(here.x), dFdy(here.x)) * uTDOutputInfo.res.zw / grid;
    float body = smoothstep(0.38, 0.62, here.x);
    float edge = clamp(length(slope) * 2.5, 0.0, 1.0) * body;
    // broad ice: the ice averaged over 4 x 4 cells; the middles of the arms: where it averaged over 2 x 2 stands above
    // its surroundings
    float broad = smoothstep(0.55, 0.95, textureLod(sTD2DInputs[1], uv, 2.0).r);
    float mid = textureLod(sTD2DInputs[1], uv, 1.0).r;
    vec2 d = 1.5 * o;
    float around = 0.25 * (textureLod(sTD2DInputs[1], uv + vec2(d.x, 0.0), 1.0).r
                         + textureLod(sTD2DInputs[1], uv - vec2(d.x, 0.0), 1.0).r
                         + textureLod(sTD2DInputs[1], uv + vec2(0.0, d.y), 1.0).r
                         + textureLod(sTD2DInputs[1], uv - vec2(0.0, d.y), 1.0).r);
    float spine = uL.z > 0.5 ? 0.0 : clamp((mid - around) * 5.0, 0.0, 1.0) * body;
    // relief: the ice blurred over 4 x 4 cells as a height, lit from the upper left, so where it has frozen over the
    // veins between its arms read as grooves
    vec2 e2 = 2.0 * o;
    vec2 relief = vec2(textureLod(sTD2DInputs[1], uv + vec2(e2.x, 0.0), 2.0).r
                       - textureLod(sTD2DInputs[1], uv - vec2(e2.x, 0.0), 2.0).r,
                       textureLod(sTD2DInputs[1], uv + vec2(0.0, e2.y), 2.0).r
                       - textureLod(sTD2DInputs[1], uv - vec2(0.0, e2.y), 2.0).r);
    float lit = dot(relief, vec2(-0.6, 0.8)) * RELIEF;
    // the arms froze before the ice between them: a cell frozen longer than the ice around it (its age against the
    // age averaged over about 6 x 6 cells) is an arm, thicker and whiter, and stays one however long it all lasts
    float older = uL.z > 0.5 ? 0.0 : clamp((here.y - textureLod(sTD2DInputs[1], uv, 2.5).b) / ARMS, -1.0, 1.0) * body;
    float thick = 1.0 - exp(-here.y / max(uL.w, 1e-3));
    // a fine grain of small crystals: a hash a pixel, smoothed over two
    vec2 q = gl_FragCoord.xy * 0.5;
    vec2 f = fract(q), b = floor(q);
    f = f * f * (3.0 - 2.0 * f);
    float g00 = hash12(b), g10 = hash12(b + vec2(1.0, 0.0)), g01 = hash12(b + vec2(0.0, 1.0)), g11 = hash12(b + 1.0);
    float grain = mix(mix(g00, g10, f.x), mix(g01, g11, f.x), f.y) - 0.5;
    vec3 pic = texture(sTD2DInputs[0], uv).rgb;
    vec3 behind = textureLod(sTD2DInputs[0], uv - slope * o * BEND * 8.0, BLUR).rgb;
    float wide = luma(textureLod(sTD2DInputs[0], uv, WIDE).rgb);
    vec3 light = uTint.rgb * (uX.x + uL.y * 1.6 * wide);
    float spark = step(0.997, float(ihash(uint(gl_FragCoord.x) + 8192u * uint(gl_FragCoord.y))) / 4294967295.0) * body;
    float white = 0.55 + 0.25 * thick + 0.15 * broad + uX.w * grain + lit + 0.3 * older;
    float a = body * uL.x * (0.55 + 0.25 * thick + 0.2 * broad);
    vec3 c = mix(pic, behind * 0.45 + light * white, a);
    c += light * (edge * uX.y * (1.0 + uB.x) + spine * uX.z + spark * 0.5 * (1.0 + uB.y));
    fragColor = TDOutputSwizzle(vec4(clamp(c, 0.0, 1.0), 1.0));
}
