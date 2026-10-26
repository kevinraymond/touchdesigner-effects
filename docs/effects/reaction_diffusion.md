# Reaction-Diffusion

![Reaction-Diffusion at its defaults on a close-up of a laughing woman's face, in black and white stripes. The stripes curve around her eyes and cheeks and run down her nose like the ridges of a fingerprint, thin and far apart on her lit skin and broad and black in the shadows, and the dark background behind her breaks up into scattered specks. Now and then, on the beat, a ripple runs through the drawing and the stripes slide out and back](reaction_diffusion.webp)

*The defaults (Lines, Medium) on a portrait, with a song on input 2: stripes that follow the face, broad in the
shadows and thin in the light, and now and then a ripple on the beat.*

**New to reaction-diffusion?** It is one way nature might paint a zebra. Two chemicals spread out over a surface and
react with each other: one feeds the other, which turns it into more of itself, and they spread at different speeds.
From a few specks they settle into stripes, spots or a branching coral that hold their shape. Alan Turing proposed it
in 1952 as how animals get their markings, and the Gray-Scott model (1983), whose patterns John Pearson mapped in
1993, is the version most people play with. You may have seen it as slowly growing mazes and coral in generative art.

This effect grows that pattern over live video and steers it with the picture. The chemicals spread faster along the
picture's edges than across them, as Witkin and Kass did in 1991, so the stripes run along its contours, around an eye
or down a stem, like a fingerprint. Lines draws the picture by the width of its stripes, as an engraving does, broad
where the picture is dark and thin where it is bright. Dots and Coral change the pattern itself with the picture's
darkness, from holes to spots or from dense coral to scattered branches. It can grow everywhere, or only on what is
bright, what moves, or what stands out in a depth map or mask on input 3, and on the beats a ripple runs through the
drawing. The free reaction-diffusion components for TouchDesigner diffuse the same way in every direction, so their
stripes wander every way whatever the picture; this one is MIT and follows the picture's edges.

**[Download reaction_diffusion.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/reaction_diffusion.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `reaction_diffusion.tox` into your network. It shows TouchDesigner's sample movie of a river running over
   rocks. The picture shows at once as an even tone, and the pattern grows in from scattered seeds and takes over
   within a few seconds.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Faces, figures against a plain
   background and pictures with clear shapes draw best. Where the picture moves, the pattern takes a moment to follow.
3. Optional: wire audio or beat channels into input 2 (see Audio input). The beats then send ripples through the
   drawing, as often as Flashing allows.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside), and set Grow On to
   Depth or Mask. The pattern then grows only on what stands out, or inside the mask. Without it, the picture's
   brightness stands in for depth.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset clears the pattern, and it
grows back the same way.

To update, delete your copy and drag in the new `reaction_diffusion.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Reaction-Diffusion page, top to bottom, in four groups: the pattern, where it grows, the ink and the music, then
Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Pattern | Lines | Lines draws stripes along the edges, broad where the picture is dark and thin where it is bright, like an engraving. Dots draws holes in the dark, a maze in between and spots in the light. Coral grows a branching coral, dense in the dark and scattered in the light. See [The patterns](#the-patterns). |
| Size | Medium | How big the pattern is, Fine, Medium or Coarse, each twice the last. The pattern grows on a grid the picture's size, half or a quarter of it, so Fine costs four times Medium. Fine shows faces and small things best; Medium and Coarse read from across a room. |
| Follow Edges | 1 | How much the stripes turn to run along the picture's edges, 0 to 1. At 1 the chemicals spread three times faster along a clear edge and three times slower across it. At 0 they spread the same every way, and the stripes wander. |
| Speed | 1 | How fast the pattern grows and reshapes as the picture changes, 0.25 to 2. |
| Reset | | Clears the pattern. The picture shows as an even tone while the pattern grows back from new seeds. |
| Grow On | Everywhere | Where the pattern grows: everywhere, on what is bright, on what moved in the last second, on what stands out in the depth map on input 3, or inside the mask on input 3. Elsewhere it breaks into spots and fades. See [Where it grows](#where-it-grows). |
| Sensitivity | 0.5 | How easily the pattern grows, 0 to 1: dimmer brightness, slower movement, farther depth or a grayer mask counts as well. Grayed out for Everywhere. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. Grayed out unless Grow On is Depth or Mask. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Ink Level | 0.5 | How much ink the picture's middle brightness takes, 0 to 1: lower for a lighter drawing, higher for a darker one. The picture's brightness is stretched between its darkest and brightest first, followed over a second, so a gray river reads as well as a dark stage. |
| Contrast | 1 | How strongly the picture's brightness sets the ink, 0 to 2. At 1 it runs from all ink at the picture's darkest to none at its brightest. At 0 the pattern is the same everywhere, and only its direction follows the picture. |
| Colors | Ink on Paper | Ink on paper, the ink Over the Picture itself, Light on Dark (light lines where the picture is bright, on black), or Orange and Blue (blue ink on orange). |
| Beat Kick | 0.5 | How deep the ripple is that the beats of input 2 send across the picture, 0 to 1. The stripes it passes slide out and back, up to 6 cells of the pattern's grid at 1. A ripple counts as a flash, so it comes as often as Flashing allows. |
| Loudness | 0.5 | How much louder music makes the lines bolder, and quiet passages finer, 0 to 1, eased over half a second. |
| Song Moments | On | With Fosfora's signal on input 2, a drop sends a broad, deep ripple out from the middle, through the same gate as the beats. |
| Flashing | Calm | How often a ripple may come. Off never ripples. Calm, the default, ripples at most once a second (every second or third beat at dance tempos). Up to 3 per second is the WCAG 2.3.1 limit, every beat up to 180 BPM. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The patterns

![Four views of a field of tall red flowers against a sunny sky, each named in the library's pixel font. INPUT is the clip as it is. LINES draws it in black stripes, thin and far apart in the bright sky and broad where the flowers and leaves are dark, running up the stems. DOTS turns the sky into scattered black spots, the flowers into a maze and the darkest leaves into black with white holes. CORAL grows a branching maze across the sky and fills the dark field below with black dotted with white holes](reaction_diffusion_patterns.webp)

*Each pattern on the flowers at the defaults otherwise, with the song on input 2.*

**Lines** sits just past the point where Gray-Scott's even mixture breaks up into stripes (feed 0.028, kill 0.0555).
There the stripes start as gentle waves that turn readily, so they line up along the picture's edges far better than
the mazes further in, which barely turned. Its pattern stays the same everywhere, and the drawing makes the tone: ink
wherever the pattern stands above a level set by the picture's darkness, so the same stripe is broad in a shadow and a
hairline in a highlight, as in an engraving.

**Dots** moves the kill rate with the picture's darkness at feed 0.030: from 0.0555, where the pattern is ink with
holes in it, through a maze, to 0.0615, where it breaks into separate spots. The pattern itself is the tone.

**Coral** does the same further into the map (feed 0.055, kill 0.0605 to 0.0655), where the pattern grows like a
branching coral, dense in the dark and thinning to scattered spots in the light.

Each pattern takes a moment to change where the picture changes: the chemicals move a few cells a frame.

## Where it grows

Everywhere, the default, grows the pattern over the whole picture. The other choices grow it only on part of the
picture, and elsewhere the kill rate rises, so the pattern breaks into spots and fades and new seeds start it again
wherever it may grow.

- **Brightness** grows it on what is bright: a lit performer on a dark stage, a beam of light.
- **Movement** grows it on what moved in the last second, so it trails a dancer and breaks up behind them. The camera
  must stay still, since a moving camera moves everything.
- **Depth (Input 3)** grows it on what stands in front of its surroundings in the depth map, as in Fluid and
  Particles. Floors and walls drop out, someone cut off by the left or right edge drops out too, and feet merge with
  the floor. With nothing on input 3, the picture's brightness stands in (only what is brighter than half counts).
- **Mask (Input 3)** grows it inside the mask, white inside (MediaPipe, the NVIDIA Background TOP).

With Ink on Paper the rest of the picture is blank paper, and with Over the Picture it is the picture itself.

## How it works

**The chemicals.** Two chemicals, U and V, live on a grid at the picture's size, a half or a quarter of it (Size), in
32-bit float. Each step, U feeds V where they meet (U V^2 turns U into V), U is topped up at the feed rate F, V decays
at F + k (k, the kill rate), and both diffuse, U twice as fast as V:

    dU/dt = Du lap(U) - U V^2 + F (1 - U)
    dV/dt = Dv lap(V) + U V^2 - (F + k) V

`react` runs these steps, many a frame (a GLSL TOP's Passes, each reading the last), 1,200 of the model's time units a
second at Speed 1 (up to 48 steps a frame), and `state_fb` hands the result to the next frame. `seed` takes it up: it
sets each cell's kill rate from what the picture asks for there, and drops a spot of V, now and then, wherever the
pattern may grow but hasn't. The spots are 4 cells across or more: smaller ones died where the diffusion is stretched.

**Steering.** `tensor`, `tensor_h`, `tensor_v` and `flow` (the library's `structure_tensor()`, shared with Paint) find
the direction of the picture's edges at every cell and how clear it is, from the smoothed structure tensor, which
`tensor_ease` eases over half a second so the direction turns smoothly instead of jittering with the picture's noise.
Where the direction is clear, `react` diffuses three times faster along it and three times slower across it, which
keeps the stripes' spacing and stretches them along the edges (Witkin and Kass's anisotropic reaction-diffusion). Each
second difference is taken along a unit step, read bilinearly from the 3 x 3 cells around, so every neighbor counts
positively and the step stays stable at any angle. Both rates had to change together: slowing only the across rate
shrank the stripes to two cells apart, finer than the grid can draw, and speeding only the along rate grew the pattern
without stretching it. A direction counts only where the picture changes enough to have one, since the noise on a dark
stage points every way.

**The ink.** `exposure` finds the picture's darkest and brightest, from a 16 x 9 grid of a small mipmap level, eased
over a second, and `where` stretches its brightness between them, bends it so the middle comes out at Ink Level, and
eases the result over a quarter of a second, so a flicker in the picture can't flip the lines back and forth. `look`
draws the pattern at the picture's size, V brought up by a Catmull-Rom bicubic and its edge smoothed over one output
pixel, so the lines stay crisp and smooth at any Size. For the first two seconds after the pattern starts it shows the
ink the picture asks for as an even tone, then crossfades into the pattern, which has grown in by then.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it into input 2. Its
beats send ripples, as often as Flashing allows, and louder music makes the lines bolder. With Song Moments on, a drop
sends a ripple out from the middle, three times as broad and twice as deep, over 1.2 s. Fosfora's drop detection is
experimental.

**Any input** brings the ripples on its beats and the lines following the loudness. On a beat a ripple runs out across
the picture in 0.6 s, from a point that turns round the middle by the golden angle each beat, a quarter of the
picture's height out. Across its band, about a twelfth of the picture's height wide, the drawing reads the pattern
from a little farther out and then a little farther in, so the stripes slide out and back as if seen through a wave in
glass. The ripple moves the drawing, not the pattern. Rings that turned the pattern itself over at every beat
scrambled it into a maze that never settled along the edges again. The stripes are about as wide as the cells a flash
test measures, though, so a slide swings them between light and dark, which counts as a flash: the beats pass through
the flash gate, and at Calm a ripple comes at most once a second (see Accessibility). Louder music adds up to 15% ink
at Loudness 1, eased over half a second. Raw audio (an Audio File In or Audio Device In CHOP) gives beats from a kick
detector and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then come on the beat even
when a kick is missed, and a kick between beats is left out. It stops 8 beats after the kicks do, and while it isn't
locked every kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset channels.

**Nothing wired:** no ripples, and the lines keep their weight.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters (Lines, Medium). Each frame took 4.0 ms on the GPU (95th percentile 5.7 ms) and
0.46 ms on the CPU, the median of three runs. The pattern's steps cost most of it, about 3.4 ms for the 31 steps of
the model a frame at 60 fps; finding the edges, the ink and the drawing together cost about 0.7 ms. Fine took 7.5 ms
(its steps 6.6 ms, on four times the cells) and Coarse 2.0 ms. Pattern, Grow On and Colors barely change the cost. GPU
times on this Mac wander from run to run, by a tenth or more (3.8 to 4.3 ms here), as its GPU changes speed. Nothing
inside cooks while the output is unused, and an unused effect holds its pattern until it is shown again.

## Accessibility

- **Flashing.** A ripple slides the stripes, and the stripes are about as wide as the cells the flash test measures
  (20 pixels at 1280 x 720), so the ones it passes swing between light and dark. On the dancer, ripples on every beat
  measured a flash a second over the clip's own at Beat Kick 1 at 140 BPM, and more under the test's 8 beats a second.
  So the beats and drops pass through the standard flash gate: Off never ripples, Calm (the default) ripples at most
  once a second, and Up to 3 per second is WCAG 2.3.1's limit.
- **The pattern itself doesn't flash.** Once grown in, it holds its shape where the picture holds still (on a still
  frame it measured no flashes). Followed at once, the drifting smoke on the dancer clip turned and thickened the
  stripes back and forth, a flash and a half a second over the clip's own with no beat at all, so the direction of the
  edges eases over half a second and the picture's tone over a quarter. Growing in on blank paper, the pattern swung
  each place between light and dark as spots appeared and split, so it starts as an even tone and crossfades into the
  pattern once it has grown in. Loudness thickens the lines over half a second.
- **No meaning in color.** The effect signals nothing by hue. Its colors are ink on warm paper, the picture's own
  under the ink, white on black, or blue on orange, and all of them read by brightness.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far busier than music (8
beats, 2 bars and 1 drop a second) and counted the flashes in the worst second by WCAG's area rule, and WCAG's red
flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 2.5 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.5 | 1.5 | 1.0 |
| Dancer, 140 BPM, Beat Kick 1 | 1.0 | 1.5 | 2.0 | 1.0 |
| Dancer, no beat | 1.0 | | | 1.0 |
| People crossing a plaza | 0.5 | 1.5 | 2.5 | 0.5 |
| Red flowers against the sky | 1.0 | 1.5 | 2.0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0 | 1.0 | 2.0 | 0.5, red 1.5 |
| Flowers, Over the Picture | | 1.0, red 1.0 | | 1.0, red 1.0 |
| Dancer, Beat Kick 1 and Loudness 1 | | 2.0 | | 1.0 |
| Dancer, Dots | | 1.5 | | 1.0 |
| Dancer, Coral | | 2.0 | | 1.0 |
| Dancer, Fine | | 1.0 | | 1.0 |
| Dancer, Coarse | | 2.0 | | 1.0 |
| Dancer, Grow On Movement | | 1.5 | | 1.0 |
| Dancer, Grow On Depth | | 1.5 | | 1.0 |

Every row keeps its setting's promise: Off adds nothing to the clip's own beyond the measurement's half-flash margin
(the koi's 1.0 against 0.5), Calm adds at most one a second, and nothing passes WCAG's 3. Red flashes: Ink on Paper
and the other drawn colors make none, so the flowers' and the koi's own red flashes are gone; Over the Picture keeps
the picture's (the flowers' 1.0).

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It takes a few beats
  to lock and can still add or miss beats where the kicks don't keep the beat. Fosfora or audioAnalysis give steadier
  beats.

## Credits and license

MIT. The shaders and operators are written for this library from the papers below, including the steering's second
differences along the edges and across them (a usual way to discretize anisotropic diffusion, with no one source
followed), the seeding, the stretch and easing of the picture's tone, the engraving's line widths, the fade-in and the
beat's ripple.

- **Reaction-diffusion:** A. M. Turing, ["The Chemical Basis of
  Morphogenesis"](https://doi.org/10.1098/rstb.1952.0012) (Philosophical Transactions of the Royal Society B 237,
  1952).
- **The Gray-Scott model:** P. Gray and S. K. Scott, ["Autocatalytic reactions in the isothermal, continuous stirred
  tank reactor: isolas and other forms of multistability"](https://doi.org/10.1016/0009-2509(83)80132-8) (Chemical
  Engineering Science 38, 1983), and its patterns as J. E. Pearson mapped them, ["Complex Patterns in a Simple
  System"](https://doi.org/10.1126/science.261.5118.189) (Science 261, 1993). The feed and kill rates of each pattern
  here were found by running the model over Pearson's region of the map, and the diffusion rates (0.21 and 0.105 a
  cell) are the usual ones for it.
- **Steered diffusion:** A. Witkin and M. Kass, ["Reaction-Diffusion Textures"](https://doi.org/10.1145/122718.122750)
  (SIGGRAPH 1991, Computer Graphics 25(4)): diffusion that runs faster one way than another, and varies across the
  picture, so the stripes follow a direction.
- **The structure tensor** as J. E. Kyprianidis, H. Kang and J. Döllner use it, ["Image and Video Abstraction by
  Anisotropic Kuwahara Filtering"](https://doi.org/10.1111/j.1467-8659.2009.01574.x) (Pacific Graphics 2009), and J.
  E. Kyprianidis and J. Döllner (NPAR 2011), with the derivative filter of B. Jähne, H. Scharr and S. Körkel (1999):
  the library's `structure_tensor()`, shared with Paint.
- **Crisp lines:** a Catmull-Rom bicubic (Catmull and Rom, 1974), shared with Datamosh and Fluid. **Seeds** fall where
  Chris Wellons' lowbias32 integer hash says ([hash-prospector](https://github.com/skeeto/hash-prospector), public
  domain).
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`, `depth_find.glsl`) is shared with Fluid, Particles and Point Cloud.
- **Seen during the survey, not used:** the reactionDiffusion in aaronmylespereira's
  [TD-Toxes](https://github.com/aaronmylespereira/TD-Toxes) (MIT, made from free tutorials), paid versions on Gumroad
  and a free `.tox` shared on Reddit (no license stated). Each diffuses the same way in every direction.
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump in the low band's
  loudness, and the beat clock takes its tempo from the gaps between kicks, each gap voting for the beat lengths it is
  a whole multiple of. That is inter-onset-interval tempo induction, the idea behind S. Dixon's "Automatic Extraction
  of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed, not copied, and
  written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
