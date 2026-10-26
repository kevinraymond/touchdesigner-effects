// touchdesigner-effects (MIT), Pencil: the pencil strokes the tone is drawn with, eight levels from a few light strokes
// to dense cross-hatching, drawn once when the effect loads (nothing here changes, so it cooks once).
// It follows the tonal art maps of Praun, Hoppe, Webb and Finkelstein ("Real-Time Hatching", SIGGRAPH 2001): each
// level holds every stroke of the lighter levels and adds more, so moving between levels only adds or takes away
// strokes, never moves them. The lighter levels add parallel strokes, the middle ones strokes across them, the darkest
// ones a diagonal third layer, as their maps do. Each stroke has a rank, and a level draws the strokes ranked below its
// share. A stroke is a slightly bowed, slightly tilted line about a pixel and a half wide, tapering to its ends, laid
// with an uneven pressure; strokes sit in rows, each row offset along itself so their ends don't line up.
// The texture repeats every uP.x pixels each way (the rows and cells fit it exactly, and the hash wraps with them), so
// draw.glsl can lay it at any angle and offset without a seam. Hatching reads it turned along the picture's edges,
// Sketch reads two of its lighter levels crossed as Lu, Xu and Jia's tonal pattern.
// Out: [0] rgba the light let through by levels 1-4, [1] by levels 5-8 (1 the paper, lower where graphite lies).
uniform vec4 uP;   // x the repeat (pixels at 720 high), y a stroke's cell along its row, z the rows' spacing,
                   // w a stroke's half width
uniform vec4 uQ;   // x the strokes' tilt (radians, at most), y how much they bow (pixels), z, w the lightest and
                   // heaviest pressure
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];

const float MAIN[8] = float[8](0.2, 0.4, 0.6, 0.8, 1.0, 1.0, 1.0, 1.0);
const float ACROSS[8] = float[8](0.0, 0.0, 0.0, 0.0, 0.35, 0.7, 1.0, 1.0);
const float DIAG[8] = float[8](0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0);

// Integer hash "lowbias32" from Chris Wellons' hash-prospector (public domain, the Unlicense), as in lib common.glsl,
// which this pass can't include: it reads its inputs' sizes, and this pass has no input.
uint ihash(uint x) {
    x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16;
    return x;
}

int imod(int a, int n) {
    return ((a % n) + n) % n;
}

float rnd(int i, int j, uint k) {
    return float(ihash(uint(i) ^ ihash(uint(j) ^ ihash(k)))) / 4294967295.0;
}

// One layer of strokes along u in rows across v (q in this layer's units, s of them to a pixel), multiplied into the
// light T each level lets through when the stroke's rank is below the level's share in thr.
void layer(vec2 q, float s, uint seed, float thr[8], inout float T[8]) {
    float period = uP.x * s;
    int nrow = int(round(period / (uP.z * s))), ncell = int(round(period / (uP.y * s)));
    float space = period / float(nrow), cell = period / float(ncell);
    float width = uP.w * s, bow = uQ.y * s;
    int j0 = int(floor(q.y / space));
    for (int dj = -1; dj <= 1; dj++) {
        int j = j0 + dj, jw = imod(j, nrow);
        float uo = q.x + rnd(jw, 3, seed) * cell;
        int i0 = int(floor(uo / cell));
        for (int di = -2; di <= 2; di++) {
            int i = i0 + di, iw = imod(i, ncell);
            uint k = seed * 131u;
            float cu = (float(i) + rnd(iw, jw, k + 1u)) * cell;
            float cv = (float(j) + 0.5 + (rnd(iw, jw, k + 2u) - 0.5) * 0.35) * space;
            float len = cell * (0.9 + 0.7 * rnd(iw, jw, k + 3u));
            float th = (rnd(iw, jw, k + 4u) - 0.5) * 2.0 * uQ.x;
            float du = uo - cu, dv = q.y - cv;
            float along = du * cos(th) + dv * sin(th);
            float across = -du * sin(th) + dv * cos(th);
            float e = 2.0 * along / len;
            across -= (rnd(iw, jw, k + 5u) - 0.5) * bow * max(1.0 - e * e, 0.0);
            float t = abs(e);
            float taper = t < 1.0 ? 1.0 - t * t : 0.0;
            float pressure = mix(uQ.z, uQ.w, rnd(iw, jw, k + 6u));
            float a = clamp(exp(-(across * across) / (width * width)) * taper * pressure, 0.0, 1.0);
            float rank = rnd(iw, jw, k + 7u);
            for (int n = 0; n < 8; n++)
                if (rank < thr[n]) T[n] *= 1.0 - a;
        }
    }
}

void main() {
    vec2 p = gl_FragCoord.xy;
    float T[8] = float[8](1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0);
    layer(p, 1.0, 1u, MAIN, T);
    layer(p.yx, 1.0, 8u, ACROSS, T);
    // The diagonal: x + y along it and y - x across, both repeating every uP.x as x and y do, at sqrt 2 units a pixel.
    layer(vec2(p.x + p.y, p.y - p.x), 1.41421356, 15u, DIAG, T);
    fragColor[0] = vec4(T[0], T[1], T[2], T[3]);
    fragColor[1] = vec4(T[4], T[5], T[6], T[7]);
}
