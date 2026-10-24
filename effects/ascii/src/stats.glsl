// ASCII (touchdesigner-effects, MIT): automatic levels, one texel. Input 0 is the mean cell color,
// input 1 the brightest cell (Analyze TOPs), input 2 this pass's previous result (a Feedback TOP).
// The white point aims at 0.9 x the brightest cell's luminance, or 4 x the mean when that is higher (a
// dim, flat picture), within 0.3..1, and eases there over uEase.y seconds, so a highlight that
// appears can't make the whole picture jump.
// Out: r the white point; b marks the result as initialized.
uniform vec2 uEase;   // seconds since the last frame, time constant in seconds
out vec4 fragColor;

void main() {
    const vec3 Y = vec3(0.2126, 0.7152, 0.0722);
    float mean = dot(texelFetch(sTD2DInputs[0], ivec2(0), 0).rgb, Y);
    float peak = dot(texelFetch(sTD2DInputs[1], ivec2(0), 0).rgb, Y);
    float target = clamp(max(0.9 * peak, 4.0 * mean), 0.3, 1.0);
    vec4 prev = texelFetch(sTD2DInputs[2], ivec2(0), 0);
    float k = 1.0 - exp(-uEase.x / max(uEase.y, 1e-3));
    float white = prev.b == 2.0 ? mix(prev.r, target, k) : target;
    fragColor = TDOutputSwizzle(vec4(white, target, 2.0, 1.0));
}
