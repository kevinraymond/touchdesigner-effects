// Point Cloud (touchdesigner-effects, MIT). The kept points, for finding the cloud's middle: an
// Analyze TOP averages this, and the average of xyz divided by the average of a is their middle.
// Inputs: 0 the points (pos.glsl).
// Out: rgb the point where it is kept, else 0; a 1 where it is kept, else 0.
out vec4 fragColor;

void main() {
    vec4 p = texelFetch(sTD2DInputs[0], ivec2(gl_FragCoord.xy), 0);
    float kept = p.w > 0.0 ? 1.0 : 0.0;
    fragColor = vec4(p.xyz * kept, kept);
}
