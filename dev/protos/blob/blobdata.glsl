// DEV ONLY (blob round 1): read blobs from the Blob Track TOP's Info CHOP turned into a texture
// by a CHOP to TOP (one channel per row: row 0 num_blobs, then id, u, v, width, height per blob).
#define MAXB 96
float D(int r) { return texelFetch(sTD2DInputs[DATA], ivec2(0, r), 0).r; }
int nBlobs() {
    int rows = textureSize(sTD2DInputs[DATA], 0).y;
    return clamp(int(D(0) + 0.5), 0, min(MAXB, (rows - 1) / 5));
}
// Center and size in pixels of the output, and the blob's ID.
void blobAt(int i, vec2 res, out int id, out vec2 c, out vec2 sz) {
    int r = 1 + 5 * i;
    id = int(D(r) + 0.5);
    c = vec2(D(r + 1), D(r + 2)) * res;
    sz = vec2(D(r + 3), D(r + 4)) * res;
}
