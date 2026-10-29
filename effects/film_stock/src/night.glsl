// Film Stock (touchdesigner-effects, MIT). Day for night, the detail: at night the eye loses fine detail but what it
// sees doesn't look blurred (Thompson, Shirley and Ferwerda 2002). So the night image is blurred to take the fine
// detail out, and the edges that remain are sharpened by raising the band between a fine blur and a wider one to the
// power 1 / 1.25, which steepens it near its zero crossings, where the edges are, without ringing. The paper's wider
// blur is a Gaussian 1.6 times the fine one's; here it is a triangle (bartlette) blur of about that width, so no two
// Gaussian blurs are subtracted (NVIDIA's US 8,064,726 claims rendering with a sum of Gaussians). What is bright enough
// for the cones keeps the day picture's own sharp color (the scotopic share s from night_src), and Day for Night mixes
// the whole against the day.
// Inputs: 0 the exposure (day, linear), 1 night_src (the night color, s in alpha), 2 its fine blur, 3 its wide blur.
// Out: linear light.
uniform vec4 uN;      // x Day for Night 0-1
out vec4 fragColor;
#define EDGE 1.25

void main() {
    vec2 uv = vUV.st;
    vec3 day = texture(sTD2DInputs[0], uv).rgb;
    float s = texture(sTD2DInputs[1], uv).a;
    vec3 fine = texture(sTD2DInputs[2], uv).rgb, wide = texture(sTD2DInputs[3], uv).rgb;
    vec3 band = fine - wide;
    vec3 night = wide + sign(band) * pow(abs(band), vec3(1.0 / EDGE));
    vec3 c = mix(day, max(night, 0.0), s);
    fragColor = vec4(mix(day, c, uN.x), 1.0);
}
