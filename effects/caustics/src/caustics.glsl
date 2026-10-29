// touchdesigner-effects (MIT), Caustics: the light the water's surface focuses onto the pool's floor, after C. Yuksel
// and J. Keyser, "Fast Real-time Caustics from Height Fields" (The Visual Computer 25, 2009). The floor's caustics map
// is gathered from the surface above it: every surface sample (one a pixel of this map) refracts the sun's light down
// through its own slope to the floor, and a square one pixel wide around where it lands lights the floor pixels it
// overlaps, by how much of it each one covers. Flat water lands every square exactly on its own pixel, so the floor is
// lit 1 everywhere; where the surface curves, neighboring squares crowd together (bright lines) or spread apart (dark).
// Each sample's square is the same size whatever its ray did: a square sized by how its ray spreads from its
// neighbors' is what NVIDIA's US 11,830,125 claims, and nothing is kept from one frame to the next (US 12,315,070
// updates its light particles over frames). See private/patents/caustics.md.
// The paper gathers for each floor pixel the samples within a window R of its illumination center, in two separable
// passes. Here a workgroup takes a TILE x TILE patch of the floor, every surface sample within REACH of it (light
// from farther away is left out, the paper's window), adds each sample's square into the patch's tally in shared
// memory, and writes the patch. At Depth 1 the window keeps all the light; at 2 about 95% of it, and at 3 three
// quarters, which is why Depth stops at 2 (three tallies of a wider window outgrow the Mac's 32 KB of shared memory). The light is lit in the rest surface's frame: the sun's tilt moves every square by
// the same amount over flat water, and that amount is taken off, so the caustics lie under the water that made them.
// Rainbow: three indices of refraction, one a color, red bending least, so the bright lines get colored fringes.
// Beyond the picture's edges the water goes on as it is at the edge.
// Inputs: 0 the surface (surface.glsl: r height, g b slope, a depth, in this map's pixels).
// Out (the surface's size): rgb the light on the floor (1 where the water is flat), a 1.
layout (local_size_x = 16, local_size_y = 16) in;
#define TILE 16
#define REACH 16
#define SIDE 48              // TILE + 2 REACH
#define SCALE 256.0          // the tallies are whole numbers: a square's share in 256ths
uniform vec4 uC;             // xyz the sun's direction (unit, downward), w the index of refraction
uniform vec4 uR;             // x Rainbow's spread of the index (0: one color for all three)
shared uint sR[SIDE * SIDE];
shared uint sG[SIDE * SIDE];
shared uint sB[SIDE * SIDE];

void tally(int ch, int i, float w) {
    uint u = uint(w * SCALE + 0.5);
    if (u == 0u) return;
    if (ch == 0) atomicAdd(sR[i], u);
    else if (ch == 1) atomicAdd(sG[i], u);
    else atomicAdd(sB[i], u);
}

// A one-pixel square centered at `at` (in the patch's pixels, centers at .5): its overlap with each pixel it covers.
void land(int ch, vec2 at) {
    vec2 q = at - 0.5;
    ivec2 i0 = ivec2(floor(q));
    vec2 f = q - vec2(i0);
    for (int dy = 0; dy < 2; dy++) {
        for (int dx = 0; dx < 2; dx++) {
            ivec2 c = i0 + ivec2(dx, dy);
            if (c.x < 0 || c.y < 0 || c.x >= SIDE || c.y >= SIDE) continue;
            float w = (dx == 0 ? 1.0 - f.x : f.x) * (dy == 0 ? 1.0 - f.y : f.y);
            tally(ch, c.y * SIDE + c.x, w);
        }
    }
}

void main() {
    ivec2 size = textureSize(sTD2DInputs[0], 0);
    ivec2 corner = ivec2(gl_WorkGroupID.xy) * TILE - REACH;
    uint me = gl_LocalInvocationIndex;
    for (uint i = me; i < uint(SIDE * SIDE); i += 256u) {
        sR[i] = 0u;
        sG[i] = 0u;
        sB[i] = 0u;
    }
    memoryBarrierShared();
    barrier();
    int colors = uR.x > 0.0 ? 3 : 1;
    for (uint i = me; i < uint(SIDE * SIDE); i += 256u) {
        ivec2 q = ivec2(int(i) % SIDE, int(i) / SIDE);
        vec4 s = texelFetch(sTD2DInputs[0], clamp(corner + q, ivec2(0), size - 1), 0);
        vec3 n = normalize(vec3(-s.g, -s.b, 1.0));
        float run = max(s.a + s.r, 0.0);
        for (int c = 0; c < colors; c++) {
            float eta = 1.0 / (uC.w + uR.x * float(1 - c));          // red bends least
            vec3 t = refract(uC.xyz, n, eta);
            vec3 t0 = refract(uC.xyz, vec3(0.0, 0.0, 1.0), eta);
            vec2 d = t.xy * run / max(-t.z, 1e-3) - t0.xy * s.a / max(-t0.z, 1e-3);
            land(c, vec2(q) + 0.5 + d);
        }
    }
    memoryBarrierShared();
    barrier();
    ivec2 l = ivec2(gl_LocalInvocationID.xy);
    ivec2 at = corner + REACH + l;
    if (at.x >= size.x || at.y >= size.y) return;
    int k = (l.y + REACH) * SIDE + l.x + REACH;
    vec3 light = colors == 3 ? vec3(sR[k], sG[k], sB[k]) / SCALE : vec3(float(sR[k]) / SCALE);
    imageStore(mTDComputeOutputs[0], at, TDOutputSwizzle(vec4(light, 1.0)));
}
