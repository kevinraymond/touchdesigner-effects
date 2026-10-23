// DEV ONLY (blob round 1): read the compact blob table written by unpack.glsl.
#define MAXB 96
vec4 P(int i, int r) { return texelFetch(sTD2DInputs[DATA], ivec2(i, r), 0); }
int nPacked() { return min(int(P(0, 1).w + 0.5), MAXB); }
