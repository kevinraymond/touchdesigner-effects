// touchdesigner-effects (MIT), Pencil: the pencil strokes the tone is drawn with, drawn once when the effect loads
// (nothing here changes, so it cooks once): six levels of hatching for Hatching, and a tonal pattern for Sketch.
// The hatching follows the tonal art maps of Praun, Hoppe, Webb and Finkelstein ("Real-Time Hatching", SIGGRAPH 2001),
// six levels as theirs: each level holds every stroke of the lighter levels and adds more, so moving between levels
// only adds or takes away strokes, never moves them. Levels 1-4 add long parallel strokes until the rows are full, and
// 5-6 strokes across them, as their maps do, so the tone is drawn in parallel lines until the darks. Each stroke has a
// rank, and a level draws the strokes ranked below its share.
// Sketch's tonal pattern stands for the scanned pencil shading Lu, Xu and Jia draw with: many short, light strokes in
// three families (along the rows and along both diagonals), each stroke turned a little at random, so the pattern has no
// direction to follow, only graphite grain.
// A stroke is a slightly bowed line tapering to its ends, laid with an uneven pressure; strokes sit in rows, each row
// offset along itself so their ends don't line up. The texture repeats every uP.x pixels each way (the rows and cells
// fit it exactly, and the hash wraps with them), so draw.glsl can lay it at any angle and offset without a seam.
// Out: [0] rgb the light let through by hatching levels 1-3, a by Sketch's pattern; [1] rgb by levels 4-6, a 1 (the
// paper, 1; lower where graphite lies).
uniform vec4 uP;   // x the repeat (pixels at 720 high), then the hatching: y a stroke's cell along its row, z the rows'
                   // spacing, w a stroke's half width
uniform vec4 uQ;   // the hatching: x the strokes' turn (radians, at most), y how much they bow (pixels), z, w the
                   // lightest and heaviest pressure
uniform vec4 uS;   // Sketch's pattern: x a stroke's cell, y the rows' spacing, z a stroke's half width, w the turn
uniform vec4 uT;   // Sketch's pattern: x the bow, y, z the lightest and heaviest pressure
layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];

const float MAIN[6] = float[6](0.25, 0.5, 0.75, 1.0, 1.0, 1.0);
const float ACROSS[6] = float[6](0.0, 0.0, 0.0, 0.0, 0.5, 1.0);
const float ALL[6] = float[6](1.0, 1.0, 1.0, 1.0, 1.0, 1.0);

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
// light T each level lets through when the stroke's rank is below the level's share in thr. cell, space, width and bow
// are in pixels; turn is the most a stroke turns from its row; plo and phi its pressure.
void layer(vec2 q, float s, uint seed, float cell, float space, float width, float turn, float bow, float plo, float phi,
           float thr[6], inout float T[6]) {
    float period = uP.x * s;
    int nrow = int(round(period / (space * s))), ncell = int(round(period / (cell * s)));
    float sp = period / float(nrow), ce = period / float(ncell);
    float w = width * s, b = bow * s;
    int j0 = int(floor(q.y / sp));
    for (int dj = -2; dj <= 2; dj++) {
        int j = j0 + dj, jw = imod(j, nrow);
        float uo = q.x + rnd(jw, 3, seed) * ce;
        int i0 = int(floor(uo / ce));
        for (int di = -2; di <= 2; di++) {
            int i = i0 + di, iw = imod(i, ncell);
            uint k = seed * 131u;
            float cu = (float(i) + rnd(iw, jw, k + 1u)) * ce;
            float cv = (float(j) + 0.5 + (rnd(iw, jw, k + 2u) - 0.5) * 0.35) * sp;
            float len = ce * (0.9 + 0.7 * rnd(iw, jw, k + 3u));
            float th = (rnd(iw, jw, k + 4u) - 0.5) * 2.0 * turn;
            float du = uo - cu, dv = q.y - cv;
            float along = du * cos(th) + dv * sin(th);
            float across = -du * sin(th) + dv * cos(th);
            float e = 2.0 * along / len;
            across -= (rnd(iw, jw, k + 5u) - 0.5) * b * max(1.0 - e * e, 0.0);
            float t = abs(e);
            float taper = t < 1.0 ? 1.0 - t * t : 0.0;
            float pressure = mix(plo, phi, rnd(iw, jw, k + 6u));
            float a = clamp(exp(-(across * across) / (w * w)) * taper * pressure, 0.0, 1.0);
            float rank = rnd(iw, jw, k + 7u);
            for (int n = 0; n < 6; n++)
                if (rank < thr[n]) T[n] *= 1.0 - a;
        }
    }
}

void main() {
    vec2 p = gl_FragCoord.xy;
    float H[6] = float[6](1.0, 1.0, 1.0, 1.0, 1.0, 1.0);
    layer(p, 1.0, 1u, uP.y, uP.z, uP.w, uQ.x, uQ.y, uQ.z, uQ.w, MAIN, H);
    layer(p.yx, 1.0, 8u, uP.y, uP.z, uP.w, uQ.x, uQ.y, uQ.z, uQ.w, ACROSS, H);
    // Sketch: along x, along the diagonal and along the other diagonal (x + y and y - x repeat every uP.x as x and y
    // do, at sqrt 2 units a pixel), each family turned at random by up to uS.w.
    float S[6] = float[6](1.0, 1.0, 1.0, 1.0, 1.0, 1.0);
    layer(p, 1.0, 21u, uS.x, uS.y, uS.z, uS.w, uT.x, uT.y, uT.z, ALL, S);
    layer(vec2(p.x + p.y, p.y - p.x), 1.41421356, 34u, uS.x, uS.y, uS.z, uS.w, uT.x, uT.y, uT.z, ALL, S);
    layer(vec2(p.y - p.x, p.x + p.y), 1.41421356, 55u, uS.x, uS.y, uS.z, uS.w, uT.x, uT.y, uT.z, ALL, S);
    fragColor[0] = vec4(H[0], H[1], H[2], S[0]);
    fragColor[1] = vec4(H[3], H[4], H[5], 1.0);
}
