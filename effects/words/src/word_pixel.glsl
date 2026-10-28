// touchdesigner-effects (MIT), Words: a word's letters, colored. The atlas holds the letters as the font drew them,
// antialiased; drawn bigger than that, the coverage is treated as a distance to the letters' edge (a half is the edge)
// and cut at one picture pixel's width, so a big word stays crisp. Smaller, the atlas's mipmaps average it.
// Color: the picture under each letter, the picture's color across the word, or white. Lift brightens the dark
// ones (1 - e^(-k c), normalized so white stays white); in Cloud it also gives black a floor of gray, so words on a dark
// subject still show (Portrait and Lines draw the whole picture in words, and their dark words stay dark). A beat (Beat Pump) and the music getting louder than usual (Swell) brighten every word.
uniform vec4 uRes;     // x, y the picture's size (pixels)
uniform vec4 uLook;    // x Color (0 picture, 1 word, 2 white), y Lift (0-1), z how much brighter (beat, swell), w gray
                       // floor (1 Cloud, 0 Portrait and Lines)
uniform sampler2D sAtlas;
uniform sampler2D sPicture;

in vec2 vUV;
flat in float vAlpha;
flat in float vScale;
flat in vec3 vColor;
out vec4 oFragColor;

void main() {
    TDCheckDiscard();
    float cov = texture(sAtlas, vUV).a;
    if (vScale > 1.0) cov = smoothstep(0.5 - 0.5 / vScale, 0.5 + 0.5 / vScale, cov);
    vec3 col = uLook.x < 0.5 ? texture(sPicture, gl_FragCoord.xy / uRes.xy).rgb : uLook.x < 1.5 ? vColor : vec3(1.0);
    if (uLook.y > 0.01) {
        float k = 3.0 * uLook.y;
        col = (1.0 - exp(-k * col)) / (1.0 - exp(-k));
        float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
        col += (1.0 - col) * 0.4 * uLook.y * uLook.w * (1.0 - l) * (1.0 - l);
    }
    col = min(col * (1.0 + uLook.z), vec3(1.0));
    float a = cov * vAlpha;
    oFragColor = TDOutputSwizzle(vec4(col * a, a));
}
