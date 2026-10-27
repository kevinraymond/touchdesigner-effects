# Chladni Sand

![Two views of red flowers against a bright, cloudy sky side by side, each named in the library's pixel font. On the left, INPUT, the clip. On the right, CHLADNI SAND, the same field struck by the music. On each beat the sky's light slides into glowing curved lines and rings, the flowers' red gathers into bright bands between dark hollows, and between beats the picture settles back to the flowers](chladni_sand.webp)

*The defaults on red flowers against the sky, the clip on the left, with a song on input 2. Each beat strikes the
plate, at most once a second (Flashing at Calm), and the picture's light gathers on the figure's lines, then settles
back.*

**New to Chladni figures?** In 1787 Ernst Chladni strewed sand on a thin metal plate, held it at its center and drew a
violin bow along its edge. The plate rang, and the sand jumped away from the parts that shook and gathered on the lines
that kept still, the nodal lines, drawing a figure of curves, stars and rings. Each note drew a different figure, and
higher notes drew busier ones. In 1833 Charles Wheatstone showed that every such figure is the sum of a few simple
ways the plate can bend, its modes. The same experiment is still a favorite in physics classes and science museums,
often with a loudspeaker under the plate, and in videos of "cymatics".

This effect makes the picture the sand. Each of the music's seven bands, from the sub bass to the brilliance, sets one
of a square plate's modes, the lowest band the simplest figure (a star) and the highest the busiest (a grid of
clover shapes), and the bands rising most above their usual level shape the figure, so it turns as the music does. Each beat
strikes the plate. The picture's light then slides toward the figure's lines and piles up there in the picture's own
colors, up to twice as bright, while the parts between empty out toward black. Over Settle it all slides back, and the
picture is itself again until the next beat. With nothing on input 2, Idle Strike strikes the plate every 2 seconds,
each time in the next figure. A depth map or mask on input 3 keeps the sand moving on near things. I found Chladni
figures in TouchDesigner drawn with particles (see Credits), but none that moves the picture itself.

**[Download chladni_sand.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/chladni_sand.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `chladni_sand.tox` into your network. It shows TouchDesigner's sample movie of mist over a lake, struck every
   2 seconds by each of the plate's seven figures in turn (Idle Strike).
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Bright, broad areas make the clearest
   figures, such as sky, mist, smoke, water or a lit wall. A dark picture has little light to pile up.
3. Wire music into input 2 (see Audio input). The beats then strike the plate, and the bands shape the figure.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Depth Focus then keeps
   the sand moving on near things, or inside the mask, while the rest stays still. Without it the whole picture is
   sand.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `chladni_sand.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Chladni Sand page holds, top to bottom, the sand, the music, depth, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Speed | 1 | How fast the sand travels toward the lines, 0.25 to 2. At 1 it moves up to nearly half the picture's height in a second while the plate shakes hardest. |
| Settle | 0.4 | How long the picture takes to come back after the sand moves, in seconds, 0.1 to 2. Short lets the figure form on each strike and clear between them; long keeps it hanging, so strikes build on each other. |
| Strike | 0.75 | How hard each beat on input 2 strikes the plate, 0 to 1. A strike rings down over a third of a second. The plate is struck as often as Flashing allows. |
| Swell | 0.5 | How much the music's bands rising above their usual level shake the plate between beats, 0 to 1. It follows them smoothed over a second. |
| Idle Strike | On | With nothing on input 2, the plate is struck every 2 seconds, each time in the next of its seven figures, so you can see them. Off, the picture rests. Flashing Off stops it too. |
| Depth Focus | 0.5 | With a depth map or mask on input 3, how much the sand moves only on near things, or inside the mask, 0 to 1. At 1 far things stay still. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away, in meters, counts as the far end of the depth. |
| Flashing | Calm | How often the plate may be struck. Off never strikes it, so only Swell moves the sand, smoothly. Calm strikes at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The figures

![Eight views of red flowers against a bright sky, each named in the library's pixel font, two to a row. INPUT is the clip. Then the seven figures, each the moment after a strike, the sky's light gathered into white lines and the flowers' red into glowing rings around dark hollows. SUB BASS has a few broad dark hollows, BASS two large round hollows in a diamond of light, LOW MID rows of smaller hollows, MID rings set in a lattice of diagonal lines, UPPER MID rings around a star, PRESENCE a grid of smaller rings, and BRILLIANCE, the busiest, a tight grid of clover-shaped hollows](chladni_sand_figures.webp)

*The seven figures with no music, each drawn by Idle Strike a moment after it struck, at the defaults, named by the
band whose mode it is.*

The plate is square, as tall as the picture and centered on it, and its figure runs on past its sides. Each band of
the music sets one mode, a figure of the form cos(n&pi;x) cos(m&pi;y) - cos(m&pi;x) cos(n&pi;y), with more lines the
higher the band: (1, 3) for the sub bass, then (2, 4), (2, 5), (3, 6), (3, 7), (4, 8) and (5, 8) for the brilliance.
The plate's shape is the seven summed, each weighted by how far its band has risen above its usual level (its average
over the last 4 seconds), plus a little of the band itself, so some figure is always there to strike. When one band
surges, its figure stands out; when several do, their figures mix into new ones, as Wheatstone found the plate's do.

Sand drifts away from where the plate shakes most and settles where it keeps still, so the light flows toward the
figure's lines from both sides and stops on them. It keeps its amount as it moves: light that leaves the parts between
the lines is the light that piles up on them, which is why the hollows go dark as the lines grow bright. The picture's
own colors travel with it, so a red flower's light makes a red line and the sky's a white one.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends the seven bands from its feature bus. Run `fosfora
--signal --feat-bus`, drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and
wire it into input 2. Its beats strike the plate. Without the feature bus, its bass, melody and drums stand in for the
bands. **Raw audio** (an Audio File In or Audio Device In CHOP) gives the bands and the beats from the sound itself.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the bands from its low, mid and high
levels.

Each band is smoothed over a second and judged against its usual level. Each beat strikes the plate as often as
Flashing allows (once a second at Calm, so on a dance track it follows every other beat or so), and a strike rings down
over a third of a second. Between beats, the largest rise of any band above its usual level shakes the plate gently and
smoothly (Swell).

**Nothing wired:** Idle Strike, every 2 seconds, each figure in turn; or with it off, the picture at rest.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 0.55 ms on the GPU (95th percentile 0.84 ms) and 0.3 ms on the
CPU, the median of three runs with the Mac otherwise idle. The plate is worked out at a quarter of the picture's size,
and its flow and divergence come straight from the modes' formulas, with nothing measured from neighboring pixels; the
sand and its display run at full size, one pass each. With raw audio on input 2, measuring the bands raises the CPU
time to about 0.6 ms. GPU times on this Mac wander from run to run as its GPU changes speed. Nothing inside cooks
while the output is unused.

## Accessibility

- **Flashing.** A strike moves the picture's light into the figure and out again over a third of a second, piling
  it into lines up to twice as bright and draining the hollows toward black. That counts as flashing, so a beat
  strikes the plate only through the standard flash gate, as does Idle Strike. Off never strikes, and only Swell moves
  the sand, smoothly, following the bands smoothed over a second. Calm (the default) strikes at most once a second, and
  Up to 3 per second is WCAG 2.3.1's limit.
- **No red guard.** The red flowers, whose reds sit near WCAG's saturated-red line, measured at most half a red flash a
  second over the clip's own at Calm, so the effect shows the picture's own colors.
- **No meaning in color.** The effect signals nothing by hue; the figure shows by brightness, bright lines and dark
  hollows, in the picture's own colors.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully on and off 8 times a second), a dance beat at 140 BPM whose bands
pulse as drums would, a song as raw audio, or no music (Idle Strike), and counted the flashes in the worst second by
WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 | 1.0 | 1.0 |
| People crossing a plaza | 0.5 | 1.5 | 1.0 | 0.5 |
| Red flowers against the sky | 1.0, red 1.0 | 1.5, red 1.0 | 1.5, red 1.0 | 1.0, red 1.0 |
| Koi in a black pond | 0.5, red 1.0 | 1.0, red 1.0 | 0.5, red 1.0 | 0.5, red 1.5 |
| A laughing face | 0.5 | 1.0 | 1.0 | 0.5 |
| Walkers with lanterns at night | 0 | 0 | 0 | 0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.5 | 1.0 | 1.0 |
| Flowers, 140 BPM | 1.0, red 1.0 | 1.5, red 1.5 | 2.5, red 1.5 | 1.0, red 1.0 |
| Koi, 140 BPM | 0.5, red 1.5 | 1.0, red 1.5 | 0.5, red 1.5 | 0.5, red 1.5 |
| Face, 140 BPM | 0.5 | 1.0 | 1.0 | 0.5 |
| Dancer, a song | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, a song | 1.0, red 1.0 | 1.0, red 1.0 | 1.5, red 1.5 | 1.0, red 1.0 |
| Koi, a song | 1.0, red 1.5 | 1.0, red 1.0 | 0.5, red 1.5 | 0.5, red 1.5 |
| Dancer, no music (Idle Strike) | 1.0 | 1.0 | 1.5 | 1.0 |
| Flowers, no music (Idle Strike) | 1.0, red 1.0 | 1.0, red 1.5 | 1.5, red 1.5 | 1.0, red 1.0 |
| Flowers, 140 BPM, Speed 2, Strike 1, Swell 1 | 1.0, red 1.0 | 1.5, red 1.5 | 2.5, red 1.5 | 1.0, red 1.0 |
| Flowers, 140 BPM, Settle 0.1, Strike 1 | 1.0, red 1.0 | 1.5, red 1.5 | 2.5, red 2.0 | 1.0, red 1.0 |
| Koi, 140 BPM, Speed 2, Strike 1, Settle 0.1 | 0.5, red 1.5 | 1.0, red 2.0 | 1.0, red 2.5 | 0.5, red 1.5 |

Every row keeps its setting's promise. Off adds nothing to the clip's own beyond the measurement's half-flash margin,
Calm adds at most one a second, and nothing passes WCAG's 3. The last three rows are far corners of the ranges: the
fastest sand, the hardest strike and the quickest settle. With Settle at its shortest, the figure forms and clears
within each strike, so the picture swings from itself to the figure and back, which at Up to 3 per second flashes as
often as that setting allows.

## Experimental

- Without Fosfora's feature bus, the bands its bass, melody and drums stand in for are a rough guess, so the figures
  follow the music more loosely.

## Credits and license

MIT. The shaders and operators are written for this library, including the sand as the picture's light with its mass
kept, the bands judged against their usual level as the plate's modes, the strikes through the flash gate and Idle
Strike.

- **The figures:** E. F. F. Chladni, *Entdeckungen über die Theorie des Klanges* (Leipzig, 1787), sand on a bowed
  plate gathering on its nodal lines.
- **The figures as simple modes summed:** C. Wheatstone, ["On the Figures Obtained by Strewing Sand on Vibrating
  Surfaces, Commonly Called Acoustic
  Figures"](https://jimclifford.ca/philosophical-transactions-ocr-1665-1869/articles/jstor-108009/) (Philosophical
  Transactions of the Royal Society 123, 1833), who wrote that "all the figures of vibrating surfaces are the resultants
  of very simple modes of vibration": two perpendicular modes in opposite phase give the square plate's figures,
  cos(n&pi;x) cos(m&pi;y) - cos(m&pi;x) cos(n&pi;y).
- **Carrying the light along the flow:** J. Stam, ["Stable Fluids"](https://doi.org/10.1145/311535.311548) (SIGGRAPH
  1999), the semi-Lagrangian step [Fluid](fluid.md) uses too.
- **The seven bands:** Fosfora's split (its `AUDIO-FEATURES.md`), measured from raw audio by the library's audio input
  (`lib/audio_callbacks.py`).
- **The same figures before this one:** Derivative's community tutorial ["Audioreactive particles with Chladni
  Cymatics"](https://derivative.ca/community-post/tutorial/audioreactive-particles-chladni-cymatics/67877), which draws
  particles into the figures. This effect moves the picture instead, and was written from Chladni's and Wheatstone's
  descriptions.
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Detail, Fluid, Motion Magnify, Paint, Particles, Pencil, Point
  Cloud and Video Vocoder.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (October 2026) found none on moving a picture or its light toward a plate's nodal
lines. The cymatics patents found are physical devices (a vibrated fluid projected as light, a plate of sand) or map
tones to colors of light.

**Not used:** moving the picture itself toward the lines (a warp, as [Motion Magnify](motion_magnify.md) moves it),
tried first beside the sand. It read as a liquid lens rather than sand.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
