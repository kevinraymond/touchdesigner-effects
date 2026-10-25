// Bent Cam (touchdesigner-effects, MIT). The computer decodes the JPEG: each pixel is put back together from the
// 64 coefficients of its blocks (the inverse DCT), and Y, U, V become R'G'B' by BT.601. A block cut off by the
// frame's edge has lost the coefficients that fell outside it, and decodes a little soft.
// Inputs: 0 the coefficients (dct). Out: R'G'B', the camera's picture as the computer gets it.
out vec4 fragColor;

void main() {
    ivec2 p = ivec2(gl_FragCoord.xy);
    int W = int(uTDOutputInfo.res.z), H = int(uTDOutputInfo.res.w);
    int n = lineOf(p, H), x = p.x;
    int xi = x & 7, xci = (x & 15) >> 1, yi = n & 7, x0 = x & ~7, xc0 = x & ~15, y0 = n & ~7;
    float cx[8], cxc[8], cy[8];
    for (int k = 0; k < 8; k++) {
        float a = k == 0 ? 0.70710678 : 1.0;
        cx[k] = a * cos(float(2 * xi + 1) * float(k) * PI / 16.0);
        cxc[k] = a * cos(float(2 * xci + 1) * float(k) * PI / 16.0);
        cy[k] = a * cos(float(2 * yi + 1) * float(k) * PI / 16.0);
    }
    vec3 f = vec3(0.0);
    for (int v = 0; v < 8; v++) {
        if (y0 + v >= H) break;
        int row = H - 1 - (y0 + v);
        for (int u = 0; u < 8; u++) {
            if (x0 + u < W) f.x += texelFetch(sTD2DInputs[0], ivec2(x0 + u, row), 0).r * cx[u] * cy[v];
            if (xc0 + 2 * u < W) f.yz += texelFetch(sTD2DInputs[0], ivec2(xc0 + 2 * u, row), 0).gb * cxc[u] * cy[v];
        }
    }
    f = 0.25 * f + 128.0;
    float Y = (f.x - 16.0) / 219.0, Pb = (f.y - 128.0) / 224.0, Pr = (f.z - 128.0) / 224.0;
    vec3 c = vec3(Y + 1.402 * Pr, Y - 0.344136 * Pb - 0.714136 * Pr, Y + 1.772 * Pb);
    fragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
