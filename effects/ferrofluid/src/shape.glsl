// Ferrofluid (touchdesigner-effects, MIT): each spike's peak, for surface.glsl to shape it into a cone. The height
// field's spikes are smooth bumps; a real one is a cone with a sharp tip. Near its peak a bump falls off as the square
// of the distance, so knowing the peak's own height is enough to tell how far from it a point is: the highest
// height within half a spike's spacing (a disc of PEAK_R cells) is the peak of the spike a point is on.
// Inputs: 0 the height (field.glsl: r h).
// Out: r h, g the peak's height nearby, a 1.
out vec4 fragColor;

#define PEAK_R 3   // cells: half the spikes' spacing (the builder's WAVE)

void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    ivec2 top = textureSize(sTD2DInputs[0], 0) - 1;
    float peak = -4.0;
    for (int j = -PEAK_R; j <= PEAK_R; j++)
        for (int i = -PEAK_R; i <= PEAK_R; i++)
            if (i * i + j * j <= PEAK_R * PEAK_R + 1)
                peak = max(peak, texelFetch(sTD2DInputs[0], clamp(c + ivec2(i, j), ivec2(0), top), 0).r);
    fragColor = vec4(texelFetch(sTD2DInputs[0], c, 0).r, peak, 0.0, 1.0);
}
