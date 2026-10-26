# Paint

![Paint on a close-up of a laughing woman's face, the middle of the picture at full size. Her skin has turned into flat patches of warm color that curve around her cheeks and nose, the wrinkles at her eyes are drawn as short dark ink strokes, and a faint canvas weave shows through. Now and then, on the beat, a band of broader, looser strokes slides across her face and the painting tightens again behind it](paint.webp)

*The defaults, Oil, on a portrait, the middle of the picture at 1:1: strokes that follow the face, ink lines in the
wrinkles, and on the beats a band of broader strokes sweeping across.*

**New to Kuwahara painting?** The Kuwahara filter turns a photo into something like a painting. Around each pixel it
looks at a few neighborhoods and takes the average color of the most even one. Busy texture, such as skin pores, grass
or noise, flattens into patches of color, while the edges between patches stay sharp, because the neighborhood that
straddles an edge is never the most even. The anisotropic version, from Kyprianidis, Kang and Döllner (2009),
stretches the neighborhoods along the edges in the picture, so the patches become strokes that follow the shapes: a
cheek is painted around its curve and grass along its blades.

This effect paints live video that way, from the papers, with their polynomial weights (2010), so nothing has to be
precomputed. It finds the direction of the edges at every pixel, paints with an ellipse turned along them, and draws
ink lines along the edges with a flow-based difference of Gaussians (XDoG, 2012). Three styles share the painting: Oil
on canvas, Watercolor washed onto paper with darker edges and pooling pigment (after Bousseau et al., 2006), and Ink,
two tones like a woodcut. A depth map or mask on input 3 paints near things finely and far things broadly, and on each
beat a broad stroke sweeps across the picture. The free Kuwahara filters for TouchDesigner are a basic one (MIT) and
an unfinished anisotropic port under the GPL, which an MIT project can't take in; this one is MIT, runs on any GPU
TouchDesigner does, Macs included, and costs the same at any brush size.

**[Download paint.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/paint.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `paint.tox` into your network. It shows TouchDesigner's sample movie of a river running over rocks, painted.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Faces, flowers, water and landscapes
   paint best; a dark, hazy picture flattens into soft paint with little to stroke.
3. Optional: wire audio or beat channels into input 2 (see Audio input). Each beat then sweeps a band of broad strokes
   across the picture.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Near things, or what is
   inside the mask, are then painted finely and the rest broadly. Without it, the brush is the same everywhere.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `paint.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Paint page, top to bottom, in four groups: the painting, the lines, input 3 and the music.

| Parameter | Default | What it does |
|---|---|---|
| Style | Oil | Oil paints flat strokes on canvas, with ink lines along the edges. Watercolor paints broader washes on paper, their edges darker and their pigment pooling unevenly. Ink turns the painting into two tones, ink on paper. See [The styles](#the-styles). |
| Brush | 12 | The strokes' size: their radius in pixels at 720 high, 2 to 24 (it scales with the picture). Strokes stretch up to twice that along a clear edge and shrink to half across it. Watercolor paints 1.5 times broader. The cost stays the same at any size. |
| Sharpness | 8 | How crisply neighboring strokes meet, 2 to 12: higher keeps regions flatter and their borders harder, lower blends them more softly (the papers' q). |
| Stretch | 1 | How far strokes stretch along the edges, 0.25 to 4. At 1, as in the papers, up to twice Brush along a clear edge and half across it. Higher, longer and thinner. |
| Passes | 1 | Paints over the painting again, up to 3 times. Each pass flattens the regions further and costs as much as the first. |
| Half Size | Off | Paints at half the picture's size, then brings it back up along the picture's edges: the painting costs about half as much, and its strokes are softer. |
| Texture | 0.5 | The surface, 0 to 1: a canvas weave under Oil, paper grain and pooling pigment under Watercolor, paper under Ink. It stays put while the picture moves over it, as paper would. |
| Lines | 0.5 | How dark the ink lines along the edges are, 0 to 1 (Oil and Watercolor). Grayed out for Ink. |
| Line Width | 1 | How wide the ink lines are, in pixels at 720 high, 0.5 to 3 (Ink's lines too). Wider lines also leave out finer detail. |
| Ink Level | 0.5 | Ink only: how much of the picture fills with ink, 0 to 1. At 0.5, everything darker than the picture's average brightness does, so a dark picture and a bright one both come out in two tones. |
| Depth Brush | 0.5 | With a depth map or mask on input 3: how much finer strokes are near (or inside) and broader far (or outside), 0 to 1. At 1 the nearest strokes are half Brush and the farthest twice. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer: depth estimators (Depth Anything) and masks. Distance 0-1: the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters: the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Beat Kick | 0.5 | How broad the stroke is that sweeps across the picture on each beat of input 2, 0 to 1 (Oil and Watercolor): in its middle the brush is up to 3 times its size at 1, and twice at the default. Grayed out for Ink (see [Accessibility](#accessibility)). |
| Loudness | 0.5 | How much louder music broadens the strokes, and quiet passages refine them, 0 to 1. At 1 the brush runs from 0.7 to 1.4 times its size, eased over half a second. |
| Song Moments | On | With Fosfora's signal on input 2, a build broadens the strokes as it rises, and a drop paints in broad strokes for Length seconds. |
| Length | 1 | How long a drop paints in broad strokes, in seconds (0.2 to 3). Grayed out with Song Moments off. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The styles

![Four views of a field of tall red flowers against a sunny sky, each named in the library's pixel font. INPUT is the clip as it is. OIL paints the flowers as flat orange strokes along their petals, with thin dark lines at their edges, and the clouds as soft patches. WATERCOLOR washes the same scene lighter onto grainy paper: the flowers outlined in darker pigment, the sky blotched where the paint pooled, the colors a little wobbly at their edges. INK turns it into two tones: the flowers and the field below them solid black with paper-white highlights, against a blank paper sky](paint_styles.webp)

*Each style on the flowers at the defaults otherwise, with the song on input 2.*

**Oil** is the painting as the filter makes it: flat strokes along the edges, ink lines on the dark side of each
edge, and a plain canvas weave under it all that darkens and lightens the paint a little along its threads.

**Watercolor** paints 1.5 times broader, since a wash covers more than a stroke, and lightens the colors, as a
transparent wash lets the paper through. Then it follows Bousseau et al.: the painting wobbles a pixel or two along
the paper's grain, its edges darken where the pigment collects, and three layers change the pigment's density, slow
blotches where the water pooled, a fine dispersion of pigment, and the paper's grain. The paper and pigment are drawn
with noise and stay put while the picture moves over them, as real paper would.

**Ink** thresholds the painting's brightness, sharpened along the edges (XDoG), into ink and paper: the darker half of
the picture (Ink Level) fills with ink and the edges sharpen into lines, like a woodcut or a linocut. It thresholds
against the picture's own average brightness, so a dark picture doesn't sink into ink.

## How it works

**The direction of the edges.** `tensor` measures how the color changes at every pixel, in each of R, G and B, with
the rotationally symmetric derivative filter of Jähne, Scharr and Körkel, and sums the three gradients' outer
products into the structure tensor. `tensor_h` and `tensor_v` blur it by a Gaussian of 2 pixels (at 720 high), which
averages out noise without canceling the two opposite gradients either side of a thin line. `flow` reads two things
out of it at every pixel: the direction along the edges (its minor eigenvector) and how clear that direction is, the
anisotropy, 0 where nothing has a direction and 1 along a clean edge. This part is `structure_tensor()` in the
library, where Reaction-diffusion and Pencil will share it.

**The painting.** Around each pixel `kuwahara1` lays an ellipse along the flow, up to twice Brush long and half as
wide where the anisotropy is high and round where it is low. It divides the ellipse into 8 overlapping sectors with
the 2010 paper's polynomial weights and a Gaussian falloff, finds each sector's mean color and how much the colors
vary in it, and gives the pixel the mean of the most even sectors, each weighted by 1 / (1 + variation^Sharpness). The
papers read every pixel of the ellipse, whose cost grows with its area (14 ms at Brush 6 and over 70 ms at Brush 10
with two passes, measured). This one reads a grid turned with the ellipse, 4 samples along a radius, each from the
mipmap level that averages the pixels between samples, so it reads about 50 samples a pixel at any brush size. Each
sample is read with the one opposite it, since turning a point half a circle turns each sector into the opposite one,
so one set of weights serves both: a third cheaper, with exactly the same picture. `kuwahara2` and `kuwahara3` are
further passes, and a Switch picks the last one asked for, so the others don't cook.

**The lines.** `dog` blurs the painting's brightness by two Gaussians, 1 and 1.6 times Line Width, straight across the
edges, and `lic` smooths both along the edges (a line integral convolution, a Gaussian of 3 pixels), so broken bits of
an edge join into one line. Their difference dips below zero on the dark side of every edge, and `paint` darkens the
painting there by XDoG's soft threshold. Ink thresholds the sharpened brightness instead, 21 times the narrow blur
less 20 times the wide one.

**The brush's size.** `brush_scale` holds a size for every pixel, at a quarter of the picture's size: from input 3,
2^(Depth Brush x (1 - 2 x nearness)), so halfway, and nothing on input 3, keep Brush; times the beat's sweep. `swell`
multiplies the whole brush by the loudness, a build and a drop.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it into input 2. Its beats
sweep, and louder music broadens the strokes. With Song Moments on, two more things happen.

- **Builds** broaden the strokes as they rise, up to 1.5 times at the peak.
- **Drops** paint in strokes twice as broad for Length seconds, rising in 0.3 s and settling over 0.8 s. Fosfora's drop
  detection is experimental.

**Any input** brings the sweeps on its beats and the strokes broadening with loudness. On each beat a broad stroke
sweeps across the picture in 0.35 s, a band about a quarter of the picture's height across: where it passes, the
painting goes loose, the brush up to twice its size at the default Beat Kick, and then tightens again. Each beat's
band comes from another direction, turning by the golden angle. Raw audio (an Audio File In or Audio Device In CHOP)
gives beats from a kick detector and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then
come on the beat even when a kick is missed, and a kick between beats is left out. It stops 8 beats after the kicks
do, and while it isn't locked every kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset
channels.

The sweep changes the strokes, not the colors: the filter keeps each area's colors whatever its brush, which is what
makes it a painting rather than a blur. So the library's reaction test (`dev/reaction.py`), which compares the
average color of each small cell of the picture, barely sees it: in the 0.2 s after a beat the picture changes 0.98
times as much as in the 0.2 s before (0.82 without the song). A band sliding across the picture is still easy to see,
which is why the beat sweeps rather than swelling the whole brush: twice the brush everywhere changed only 5% of a
still flower's pixels.

**Nothing wired:** no sweeps, and the brush keeps its size.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 5.3 ms on the GPU (95th percentile 5.9 ms) and 0.37 ms on the
CPU, the median of three runs. The painting costs most of it (3.8 ms); finding the edges, the lines and the style
together cost about 1.4 ms. Half Size cut the frame to 4.2 ms (the painting 1.7 ms, the upsampling 0.4 ms) and
two passes raised it to 6.5 ms. The brush size barely matters (Brush 24 measured the same as 12). GPU times on this
Mac wander from run to run, by a third or more, as its GPU changes speed. Nothing inside cooks while the output is
unused.

## Accessibility

- **No flashes of its own.** The painting follows the picture: it adds no light, color or movement the picture didn't
  have. In Oil and Watercolor a beat's sweep repaints a band in broader strokes, which keeps each area's colors, and
  the surface (canvas, paper, pigment) never changes. So Paint has no Flashing setting.
- **Ink doesn't sweep.** In Ink a sweep flipped whole patches between ink and paper: under the test beat the flowers
  measured 2.0 flashes a second against the clip's 1.0, and 1.0 without the sweep. So Ink's strokes follow the
  loudness, the builds and the drops, which measured clean, and not the beats.
- **No meaning in color.** The effect signals nothing by hue. Oil and Watercolor keep the picture's own colors,
  Watercolor a little lighter, and Ink is black on warm white.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far busier than music
(8 beats, 2 bars and 1 drop a second) and counted the flashes in the worst second, by WCAG's area rule, and WCAG's
red flashes separately:

| Clip and settings | Flashes | Red flashes | The clip alone |
|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 0 | 1.0, red 0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 0 | 1.0, red 0 |
| Dancer, no beat | 1.0 | 0 | 1.0, red 0 |
| People crossing a plaza | 0.5 | 0 | 0.5, red 0 |
| Red flowers against the sky | 0.5 | 1.5 | 1.0, red 1.0 |
| Koi in a black pond | 0.5 | 1.5 | 0.5, red 1.5 |
| Dancer, Beat Kick 1, Loudness 1 | 1.0 | 0 | 1.0, red 0 |
| Flowers, Beat Kick 1, Loudness 1 | 0.5 | 2.0 | 1.0, red 1.0 |
| Plaza, Beat Kick 1 | 0.5 | 0 | 0.5, red 0 |
| Dancer, Watercolor | 1.0 | 0 | 1.0, red 0 |
| Flowers, Watercolor | 0.5 | 1.5 | 1.0, red 1.0 |
| Dancer, Ink | 1.0 | 0 | 1.0, red 0 |
| Flowers, Ink | 1.0 | 0 | 1.0, red 1.0 |
| Dancer, Depth Brush 1 | 1.0 | 0 | 1.0, red 0 |
| Koi, 3 passes | 0.5 | 2.0 | 0.5, red 1.5 |

Every row is within WCAG's 3 a second, and the defaults add no flashes to the clips' own beyond the measurement's
half-flash margin. Red flashes follow the clips': the flowers and the koi make them by themselves, as their reds sit
near WCAG's line, and repainting them moves a few patches across it. At Beat Kick and Loudness both at 1 that came to
one more a second on the flowers.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It takes a few beats
  to lock and can still add or miss beats where the kicks don't keep the beat. Fosfora or audioAnalysis give steadier
  beats.

## Credits and license

MIT. The shaders and operators are written for this library from the papers below, including reading the ellipse on
a turned grid from mipmap levels, the pairing of opposite samples, the canvas weave, the depth and the music.

- **The anisotropic Kuwahara filter:** J. E. Kyprianidis, H. Kang and J. Döllner, ["Image and Video Abstraction by
  Anisotropic Kuwahara Filtering"](https://doi.org/10.1111/j.1467-8659.2009.01574.x) (Computer Graphics Forum 28(7),
  Pacific Graphics 2009). The ellipse along the flow, its anisotropy, the 8 sectors and their weighting by how much
  their colors vary are from the paper.
- **Its polynomial weights:** J. E. Kyprianidis, A. Semmo, H. Kang and J. Döllner, ["Anisotropic Kuwahara Filtering
  with Polynomial Weighting Functions"](https://doi.org/10.2312/LocalChapterEvents/TPCG/TPCG10/025-030) (EG UK Theory
  and Practice of Computer Graphics 2010). zeta and eta for 8 sectors, and computing the 8 weights from two sets of 4
  (its Listing 1), are from the paper.
- **The structure tensor** as J. E. Kyprianidis and J. Döllner use it, ["Image and Video Abstraction by Multi-scale
  Anisotropic Kuwahara Filtering"](https://www.kyprianidis.com/p/npar2011/jkyprian-npar2011.pdf) (NPAR 2011, 3.2):
  the derivative filter of B. Jähne, H. Scharr and S. Körkel ("Principles of filter design", 1999), the color tensor
  of S. Di Zenzo ("A note on the gradient of a multi-image", 1986), smoothing the tensor rather than the picture
  (T. Brox et al., "Adaptive structure tensors and their applications", 2006), and the anisotropy of G.-Z. Yang et al.
  ("Structure adaptive anisotropic image filtering", 1996).
- **The ink lines and Ink:** H. Winnemöller, J. E. Kyprianidis and S. C. Olsen, ["XDoG: An eXtended
  Difference-of-Gaussians Compendium Including Advanced Image Stylization"](https://doi.org/10.1016/j.cag.2012.03.004)
  (Computers & Graphics 36(6), 2012): the difference of Gaussians, the sharpened image, the soft threshold and the
  flow-based version, after H. Kang, S. Lee and C. K. Chui, "Coherent Line Drawing" (NPAR 2007). The smoothing along
  the edges is a line integral convolution, after B. Cabral and L. Leedom, "Imaging Vector Fields Using Line Integral
  Convolution" (SIGGRAPH 1993).
- **Watercolor:** A. Bousseau, M. Kaplan, J. Thollot and F. X. Sillion, ["Interactive Watercolor Rendering with
  Temporal Coherence and Abstraction"](https://doi.org/10.1145/1124728.1124751) (NPAR 2006): the pigment density
  formula, the turbulence, dispersion and paper layers, edge darkening by the painting's gradient and wobbling by the
  paper's are from the paper. The layers are drawn here with noise, where the paper used Perlin noise, Gaussian noise
  and scanned paper.
- **Noise:** gradient noise after K. Perlin, "Improving Noise" (SIGGRAPH 2002), on Chris Wellons' lowbias32 integer
  hash ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain).
- **Half Size:** joint bilateral upsampling, J. Kopf, M. F. Cohen, D. Lischinski and M. Uyttendaele, "Joint Bilateral
  Upsampling" (SIGGRAPH 2007). **Mipmaps:** L. Williams, "Pyramidal Parametrics" (SIGGRAPH 1983).
- **Seen during the survey, not used:** yeataro's
  [TD-Anisotropic-Kuwahara](https://github.com/yeataro/TD-Anisotropic-Kuwahara) (GPL-3.0, unfinished) and the basic
  Kuwahara in ogrew's [TD-PostEffectShader](https://github.com/ogrew/TD-PostEffectShader) (MIT).
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump in the low band's
  loudness, and the beat clock takes its tempo from the gaps between kicks, each gap voting for the beat lengths it is a
  whole multiple of. That is inter-onset-interval tempo induction, the idea behind S. Dixon's "Automatic Extraction of
  Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed, not copied, and written
  for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person.
