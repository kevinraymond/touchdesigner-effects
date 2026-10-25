// touchdesigner-effects (MIT), Slit-Scan: each part of the picture from its own moment. The time map says how far
// back each pixel lies, from 0 (now) to 1 (Delay ago); past() (past.glsl) fetches the picture as it was then.
// A normal picture is a slice straight across the video's frames stacked in time (the video cube); this is a slice
// at a tilt (Sweep), a bowl (Rings) or a shape the depth or a noise draws (Depth, Liquid), so whatever moves bends.
// Inputs as past.glsl, and sTD2DInputs[2] the depth (input 3 when wired, else input 1's brightness).
uniform vec4 uMap;    // x: the map (0 Sweep, 1 Rings, 2 Depth, 3 Liquid), y: Bands (below 2: smooth),
                      // z: how far the map is flipped end over end (0-1), w: Delay as the music shapes it (seconds)
uniform vec4 uDir;    // x, y: where Sweep's past lies (a unit vector, turned by Spin), z, w: the rings' center (0-1)
uniform vec4 uLiq;    // x: Liquid's scale, y: how far its noise has moved (0-256, where it repeats)
uniform vec4 uTime;   // x: Between Frames (0 Flow, 1 Blend, 2 Steps), y: time frozen so far (seconds)
out vec4 fragColor;

float lattice(ivec3 p) {   // repeats every 256 along z, so the noise's movement can loop without a jump
    return float(ihash(uint(p.x) ^ ihash(uint(p.y) ^ ihash(uint(p.z & 255))))) / 4294967295.0;
}

// Value noise: hashed lattice values, smoothly interpolated.
float vnoise(vec3 p) {
    ivec3 i = ivec3(floor(p));
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float x00 = mix(lattice(i), lattice(i + ivec3(1, 0, 0)), f.x);
    float x10 = mix(lattice(i + ivec3(0, 1, 0)), lattice(i + ivec3(1, 1, 0)), f.x);
    float x01 = mix(lattice(i + ivec3(0, 0, 1)), lattice(i + ivec3(1, 0, 1)), f.x);
    float x11 = mix(lattice(i + ivec3(0, 1, 1)), lattice(i + ivec3(1, 1, 1)), f.x);
    return mix(mix(x00, x10, f.y), mix(x01, x11, f.y), f.z);
}

void main() {
    vec2 uv = vUV.st;
    float aspect = uTD2DInfos[0].res.z / uTD2DInfos[0].res.w;
    vec2 q = vec2((uv.x - 0.5) * aspect, uv.y - 0.5);   // picture heights from the middle
    int map = int(uMap.x + 0.5);
    float m;
    if (map == 0) {
        vec2 dir = uDir.xy;
        float extent = 0.5 * (abs(dir.x) * aspect + abs(dir.y));   // so the far corners reach 0 and 1
        m = 0.5 + 0.5 * dot(q, dir) / extent;
    } else if (map == 1) {
        vec2 c = vec2((uDir.z - 0.5) * aspect, uDir.w - 0.5);
        vec2 far = max(abs(c - vec2(-0.5 * aspect, -0.5)), abs(c - vec2(0.5 * aspect, 0.5)));
        m = length(q - c) / length(far);
    } else if (map == 2) {
        m = 1.0 - texture(sTD2DInputs[2], uv).r;               // brighter is nearer, and nearer is now
    } else {
        vec3 p = vec3(q * uLiq.x, uLiq.y);
        float v = 0.65 * vnoise(p) + 0.35 * vnoise(p * vec3(2.03, 2.03, 2.0) + vec3(17.0, 5.0, 0.0));
        m = (v - 0.5) * 2.2 + 0.5;
    }
    m = clamp(m, 0.0, 1.0);
    if (uMap.y >= 2.0) m = min(floor(m * uMap.y), uMap.y - 1.0) / (uMap.y - 1.0);
    m = mix(m, 1.0 - m, uMap.z);
    float d = m * min(uMap.w, reach());
    fragColor = past(uv, d + tear(1.0 - uv.y) + uTime.y, int(uTime.x + 0.5));
}
