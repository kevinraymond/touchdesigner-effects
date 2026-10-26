# Pencil

![Pencil at its defaults on a close-up of a laughing woman's face, drawn in graphite on white paper. Quick dark strokes outline her eyes, her smile and the creases around them, running a little past the corners where two lines meet, and her skin is left mostly white with a few light strokes. The dark background behind her is filled with an even gray grain of short pencil strokes laid every way, and now and then, on the beat, the shading and the lines are redrawn](pencil.webp)

*The defaults (Sketch, Graphite) on a portrait, with a song on input 2: lines along the face, its tones in pencil
strokes, and a redraw on each beat.*

**New to pencil drawing?** A pencil drawing is two things at once. Lines give the shapes: quick, straight strokes that
run on past the corners and cross where two edges meet, because a hand moving fast overshoots. Tone gives the light
and shade: strokes laid over each other until an area is as dark as it should be, with most of the paper left white.
Cewu Lu, Li Xu and Jiaya Jia turned both into an algorithm in 2012, in a paper that won NPAR's best paper award, and
Emil Praun and colleagues had already shown in 2001 how hatching can be drawn in real time from a set of stroke
textures.

This effect draws live video both ways. It classifies the picture's edges into eight directions of short line
segments and spreads each direction back along its own segment, so the lines look drawn rather than traced, and it
matches the picture's tones to those of real pencil drawings (mostly paper, a band of mild strokes, a few dark
accents) before drawing them with pencil strokes. Sketch shades them in soft graphite, short strokes laid every way,
as the paper does. Hatching lays long parallel strokes that follow the picture's edges and cross only in the darks, as
an illustrator hatches. The paper
names video as its limit, since its strokes stay put while the picture moves under them; here the strokes travel with
what moves. On the beats the drawing is redrawn, as the next drawing of a hand-drawn animation would be. I found no
TouchDesigner version of this method; the usual quick pencil sketch is a color dodge of a blurred, inverted copy of
the picture, which gives soft outlines but no strokes and no tone.

**[Download pencil.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/pencil.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `pencil.tox` into your network. It shows TouchDesigner's sample movie of a river running over rocks, drawn in
   pencil.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Faces, figures and pictures with clear
   shapes draw best; a picture with large dark areas comes out with large areas of shading, since a pencil drawing has
   few true darks.
3. Optional: wire audio or beat channels into input 2 (see Audio input). The beats then redraw the drawing, and
   loudness presses the pencil harder.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Depth Fade then draws
   far things lighter, or leaves what lies outside the mask as paper. Nothing fades without it.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `pencil.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Pencil page, top to bottom, in four groups: the style, the lines, the tone and strokes, depth and the music, then
the window.

| Parameter | Default | What it does |
|---|---|---|
| Style | Sketch | Sketch draws lines along the edges and the tones in soft graphite shading, short strokes laid every way, as Lu, Xu and Jia draw them. Hatching draws the tones in long parallel strokes that follow the edges, crossing only in the darks. Lines draws the lines alone. See [The styles](#the-styles). |
| Colors | Graphite | Graphite on white paper, Colored Pencil (the picture's own colors, the drawing as their brightness), Blue Pencil (an animator's blue), or Light on Dark: white pencil on black paper, drawing where the picture is light. |
| Lines | 0.5 | How dark the lines along the edges are, 0 to 1. At 1, every strong edge is drawn black. |
| Line Length | 1 | How far the lines run past their edges, 0.5 to 2. At 1 a segment is 1/30 of the picture's height, the paper's choice, so strokes cross at corners as a quick hand draws them; longer looks looser. |
| Shading | 0.5 | How dark the drawing's tones are, 0 to 1: 0 mostly paper, 0.5 as the paper's pencil drawings, 1 darker, with more dark accents. The tones follow the picture over a second. Grayed out for Lines. |
| Stroke Size | 1 | How big the pencil strokes are, 0.5 to 2. At 1 a hatching stroke is 45 to 75 pixels long and Sketch's 25 to 45, about 1.5 wide, at 720 high, and they scale with the picture. Grayed out for Lines. |
| Follow Movement | 1 | How much the pencil strokes travel with what moves in the picture, 0 to 1. At 0 they stay on the paper while the picture slides under them, and the motion isn't measured, which saves about a quarter of the cost. Grayed out for Lines. See [Following movement](#following-movement). |
| Texture | 0.5 | How much the paper's grain shows in the graphite, 0 to 1. The paper stays put while the picture moves, as paper would. |
| Depth Fade | 0.5 | With a depth map or mask on input 3: how much lighter far things (or what lies outside the mask) are drawn, 0 to 1. At 1 the farthest are left as paper. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Beat Kick | 0.5 | How much each beat of input 2 redraws the drawing, 0 to 1: the line segments turn by up to 11 degrees and the pencil strokes move by up to 24 pixels at 1, as the next drawing of a hand-drawn animation would. |
| Loudness | 0.5 | How much harder the pencil presses when the music is loud, and lighter when quiet, 0 to 1, eased over half a second. |
| Song Moments | On | With Fosfora's signal on input 2, a build draws longer, looser lines as it rises, and a drop draws them twice as long for Length seconds. |
| Length | 1 | How long a drop draws long lines, in seconds. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The styles

![Six views of orange and white koi in a black pond, each named in the library's pixel font. INPUT is the clip as it is. SKETCH draws the fish in quick graphite lines, left almost white, and fills the dark water with an even gray grain of short pencil strokes laid every way. HATCHING fills the water instead with long parallel strokes that run along the fish and cross where it is darkest. LINES draws only the fish's outlines and markings on white paper. COLORED PENCIL keeps the orange fish and draws the water in gray graphite. LIGHT ON DARK draws the fish in white pencil on black paper](pencil_styles.webp)

*Each style and two of the colorings on the koi, at the defaults otherwise, with the song on input 2.*

**Sketch** is Lu, Xu and Jia's drawing: the lines times the tone, the tone drawn with a pencil pattern whose strokes
have no one direction, laid over itself as often as each area's tone asks. It reads as soft graphite shading: dark
areas fill with a dense grain of short strokes laid every way, light ones keep a few, and most of the paper stays
white. There are no lines to follow in it; the lines along the edges carry the shapes.

**Hatching** draws the same tones with long, evenly spaced parallel strokes that follow the picture's edges, wrapping
round a face or running along the smoke, as Praun and colleagues' tonal art maps do on 3D surfaces. The tone is drawn
in parallel lines, closer together as it darkens, until the darks, which add strokes across them. Where the picture has no clear
direction (a smooth sky, a blurred background), the hatching runs from lower left to upper right, as a right-handed
artist's does.

**Lines** leaves the tone out: the lines alone, like a quick contour sketch.

**Colored Pencil** keeps the picture's colors and draws its brightness, as the paper does for color (the drawing as
the brightness in YUV, the picture's own color around it). **Blue Pencil** draws in the light blue animators rough in.
**Light on Dark** draws white pencil on black paper, its marks where the picture is light, which suits a dark stage.

## How it works

**The lines.** `edges` takes the gradient of the picture's brightness (forward differences, as the paper does) and
eases it over a fifth of a second. `classify` sums that gradient along eight short line segments through each pixel,
22.5 degrees apart, each 1/30 of the picture's height long at Line Length 1, and gives the pixel to the direction whose
segment gathers the most. A pixel is decided by the gradient around it along a line, not by its own, so noise and
texture don't decide it. `shape` spreads each direction's pixels back along that direction's segment. Edge pixels that
line up join into one stroke, a gap in an edge closes, and a stroke runs on past where its edge ends, so two strokes
cross at a corner; the middle of a long line, reached from both sides, comes out darker than its ends. Each segment is
read at 11 points whatever its length, so a longer stroke costs no more.

**The tone.** Lu, Xu and Jia found that pencil drawings share a pattern of tones that photographs don't: a peak of
white paper, a broad, even band of mild strokes, and a few dark accents. They model it as a Laplacian at white, a
uniform band and a Gaussian, weighted 52 : 37 : 11 (bright : mild : dark) in their Table 1, and match each picture's
histogram to it. `histogram` counts the picture's levels from a 64 x 36 grid of a small mipmap level, each sample
spread over four levels, and caps each level at three times an even share, as contrast-limited histogram equalization
does: a picture whose tones crowd into a narrow band, a dark pond or a gray square, would otherwise be stretched over
every tone, and its ripples and noise with it. `tone` turns the result into a table of 256 levels, each the tone the
model gives the same share, eased over a second so a bright thing walking in doesn't swing the whole drawing at once.
Shading moves between three weightings the paper shows, from 76 : 22 : 2 (mostly paper) through Table 1 to
42 : 29 : 29 (more dark accents).

**The pencil strokes.** `strokes` draws them once, when the effect loads, as a texture that repeats every 512 pixels.
Hatching's are six levels, as in Praun and colleagues' tonal art maps: each holds every stroke of the lighter ones and
adds more, long straight strokes 45 to 75 pixels long until the rows are full (levels 1 to 4), then strokes across
them (5 and 6). Sketch's is one tonal pattern of short, light strokes 25 to 45 pixels long in three families, along the
rows and along both diagonals, each stroke turned at random by up to 17 degrees. A stroke is a slightly bowed line
tapering to its ends, laid with an uneven pressure, in rows offset along themselves so their ends don't line up.
Nothing is loaded from a file, so the strokes travel inside the `.tox`.

**Sketch** draws the tone as the paper does: its pencil pattern H, turned so no family of strokes lies square to the
frame, drawn over itself beta times, since pencil strokes over pencil strokes multiply their darkness, so that H^beta matches
the tone J. The paper solves for a smooth beta by least squares; here beta = ln J / ln H_blur, with H blurred (a
mipmap level of the pattern), which needs no solver and keeps the pattern's strokes. The pattern has to be about as dark
as the darkest tone wanted: a light one needed beta near 4 for the darks, which turned the strokes black and the gaps
white.

**Hatching** reads the two levels around the tone wanted and mixes between them, each level's tone read from its own
mipmap. The strokes turn along the picture's edges, from the library's `structure_tensor()` (shared with Paint and
Reaction-Diffusion) on the picture at half size, smoothed over 6 pixels and eased over half a second. Turning a
texture pixel by pixel would tear it wherever the direction changes, so the strokes are read at eight directions, each
one turned as a whole, and each pixel mixes the two around its own direction.

**Paper and color.** Graphite catches on the paper's tooth, so each mark is thinned where the paper dips (gradient
noise shared with Paint, fixed to the frame). `draw` multiplies the lines by the tone and colors the result.

## Following movement

Lu, Xu and Jia name video as their method's limit: the pencil pattern stays put while the picture moves under it, so a
moving face slides through a fixed texture, a look called the shower door. With Follow Movement on, the strokes travel
with what moves. The library's optical flow (as in Datamosh and Fluid) measures the picture's motion, averaged over
blocks of about 16 pixels so that only motion that holds together over an area counts, and `drift` carries two offsets
along with it, frame by frame: each pixel takes the offset from where its content came from, plus this frame's motion.
Each offset starts again from nothing every second, half a second apart, and `draw` fades to the younger one before
the older has stretched far: the advected textures of Max and Becker (1995) and Neyret (2003). Where nothing moves both
stay at nothing and the strokes stay put.

On a picture panning steadily sideways, the offsets matched the pan within a few pixels, and the drawing lined up with
itself 0.3 s later about twice as well as with the strokes held still on a slow pan (a twentieth of the picture a
second), and a quarter better on a fast one (a fifth). On noisy motion, drifting smoke or rippling
water, the flow is less sure of itself, and the strokes there can curve a little, like marbled paper; Follow Movement
lower holds them closer to the paper.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it into input 2. Its beats
redraw the drawing and its loudness presses the pencil. With Song Moments on, a build lengthens the lines by up to half
as it rises, and a drop draws them twice as long, up in 0.3 s, held for Length and back over 0.8 s, so the drawing turns
loose and scribbly. Fosfora's drop detection is experimental.

**Any input** brings the redraws and the pressure. On each beat the line segments turn by up to 11 degrees (half the
step between two directions) and the pencil strokes jump by up to 24 pixels, at Beat Kick 1, so the lines cross their
corners at new angles and the shading is drawn again, as in the next drawing of a hand-drawn animation. A redraw moves
only fine strokes, so every area keeps its tone (see Accessibility). Louder music presses the lines up to half again as
dark at Loudness 1, and darkens the tone a little, eased over half a second; quiet passages draw lighter. Raw audio (an
Audio File In or Audio Device In CHOP) gives beats from a kick detector and a beat clock. Once the kicks keep to a
tempo, the clock locks to them, beats then come on the beat even when a kick is missed, and a kick between beats is
left out. It stops 8 beats after the kicks do, and while it isn't locked every kick is a beat. TouchDesigner's
audioAnalysis gives beats from its kick or onset channels.

**Nothing wired:** no redraws, and the pencil keeps its pressure.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters (Sketch, Follow Movement 1). Each frame took 5.3 ms on the GPU (95th percentile
6.4 ms) and 0.61 ms on the CPU, the median of three runs. The lines cost most of it, about 2.1 ms for `classify` and
`shape` together; the optical flow behind Follow Movement about 1.5 ms; the drawing about 1.2 ms; the tone 0.3 ms.
Hatching took 6.0 ms (its drawing reads more of the strokes), and Follow Movement 0 took 4.0 ms. GPU times on this Mac
wander from run to run as its GPU changes speed, by a fifth or more: an earlier build, nearly the same, measured 6.5 to
6.6 ms in one series and 5.7 to 6.1 in another. The pencil strokes are drawn once, when the effect loads. Nothing inside cooks while the output is unused.

## Accessibility

- **No flashes of its own.** The drawing adds no light the picture didn't have, and a beat's redraw only moves fine
  strokes, which keeps each area's tone: on the dancer, the redraws, the drops' long lines and the pressure measured
  the same as no beat at all. Hatching's strokes are coarser, and redrawn 8 times a second under the test beat they
  added half a flash a second, within the count's margin (none at a dance tempo). So Pencil has no Flashing setting.
- **The lines are eased.** They multiply small changes in the picture's edges many times over (a faint edge in drifting
  smoke comes out a dark line), so a video's noise, followed at once, flickered the lines in the smoke between dark and
  light: half a flash a second over the clip's own on the dancer, with no beat at all. The edges are now followed over
  a fifth of a second.
- **The tones are capped.** Matched to a pencil drawing's tones over the whole picture, a picture whose tones crowd
  into a narrow band is stretched over every tone, its flicker with it; capping the histogram keeps that within
  bounds (the koi's worst cell went from 4 flashes a second to 3), and the tones follow the picture over a second.
- **Darks drawn as mid tones.** A pencil drawing has few true darks, so the koi's near-black pond is drawn mid-gray,
  and ripples too dark to count as flashes in the clip move the drawing enough to count. The plaza's long shadows
  become dense cross-hatching on white, so a walker's shadow sweeps whole cells from paper to graphite. Both are the
  clip's own changes, drawn with a drawing's contrast; they stay well within WCAG's three a second.
- **No meaning in color.** The effect signals nothing by hue. Its colors are graphite or blue pencil on white, white on
  black, or the picture's own, and all of them read by brightness.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far busier than music (8
beats, 2 bars and 1 drop a second) and counted the flashes in the worst second by WCAG's area rule, and WCAG's red
flashes separately:

| Clip and settings | Pencil | The clip alone |
|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.0 |
| Dancer, no beat | 1.0 | 1.0 |
| People crossing a plaza | 1.0 | 0.5 |
| Red flowers against the sky | 1.0 | 1.0, red 1.0 |
| Koi in a black pond | 1.5 | 0.5, red 1.5 |
| Dancer, Hatching | 1.5 | 1.0 |
| Dancer, Hatching, 140 BPM | 1.0 | 1.0 |
| Dancer, Hatching, no beat | 1.0 | 1.0 |
| Flowers, Hatching | 1.0 | 1.0, red 1.0 |
| Plaza, Hatching | 1.0 | 0.5 |
| Dancer, Lines | 1.0 | 1.0 |
| Dancer, Light on Dark | 1.0 | 1.0 |
| Flowers, Colored Pencil | 1.0, red 1.0 | 1.0, red 1.0 |
| Dancer, Beat Kick 1, Loudness 1, Line Length 2 | 1.0 | 1.0 |
| Dancer, Follow Movement 0 | 1.0 | 1.0 |

No row adds more to the clip's own than the half flash a second the count allows for measuring noise, taking the
worse of the general and the red flashes: the plaza's 1.0 against 0.5 (in either style); the koi's 1.5, all general flashes, against the
clip's 1.5 red; and Hatching's 1.5 under the test's 8 beats a second, which comes from redrawing its coarser strokes 8
times a second (1.0 at Beat Kick 0, and at 140 BPM). Nothing comes near WCAG's 3. Red flashes: Graphite, Blue Pencil
and Light on Dark make none, so the flowers' and the koi's own red flashes are gone; Colored Pencil keeps the
flowers' (1.0).

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It takes a few beats
  to lock and can still add or miss beats where the kicks don't keep the beat. Fosfora or audioAnalysis give steadier
  beats.

## Credits and license

MIT. The shaders and operators are written for this library from the papers below, including the pencil strokes drawn
by a shader, the eight directions read whole and mixed, the easing of the edges and the tones, the redraw on the beat
and the depth fade.

- **The lines, the tone model and the pencil texture:** C. Lu, L. Xu and J. Jia, ["Combining Sketch and Tone for Pencil
  Drawing Production"](https://www.cse.cuhk.edu.hk/~leojia/projects/pencilsketch/pencil_drawing.htm) (NPAR 2012,
  doi:10.2312/PE/NPAR/NPAR12/065-073), written from the paper. Three changes: the pattern's density comes from a closed
  form, beta = ln J / ln H_blur, where the paper solves a smoothed least squares; the eight directions span half a turn,
  since a line has no sign; and the histogram is capped. Its Table 1 lists the weights 11 : 37 : 52, which its Figures
  9 and 11 show as dark : mild : bright; each layer is normalized as a distribution here, so a weight is its layer's
  share of the pixels, as the paper estimates them. The pencil pattern is drawn by a shader rather than taken from a
  scan of real strokes, as the paper's were.
- **Hatching:** tonal art maps after E. Praun, H. Hoppe, M. Webb and A. Finkelstein, ["Real-Time
  Hatching"](https://doi.org/10.1145/383259.383328) (SIGGRAPH 2001): nested levels of strokes, the two around each tone
  mixed. Here they turn along the picture's edges rather than a surface's curvature.
- **The capped histogram:** as contrast-limited histogram equalization caps its histogram, S. M. Pizer et al.,
  "Adaptive Histogram Equalization and Its Variations" (Computer Vision, Graphics, and Image Processing 39, 1987), and
  K. Zuiderveld, "Contrast Limited Adaptive Histogram Equalization" (Graphics Gems IV, 1994), here over the whole
  picture. erf by M. Abramowitz and I. Stegun's Handbook of Mathematical Functions, 7.1.26.
- **Strokes that travel with the picture:** advected textures, after N. Max and B. Becker, "Flow Visualization Using
  Moving Textures" (ICASE/LaRC Symposium on Visualizing Time-Varying Data, 1995), and F. Neyret, "Advected Textures"
  (Symposium on Computer Animation, SCA 2003). The motion is the library's Lucas-Kanade optical flow,
  written from B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to Stereo
  Vision" (1981), shared with [Datamosh](datamosh.md), [Fluid](fluid.md) and [VHS + CRT](vhs_crt.md).
- **The structure tensor** as J. E. Kyprianidis, H. Kang and J. Döllner use it, ["Image and Video Abstraction by
  Anisotropic Kuwahara Filtering"](https://doi.org/10.1111/j.1467-8659.2009.01574.x) (Pacific Graphics 2009), and J.
  E. Kyprianidis and J. Döllner (NPAR 2011), with the derivative filter of B. Jähne, H. Scharr and S. Körkel (1999):
  the library's `structure_tensor()`, shared with [Paint](paint.md) and [Reaction-Diffusion](reaction_diffusion.md).
- **The paper's grain:** gradient noise after K. Perlin, "Improving Noise" (SIGGRAPH 2002), shared with Paint
  (`lib/glsl/paper.glsl`). **Strokes** fall where Chris Wellons' lowbias32 integer hash says
  ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain).
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Fluid, Paint, Particles and Point Cloud.
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump in the low band's
  loudness, and the beat clock takes its tempo from the gaps between kicks, each gap voting for the beat lengths it is
  a whole multiple of. That is inter-onset-interval tempo induction, the idea behind S. Dixon's "Automatic Extraction
  of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed, not copied, and
  written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
