# Video Vocoder

![Two views of the same field side by side, each named in the library's pixel font. Tall spikes of red flowers stand in a green field against a bright, cloudy sky, swaying in the wind. On the left, INPUT: the clip. On the right, VIDEO VOCODER: the same field pumping with the music, one moment so soft that the flowers blur into a red haze, the next crisp, every petal sharp and the reds deep, then easing back](video_vocoder.webp)

*The defaults on red flowers against the sky, the clip on the left, with a song on input 2: the picture softens
between the hits and snaps crisp when the music jumps, at most once a second (Flashing at Calm).*

**New to vocoders?** A vocoder is the machine that makes a synthesizer talk, the robot voice of so much pop and
electronic music. It splits a voice into bands of pitch, from the lowest to the highest, measures how loud each band
is from moment to moment, and lets the matching band of a second sound (a synthesizer chord, say) through only as loud
as that. Homer Dudley built the first one at Bell Labs in 1939. A picture can be split into bands too, by size rather
than pitch: its largest shapes and soft light, then smaller and smaller detail, down to its finest grain. Each band
holds detail twice as fine as the one before, an octave of size, and adding them all back up gives the picture again.
That split is called a Laplacian pyramid.

This effect splits the live picture into seven octaves of detail and makes each one stronger or weaker with the
matching band of the music. The bass pumps the large shapes and the glow, the mids sharpen the edges and features,
and the treble sparkles the finest grain. Each band of the music is judged against its usual level over the last 4
seconds, so a mix heavy in bass doesn't leave the picture overdriven, and what shows is how the music changes. A
quiet moment softens the picture to a haze, and a loud one makes it crisp and vivid, since the detail carries the
picture's colors too. With nothing on input 2, the seven sliders are an equalizer for the picture's detail, and a
slow wave moves through them (Idle Sweep). With every slider at 1 and no music the picture comes back as it was, to
within a fraction of an 8-bit step. I found no other for TouchDesigner; the nearest is stoatworks-labs' vocoder for
Resolume (see Credits), the same idea as a plugin.

**[Download video_vocoder.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/video_vocoder.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `video_vocoder.tox` into your network. It shows TouchDesigner's sample movie of a river running over rocks,
   a slow wave moving through its octaves of detail (Idle Sweep).
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Pictures full of detail show it best:
   leaves and flowers, water, faces, fabric, crowds. A dark or plain picture has little detail to pump.
3. Wire music into input 2 (see Audio input). The picture then follows the music's bands.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Depth Focus then keeps
   the music's changes to near things, or to what lies inside the mask, while the rest keeps the sliders alone.
   Without it the music moves the whole picture.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `video_vocoder.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Video Vocoder page, top to bottom, in five groups: the seven octaves, the music, depth, Flashing, then the
window.

| Parameter | Default | What it does |
|---|---|---|
| Brilliance | 1 | How strong the picture's finest grain is (a pixel or two, at 720 high), 0 to 3, before the music: 1 as it is, 0 gone, 3 three times as strong. The music's brilliance band (6000 Hz and up) drives it, swinging it no further above 1 than at 1. See [The octaves](#the-octaves). |
| Presence | 1 | The same for fine detail, 2 to 4 pixels, driven by the presence band (4000 to 6000 Hz). |
| Upper Mid | 1 | The same for small detail, 4 to 8 pixels, driven by the upper mid band (2000 to 4000 Hz). |
| Mid | 1 | The same for edges and features, 8 to 16 pixels, driven by the mid band (500 to 2000 Hz). |
| Low Mid | 1 | The same for shapes, 16 to 32 pixels, driven by the low mid band (250 to 500 Hz). |
| Bass | 1 | The same for large shapes and soft light, 32 to 64 pixels, driven by the bass band (60 to 250 Hz). |
| Sub Bass | 1 | The same for the largest shapes and the glow, 64 to 128 pixels, driven by the sub bass band (20 to 60 Hz). Below it the picture's broad light and color stay as they are. |
| Drive | 0.75 | How much the music on input 2 moves each octave, 0 to 1: a band of the music above its usual level makes its octave stronger, below it weaker. At 1, a band 0.25 above its usual level (on its 0 to 1 scale) doubles one of the four fine octaves; the three largest swing half as far. With nothing on input 2, how far Idle Sweep swings them. See [Audio input](#audio-input). |
| Release | 0.25 | How long an octave takes to settle after the music makes it jump, in seconds, 0.05 to 1. It jumps up at once as often as Flashing allows (once a second at Calm); in between it follows the music smoothed over a second. |
| Idle Sweep | On | With nothing on input 2, a slow wave moves through the octaves, finest to largest every 4 seconds, so you can see what each one holds. Off: the sliders alone. |
| Depth Focus | 0.5 | With a depth map or mask on input 3: how much the music moves only near things, or what lies inside the mask, 0 to 1. At 1 far things keep the sliders alone. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Flashing | Calm | How often the music may make the octaves jump. Off never: the music moves them only smoothly, over a second. Calm at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The octaves

![Four views of a woman laughing against a dark background, each named in the library's pixel font. INPUT is the clip: she laughs with her eyes creased shut. FINE OCTAVES 0, with the four finest octaves taken out: the same laugh out of focus, her features soft and blurred. FINE OCTAVES 3, with them three times as strong: every wrinkle and pore deeply etched, her skin rough and crunchy. LARGE OCTAVES 3, with the three largest three times as strong: her face lit up and glowing against the black, its shading deepened, its fine texture as it was](video_vocoder_bands.webp)

*The same laugh with no music, the sliders alone: the four fine octaves (Brilliance to Mid) at 0, then at 3, and
the three large ones (Low Mid to Sub Bass) at 3.*

Each octave is the picture at one size minus the picture at half that size, blown back up: what one halving smooths
away. The finest four (Brilliance to Mid, up to 16 pixels) are texture and edges. Taken out, they leave the picture
soft, as if out of focus; made stronger, they sharpen it until it turns crunchy, as heavy sharpening does. The largest
three (Low Mid to Sub Bass, 16 to 128 pixels) are shapes and light. Made stronger, they deepen the shading and make
bright things glow against their surroundings, the look of a photo's clarity or local contrast pushed up; taken out,
the picture goes flat, its shapes washed into its broad light. Below Sub Bass the picture's overall light and color
are never changed. Each octave carries color as well as brightness, so a stronger octave also makes the small things
of its size more vivid.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends the seven bands from its feature bus. Run
`fosfora --signal --feat-bus`, drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your
project, and wire it into input 2. The bands are Fosfora's seven: sub bass (20 to 60 Hz), bass (to 250), low mid (to
500), mid (to 2000), upper mid (to 4000), presence (to 6000) and brilliance (above). Without the feature bus, its bass,
melody and drums stand in: bass for the lowest two bands, melody for the middle three, drums for the top two.

**Raw audio** (an Audio File In or Audio Device In CHOP) gives the bands directly, measured from the sound itself, the
lowest three over the last tenth of a second and the rest over the last fiftieth, which follows a hi-hat closely.
Each band is measured against its own loudest of the last few seconds, so a quiet band such as brilliance moves as
much as the bass. **TouchDesigner's audioAnalysis** gives them from its low, mid and high levels (low for the lowest
two, mid for the middle three, high for the top two).

However they arrive, each band jumps up at once as often as Flashing allows (once a second at Calm, all seven bands
together) and settles back over Release; in between, it follows the band smoothed over a second. Its usual level is
its average over the last 4 seconds. An octave's gain from the music is 1 plus Drive times 4 times how far its band is
above its usual level, between 0 and 3, for the four fine octaves, and half that swing, between 0.5 and 1.5, for the
three largest; a slider multiplies it up to 1, and above 1 the swing stays as it is at 1. So at the defaults, a hi-hat
0.25 above its usual level makes Brilliance 1.75 times as strong, and a pause in the kick takes Sub Bass down toward
half. At Calm the picture jumps crisp once a second at most, on the first hit the gate lets through, and eases back
over Release; Up to 3 per second follows the beat more closely. When music starts after silence, every band is above
its usual level, so the picture turns crisp and settles over the next 4 seconds; when it stops, the picture goes soft
and settles back.

**Nothing wired:** the sliders alone, with Idle Sweep's wave moving through them while it is on.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 0.9 ms on the GPU (95th percentile 1.4 ms) and 0.6 ms on the
CPU, the median of three runs with the Mac otherwise idle. Each level of the pyramid is a quarter the size of the one
above, so all seven together cost about a third of one full-size pass, and only the last pass, which gives the
picture, runs at full size. With raw audio on input 2, measuring the bands raises the CPU time to about 0.9 ms. GPU
times on this Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** Pumping the octaves at every hit flashes, the fine ones as much as the large: on every eighth note at
  140 BPM, the red flowers measured 4 flashes a second at the defaults, past WCAG's 3. So a band jumps up at once only
  through the standard flash gate, all seven bands together, and settles back over Release. Off never jumps, and the
  music moves the octaves only smoothly, over a second. Calm (the default) jumps at most once a second, and Up to 3 per
  second is WCAG 2.3.1's limit.
- **Smooth between jumps.** Rising slowly but falling over Release, a band rippled at every hit between jumps, and with
  a short Release the ripple flipped reds near WCAG's saturated-red line 3 times a second at Calm. So between jumps
  each band follows itself smoothed over a second.
- **Sliders above 1.** A slider multiplied the music's swing, so with every slider at 3 the fine octaves swung between
  0 and 9: 4 flashes a second under the test's beat. Above 1 a slider now raises its octave without widening the swing.
- **The picture's own reds.** Before the gate, the music pumping red flowers' color detail crossed WCAG's red line, and
  a red guard kept every red short of it, turning the flowers orange. With the gate in, the reds keep their promises
  without it, so the effect shows the picture's own colors.
- **No meaning in color.** The effect signals nothing by hue; it shows the picture's own colors, its detail stronger
  or weaker.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully on and off 8 times a second), a dance beat at 140 BPM whose
bands pulse as drums would (the kick's on each beat, the hi-hats' on every eighth note), a song as raw audio, or no
music, and counted the flashes in the worst second by WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 | 1.0 | 1.0 |
| People crossing a plaza | 0.5 | 0.5 | 0.5 | 0.5 |
| Red flowers against the sky | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 1.5 | 0.5, red 1.5 |
| A laughing face | 0.5 | 0.5 | 0.5 | 0.5 |
| Walkers with lanterns at night | 0 | 0 | 0 | 0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 | 2.5 | 1.0 |
| Flowers, 140 BPM | 1.0, red 1.0 | 1.0, red 1.5 | 3.0, red 2.5 | 1.0, red 1.0 |
| Koi, 140 BPM | 0.5, red 1.5 | 1.0, red 2.0 | 1.5, red 2.5 | 0.5, red 1.5 |
| Face, 140 BPM | 0.5 | 1.0 | 2.5 | 0.5 |
| Dancer, a song | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, a song | 1.0, red 1.0 | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 1.0 |
| Koi, a song | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 2.0 | 0.5, red 1.5 |
| Dancer, no music (Idle Sweep) | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, no music (Idle Sweep) | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Flowers, 140 BPM, Drive 1, every slider at 3 | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 1.0 |
| Flowers, 140 BPM, Drive 1, Release 0.05 | 1.0, red 1.0 | 1.0, red 2.0 | 3.0, red 3.0 | 1.0, red 1.0 |
| Flowers, Drive 1, every slider at 3 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Flowers, no music, Drive 1, every slider at 3 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |

Every row keeps its setting's promise: Off adds nothing to the clip's own beyond the measurement's half-flash margin
(the koi's 1.0 against 0.5, and red 1.5 against 1.0 with every slider at 3), Calm adds at most one a second, and
nothing passes WCAG's 3. Up to 3 per second reaches it on the flowers at 140 BPM, as that setting allows. The last
four rows are the far corners of the ranges. The busiest beat flashes least: Release smooths 8 hits a second more
than a dance beat's 4.

## Experimental

- Without Fosfora's feature bus, the bands its bass, melody and drums stand in for are a rough guess: the middle
  three bands all follow its melody, and the top two its drums.

## Credits and license

MIT. The shaders and operators are written for this library, including judging each band against its usual level,
the bands' jumps through the flash gate, the largest octaves' narrower swing, Idle Sweep and the depth focus.

- **The channel vocoder:** H. Dudley, "Remaking Speech" (Journal of the Acoustical Society of America 11, 1939), and
  his vocoder, built at Bell Labs in 1939. Here the picture is the carrier and the music the modulator.
- **The octaves of detail:** P. J. Burt and E. H. Adelson, ["The Laplacian Pyramid as a Compact Image
  Code"](https://doi.org/10.1109/TCOM.1983.1095851) (IEEE Transactions on Communications 31(4), 1983): each level
  smoothed by their generating kernel, here the binomial [1 5 10 10 5 1] / 32, and halved, and each octave a level
  minus the next one expanded. The library's pyramid (`lib/glsl/pyramid_down.glsl` and `pyramid.glsl`, shared with
  effects to come) expands by the cubic B-spline in four bilinear reads, after C. Sigg and M. Hadwiger, ["Fast
  Third-Order Texture
  Filtering"](https://developer.nvidia.com/gpugems/gpugems2/part-iii-high-quality-rendering/chapter-20-fast-third-order-texture-filtering)
  (GPU Gems 2, chapter 20, 2005).
- **The same idea before this one:** [stoatworks-labs/vocoder](https://github.com/stoatworks-labs/vocoder) (MIT,
  2026), a channel vocoder with the picture as the carrier, as an FFGL plugin for Resolume. This effect was written
  from Dudley's and Burt and Adelson's descriptions, not from its code.
- **The seven bands:** Fosfora's split (its `AUDIO-FEATURES.md`), measured from raw audio by the library's audio input
  (`lib/audio_callbacks.py`).
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Fluid, Motion Magnify, Paint, Particles, Pencil and Point Cloud.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
