// touchdesigner-effects (MIT), Temporal Resonator: where the string's delay line is read. The state goes into the
// ring once a cook, a cook late, with its stamp beside it; a Texture 3D TOP writes the next slot every cook and says
// nothing of which (docs/BUILDING.md), so the newest slot is the one stamped with the last cook's serial, and walking
// back from it, a slot belongs to the string while its serial is the next one down and no pause lies between it and the
// newer one. Each tap is a moment some seconds back, between two slots: Karplus and Strong's loop averages the sample
// one period back with the one before it, and here three taps, the delay and a little either side, weighted 1, 2, 1,
// average around one beat back, so the loop's delay stays one beat however soft it is (Jaffe and Smith tune the
// loop's delay the same way, with a fractional delay).
// Inputs: sTD2DInputs[0] this cook's stamp (stamp.glsl), sTD2DArrayInputs[0] the stamps ring.
// Out (3 x 1), per tap (0 the delay less the spread, 1 the delay, 2 the delay plus the spread): r the newer slot, g
// the older, b how far from the newer to the older (0-1), a 1 when the string reaches back that far, else 0.
uniform vec4 uT;   // x the delay (s), y the spread (s), z the longest pause the string rings through (s), w the clock's
                   // wrap (CLOCK)
out vec4 fragColor;
const float SERIALS = 1048576.0;

vec4 stampAt(int slot) { return texelFetch(sTD2DArrayInputs[0], ivec3(0, 0, slot), 0); }
float since(float now, float then) { return mod(now - then + uT.w, uT.w); }

void main() {
    float d = max(uT.x + (gl_FragCoord.x - 1.5) * uT.y, 0.0);
    int n = textureSize(sTD2DArrayInputs[0], 0).z;
    vec4 cur = texelFetch(sTD2DInputs[0], ivec2(0), 0);
    // The newest slot holds the last cook's state, stamped with its serial.
    float want = mod(cur.r - 1.0 + SERIALS, SERIALS);
    int newest = -1;
    for (int k = 0; k < n; k++) {
        if (stampAt(k).r == want) { newest = k; break; }
    }
    fragColor = vec4(0.0);
    if (newest < 0 || cur.b > 0.5) return;
    float newerAge = -1.0, tNewer = cur.g;
    int newer = -1;
    for (int a = 0; a < n; a++) {
        int s = (newest - a + n) % n;
        vec4 st = stampAt(s);
        if (st.r != mod(want - float(a) + SERIALS, SERIALS) || since(tNewer, st.g) > uT.z) return;
        float age = since(cur.g, st.g);
        if (age >= d) {
            float u = newer < 0 ? 0.0 : clamp((d - newerAge) / max(age - newerAge, 1e-5), 0.0, 1.0);
            fragColor = vec4(float(newer < 0 ? s : newer), float(s), u, 1.0);
            return;
        }
        if (st.b > 0.5) return;    // the string started again here: nothing older belongs to it
        newer = s;
        newerAge = age;
        tNewer = st.g;
    }
}
