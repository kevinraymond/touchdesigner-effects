// touchdesigner-effects (MIT), shared by the effects that follow the picture's edges (lib/glsl,
// structure_tensor()): the structure tensor of the picture's color, per pixel, before smoothing. For each of
// R, G and B the gradient (fx, fy) comes from the derivative filter of Jaehne, Scharr and Koerkel (1999),
// rotationally more symmetric than Sobel's, as Kyprianidis and Doellner use it ("Image and Video Abstraction by
// Multi-scale Anisotropic Kuwahara Filtering", NPAR 2011, 3.2.1):
//     Dx = 1/2 [ p1 0 -p1 ; 1-2p1 0 2p1-1 ; p1 0 -p1 ],  Dy = Dx transposed,  p1 = 0.183
// and the tensor is the sum of the three channels' outer products (Di Zenzo 1986):
//     E = sum fx^2,  F = sum fx fy,  G = sum fy^2.
// tensor_blur.glsl smooths it, which estimates the orientation better than blurring the picture first
// (Brox et al. 2006), and tensor_flow.glsl reads the orientation and anisotropy out of it.
// Inputs: 0 the picture (Input Extend Mode UV Hold, so the frame's edges aren't a cliff to black).
// Out: r E, g F, b G (gradients per pixel, the picture's values 0-1), a 1.
out vec4 fragColor;

const float P1 = 0.183;

vec3 at(vec2 uv, float i, float j) {
    return texture(sTD2DInputs[0], uv + vec2(i, j) * uTD2DInfos[0].res.xy).rgb;
}

void main() {
    vec2 uv = vUV.st;
    vec3 a = at(uv, -1.0, 1.0), b = at(uv, 0.0, 1.0), c = at(uv, 1.0, 1.0);
    vec3 d = at(uv, -1.0, 0.0),                       f = at(uv, 1.0, 0.0);
    vec3 g = at(uv, -1.0, -1.0), h = at(uv, 0.0, -1.0), k = at(uv, 1.0, -1.0);
    // x grows to the right and y upward, as UV does in TouchDesigner.
    vec3 fx = 0.5 * (P1 * (c - a) + (1.0 - 2.0 * P1) * (f - d) + P1 * (k - g));
    vec3 fy = 0.5 * (P1 * (a - g) + (1.0 - 2.0 * P1) * (b - h) + P1 * (c - k));
    fragColor = vec4(dot(fx, fx), dot(fx, fy), dot(fy, fy), 1.0);
}
