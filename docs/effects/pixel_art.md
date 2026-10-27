# Pixel Art

![Two views of orange and white koi swimming in a black pond side by side, each named in the library's pixel font. On the left, INPUT, the clip. On the right, PIXEL ART, the same fish drawn in big square pixels and a dozen flat colors, orange, white and a few grays, their outlines crisp against the black water, which the louder passages fill with a faint checkerboard of dither; on the beat the picture jumps for a moment into bigger blocks and back](pixel_art.webp)

*The defaults on koi in a black pond, the clip on the left, with a song on input 2. On each beat the art jumps into
bigger blocks for a moment, at most once a second (Flashing at Calm), and loud passages dither the water.*

**New to pixel art?** Pixel art is a picture drawn one pixel at a time in a few colors, the way game consoles and home
computers of the 1980s and 1990s had to draw everything. It is still a style of its own in games and illustration.
Shrinking a photo and cutting its colors down doesn't make pixel art. Edges blur across two pixels, small features
smear away, flat areas break into speckles, and the few colors come out gray. A pixel artist picks a few colors that
matter and places each pixel so the shapes read.

This effect does that the way Timothy Gerstner and his colleagues described in 2012. Each pixel of the art covers a
small region of the picture, and the regions bend around the picture's features, so an eye, the line of a mouth or the
edge of a fin lands on whole art pixels instead of being smeared between two. The palette picks itself from the
picture. It starts as one color, the picture's average, and splits into more as it settles, until it has as many as you
ask for. The regions are shaped by the palette's colors and the palette by the regions, each refining the other. On
video it never stops. Each frame carries on from the last, so the art follows the picture as it moves and the palette
follows its colors as they change. The Palette's pixelate component and the Limit TOP's posterizing make the
shrunk-and-cut-down picture described above; this effect makes the art the paper describes.

**[Download pixel_art.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/pixel_art.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `pixel_art.tox` into your network. It shows TouchDesigner's sample movie of mist over a lake as pixel art.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. For about the first second the art
   shows each region's own color while the palette takes shape, then fades into the palette.
3. Wire music into input 2 (see Audio input). The beats then kick the art into bigger blocks, and loud passages dither
   it.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Subject Colors then
   spends more of the palette on near things, or inside the mask. Without it every part of the picture counts the same.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `pixel_art.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Pixel Art page holds, top to bottom, the art, the palette, the music, depth, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Pixel Size | 8 | How many of the picture's pixels across one pixel of the art is, 2 to 32. At 8 a 1280 x 720 picture becomes art 160 x 90 pixels big. |
| Colors | 12 | How many colors the palette has, 2 to 32. It picks them itself from the picture and keeps following it. |
| Dither | 0 | Mixes two colors in a checkerboard where an art pixel sits between them, 0 to 1. At 0 every pixel is one color, as in the paper. At 1 every in-between shade is dithered, as on old consoles. |
| Saturation | 1.1 | How colorful the palette is drawn, 0.5 to 2. At 1 the colors are as found. Pixel artists push them a little, and 1.1 is the paper's. |
| Hold Palette | Off | Keeps the palette as it is now. The art still follows the picture, in these colors only. |
| New Palette | | Starts the palette again. It picks its colors afresh from the picture over about a second, and the art fades into them. |
| Mosaic Kick | 0.75 | On each beat on input 2 the art jumps to bigger blocks for a moment, as the Super Nintendo's mosaic did, 0 to 1. At 0.75 the blocks are 4 art pixels across, at 1 five. As often as Flashing allows. |
| Swell | 0.5 | How much the music getting louder than usual dithers the art, 0 to 1, on top of Dither. It follows the loudness over a second. |
| Subject Colors | 0.75 | With a depth map or mask on input 3, how much of the palette goes to near things, or inside the mask, 0 to 1. At 1 far things get only the colors near ones chose. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away, in meters, counts as the far end of the depth. |
| Flashing | Calm | How often the beat may kick the art into its mosaic. Off never does. Calm does at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The looks

![Six views of a woman's face in profile against a deep blue background, each named in the library's pixel font. INPUT is the clip. PIXEL ART, the defaults, draws her in a dozen flat skin tones and blues, the eye, nostril and line of the lips kept crisp. 6 COLORS flattens her into a poster of a few browns against a few blues. 24 COLORS shades her face in many more steps. DITHER 1 draws every in-between shade as a checkerboard of two colors, as old consoles did. PIXEL SIZE 16 makes the art half as fine, in big chunky pixels](pixel_art_looks.webp)

*The defaults and four settings off them on the same face, each on its own, with no music.*

## How it works

The art's pixels sit on a grid, one for each square of Pixel Size x Pixel Size of the picture's pixels, and each one
is a **superpixel**, a region of the picture that belongs to it. Every frame, each of the picture's pixels joins the
nearest superpixel among those around it, nearest in color and in place together (SLIC, Achanta and his colleagues'
clustering). Gerstner and his colleagues measure the color to the palette color the superpixel shows, not to its
average, so the regions take the shapes the palette can draw. Each superpixel's center then moves to the middle of the
pixels that joined it, and 40% of the way toward its four neighbors', which keeps the regions in rows and columns like
the art's pixels. Its color is the average of its pixels, smoothed across neighbors of similar color (a bilateral
filter) so a soft gradient doesn't break into speckles.

The **palette** comes from deterministic annealing (Kenneth Rose's clustering). Each superpixel belongs to every palette
color a little, more to the nearer ones, and how sharply it prefers the nearest is set by a temperature. Each palette
color moves to the average of the superpixels that belong to it. It starts hot, as one color (the picture's average)
held as two slightly different copies. As the temperature falls, a color whose two copies drift apart has found two
groups in the picture, and splits in two, until the palette has Colors of them. Then it goes on cooling until each
superpixel belongs to one color, its nearest, and that is the color its art pixel shows. The paper runs this loop to
the end on one picture. Here it runs one step a frame and never stops, so on video the palette keeps following the
picture.

Four things keep video steady. A superpixel's color is eased over a fifth of a second where it changed only a little
(the picture's noise) and taken at once where it changed a lot (a cut, an edge going by), so nothing trails. An art
pixel keeps its color until another is clearly nearer, so a region between two colors doesn't flicker between them. A
palette color that no superpixel uses any more takes half of the most spread-out color. And while the palette takes
shape, the art shows each region's own color, then fades into the palette over half a second, so its splits never
show.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends beats and loudness. Drag `fosfora_signal.tox` (in
Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw audio** (an Audio File In or
Audio Device In CHOP) gives the beats and the loudness from the sound itself. **TouchDesigner's audioAnalysis** gives
beats from its kick or onset channels and loudness from its level.

On each beat the art jumps into blocks of Mosaic Kick's size for 0.15 seconds, each block showing its top-left art
pixel, as the Super Nintendo's mosaic did, as often as Flashing allows (once a second at Calm, so on a dance track every
other beat or so). Between beats, the loudness, smoothed over a second and judged against its usual level over the last
4 seconds, adds dither as the music swells (Swell), so loud passages get the checkerboards old consoles drew their
in-between shades with.

**Nothing wired:** the art, with no mosaic and no swell.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 2.3 ms on the GPU (95th percentile 2.7 ms) and 0.3 ms on the
CPU, the median of three runs with the Mac otherwise idle. About 0.9 ms of it is the superpixels' update, a compute
shader with one workgroup for each superpixel whose 64 invocations share its window and add their sums in shared
memory. The palette's sums for each color are another (one workgroup a color, 256 invocations). Everything else is a
few small passes on the art's grid and three at full size, which turn the picture into Lab colors, put each pixel into a
superpixel and draw the art. Pixel Size sets how many superpixels there are. At 2 (230,400 of them) a frame took 5.6 ms on the
GPU, at 32 (920) 1.6 ms. Colors costs little (32 colors: 2.0 ms). With raw audio on input 2, measuring it raises the
CPU time to about 0.7 ms. GPU times on this Mac wander from run to
run as its GPU changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** The mosaic changes the whole picture at once and back, which counts as flashing, so a beat kicks it
  only through the standard flash gate. Off never kicks, Calm (the default) kicks at most once a second, and Up to 3
  per second is WCAG 2.3.1's limit.
- **The art's own changes.** Few colors and flat regions turn small changes in the picture into whole art pixels
  changing color. The steadying described in How it works keeps that to the picture's own movement. With Flashing Off
  every clip measured within the clip's own flashes.
- **The palette takes shape out of sight.** The palette's splits each change large parts of the picture a few frames
  apart, which flashed while it took shape, so the art shows the regions' own colors until the palette is whole and
  then fades into it.
- **Reds kept clear of the line.** WCAG counts a color as saturated red, all or nothing, once red is 80% of it in
  linear light. A palette color sitting near that line, drifting across it as the palette followed the picture, turned
  every pixel it covers to saturated red and back at once, though nothing visible changed (on the red flowers a dark
  red-brown did this, in bursts of red flashes with Flashing Off). So each palette color keeps to one side of the line, at most 77%
  or at least 83%, and changes side only once its own share is well past it. A deep red stays deep red.
- **No meaning in color.** The effect signals nothing by hue; it shows the picture in its own colors.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, the loudness swinging 8 times a second), a dance beat at 140 BPM, a song as raw audio, or no
music, and counted the flashes in the worst second by WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 0.5 | 1.0 | 1.5 | 1.0 |
| People crossing a plaza | 0.5 | 0.5 | 1.0 | 0.5 |
| Red flowers against the sky | 1.0, red 1.5 | 1.5, red 1.5 | 3.0, red 3.0 | 1.0, red 1.0 |
| Koi in a black pond | 0.5, red 1.0 | 1.0, red 1.5 | 2.0, red 3.0 | 0.5, red 1.5 |
| A laughing face | 0.5 | 0.5 | 0.5 | 0.5 |
| Walkers with lanterns at night | 0 | 0 | 0 | 0 |
| Flowers, a dance beat (140 BPM) | 1.0, red 1.0 | 1.5, red 1.5 | 2.5, red 2.5 | 1.0, red 1.0 |
| Koi, 140 BPM | 0.5, red 1.0 | 1.0, red 1.5 | 2.0, red 3.0 | 0.5, red 1.5 |
| Face, 140 BPM | 0.5 | 0.5 | 0.5 | 0.5 |
| Dancer, a song | 1.0 | 1.0 | 1.5 | 1.0 |
| Flowers, a song | 1.0, red 1.0 | 1.5, red 2.0 | 2.5, red 3.0 | 1.0, red 1.0 |
| Koi, a song | 0.5, red 1.0 | 1.0, red 1.5 | 1.5, red 2.5 | 0.5, red 1.5 |
| Dancer, no music | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, no music | 1.0, red 1.0 | 0.5, red 1.0 | 0.5, red 1.0 | 1.0, red 1.0 |
| Flowers, Mosaic Kick 1 | 1.0, red 1.0 | 1.5, red 1.5 | 3.0, red 3.0 | 1.0, red 1.0 |
| Plaza, Mosaic Kick 1 | 0.5 | 1.0 | 2.0 | 0.5 |
| Flowers, Dither 1, Swell 1 | 1.0, red 1.0 | | | 1.0, red 1.0 |
| Flowers, 24 colors | 1.0, red 1.0 | | | 1.0, red 1.0 |
| Flowers, Pixel Size 4 | 1.0, red 1.0 | | | 1.0, red 1.0 |

Every row keeps its setting's promise. Off adds nothing to the clip's own beyond the measurement's half-flash margin,
Calm adds at most one a second, and nothing passes WCAG's 3. Up to 3 per second reaches it on the red flowers and the
koi, where the mosaic kicks as often as that setting allows and every kick swings their reds across WCAG's line and
back. The last five rows are corners of the ranges, spot-checked. They are the biggest mosaic at every setting and, with
Flashing Off, the most dither, the most colors in common use and the finest pixels. Mosaic Kick stops at blocks of 5 art
pixels, since blocks of 7 took the flowers to 3.5 red flashes a second at Up to 3 per second.

## Credits and license

MIT. The shaders and operators are written for this library, including running the paper's loop one step a frame on
video, the steadying for video, the palette's fade-in, the red line kept clear, Dither between the two nearest colors,
the mosaic on the beat through the flash gate and the swell of dither with the loudness.

- **The method:** T. Gerstner, D. DeCarlo, M. Alexa, A. Finkelstein, Y. Gingold and A. Nealen, ["Pixelated Image
  Abstraction"](https://gfx.cs.princeton.edu/pubs/Gerstner_2012_PIA/) (NPAR 2012): superpixels on the art's grid by a
  SLIC whose color distance is to the palette, Laplacian smoothing of their centers, a bilateral filter on their colors,
  the palette by mass-constrained deterministic annealing, the saturation step and the importance map (Subject Colors).
- **SLIC superpixels:** R. Achanta, A. Shaji, K. Smith, A. Lucchi, P. Fua and S. Süsstrunk, ["SLIC Superpixels
  Compared to State-of-the-Art Superpixel Methods"](https://doi.org/10.1109/TPAMI.2012.120) (TPAMI 34(11), 2012; EPFL
  technical report 149300, 2010).
- **Deterministic annealing:** K. Rose, ["Deterministic annealing for clustering, compression, classification,
  regression, and related optimization problems"](https://doi.org/10.1109/5.726788) (Proceedings of the IEEE 86(11),
  1998), after K. Rose, E. Gurewitz and G. Fox (Physical Review Letters 65, 1990).
- **The bilateral filter:** C. Tomasi and R. Manduchi, ["Bilateral Filtering for Gray and Color
  Images"](https://doi.org/10.1109/ICCV.1998.710815) (ICCV 1998).
- **The sums in shared memory:** a parallel reduction, as in W. D. Hillis and G. L. Steele, ["Data parallel
  algorithms"](https://doi.org/10.1145/7902.7903) (CACM 29(12), 1986).
- **Colors:** CIE L\*a\*b\* (CIE 1976) from sRGB (IEC 61966-2-1) with the D65 white.
- **Dither:** B. E. Bayer, "An optimum method for two-level rendition of continuous-tone pictures" (IEEE International
  Conference on Communications, 1973), its 4 x 4 matrix.
- **The mosaic:** the Super Nintendo's mosaic effect (Nintendo, 1990), each block showing its top-left pixel.
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Chladni Sand, Detail, Fluid, Motion Magnify, Paint, Particles,
  Pencil, Point Cloud and Video Vocoder.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (October 2026) found none on SLIC itself, on Gerstner and his colleagues' method or
on abstracting a picture into pixel art with superpixels and an adaptive palette. EPFL's patent on scale-adaptive
superpixels (US 10,229,337) has lapsed, and deterministic annealing dates from 1990.

**Not used:** optimizing the small picture against a perceptual measure of how like the input it looks, once it is
scaled back up (A. C. Öztireli and M. Gross, ["Perceptually Based Downscaling of
Images"](https://doi.org/10.1145/2766891), SIGGRAPH 2015). ETH Zurich holds an active US patent on it (US 10,325,346).
Nor the library's red guard, which keeps every red short of WCAG's line. Tried first, it turned the red flowers orange.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
