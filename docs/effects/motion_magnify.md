# Motion Magnify

![Two views of the same night scene side by side, each named in the library's pixel font. Five hooded figures in pale masks walk toward the camera along a dirt path in a dark field, each carrying a glowing lantern at their side. On the left, INPUT: they walk steadily, their lanterns barely swinging. On the right, MOTION MAGNIFY: the same walk with every sway made larger, so the lanterns swing like pendulums, their light stretching into streaks, and the figures lurch from side to side as they come, while the dark field and the sky behind them stay put](motion_magnify.webp)

*The defaults on five walkers carrying lanterns at night, the clip on the left: each step's sway, drawn four times as
large.*

**New to motion magnification?** Motion magnification makes the movements in a video larger than they were, while
whatever stands still stays where it is. It was invented to see what eyes miss, a building swaying in the wind or a
baby breathing, and MIT's video magnification of 2012, which made a face's pulse visible, made it famous. There are two
ways to do it. The Eulerian way, MIT's, changes each pixel's color over time without ever finding out what moved. The
Lagrangian way, older, measures how each part of the picture moves and then moves it further. This effect is
Lagrangian.

This effect measures how the live picture moves (optical flow) and draws every part further from where it rests. It
follows each part as it goes and keeps count of how far it is from where it usually is, and that count leaks back to
nothing, so a part that keeps moving one way (someone walking across) takes its rest along and stays as it was, while
one that goes back and forth (a sway, a nod, a bounce) grows. Timing picks how fast a back and forth grows most. Where
moving the picture further would fold it over itself, as a dancer's arm sweeping past would drag the wall behind her
into a knot, the movement is held back, so things stretch rather than tear. It runs on live video of any length at
60 fps. The Eulerian methods are patented in the US until 2032 to 2035 (see Credits), so it doesn't use them, and it
has no color mode that makes a pulse visible. I found no other free motion magnification for TouchDesigner; the
nearest is a 2012 forum file whose author calls it "not exactly Eulerian".

**[Download motion_magnify.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/motion_magnify.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `motion_magnify.tox` into your network. It shows TouchDesigner's sample movie of grass swaying in front of a
   painted wall, its sway made larger.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. A camera on a tripod works best: when the
   camera moves, everything moves, and all of it grows. Movement that goes back and forth grows most: people swaying,
   walking in place, nodding or dancing, plants in the wind, things hanging and swinging.
3. Optional: wire audio or beat channels into input 2 (see Audio input). Each beat then pushes the movement larger for a
   moment, and loudness grows it.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Depth Focus then keeps the
   larger movement to near things, or to what lies inside the mask. Without it everything grows.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `motion_magnify.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Motion Magnify page, top to bottom, in three groups: the movement, depth and the music, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Amount | 3 | How much further things move, 0 to 10. At 3 a movement is drawn 4 times as large; 0 shows the picture as it is, and the motion isn't measured. See [Amount](#amount). |
| Timing | 1 | Which movements grow, by how often they go back and forth, in Hz: 0.5 a slow sway or a breath, 1 a nod, 2 or 3 a bounce. Much slower movements (a steady walk across the picture) and much faster ones (a shake, the camera's noise) grow less. |
| Follow Tempo | Off | With beats on input 2, Timing follows the music: one back and forth every two beats (1 Hz at 120 BPM), as a dancer steps one way on a beat and back on the next. It takes the tempo from the beats of the last 4 seconds, and goes back to Timing when the beats stop. |
| Smoothness | 1 | How large the areas that move together are, 0.25 to 4. At 1 the movement is spread over about 12 pixels at 720 high. Lower lets small details move on their own (and tear more where they part), higher moves whole areas as one. |
| Depth Focus | 0.5 | With a depth map or mask on input 3: how much the movement grows only near the camera, or inside the mask, 0 to 1. At 1 far things, or what lies outside the mask, stay as they are. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Beat Kick | 0.5 | How much larger the movement grows for a moment on each beat of input 2, 0 to 1: at 1 twice as large at once, easing back over 0.4 s. |
| Loudness | 0.5 | How much larger the movement grows when the music is loud, and smaller when quiet, 0 to 1: at 1, up to half again as large, eased over half a second. |
| Song Moments | On | With Fosfora's signal on input 2, a build makes the movement grow by up to half as it rises, and a drop makes it twice as large for Length seconds. |
| Length | 1 | How long a drop makes the movement larger, in seconds. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## Amount

![Four views of a laughing woman's face, each named in the library's pixel font. INPUT is the clip: she breaks from a smile into a laugh, her eyes creasing shut. AMOUNT 1.5, AMOUNT 3 and AMOUNT 6 show the same laugh drawn larger each time: her smile widens further, her cheeks lift higher and her eyes squeeze tighter, until at 6 her mouth stretches wide and her features slide as she laughs, while her hair and the dark background stay put](motion_magnify_amounts.webp)

*The same laugh at Amount 1.5, 3 (the default) and 6, with a song on input 2.*

Each movement is drawn 1 + Amount times as large, within the timing Timing keeps. Up to about 3 it reads as the same
movement made bigger. Past that, faces and bodies turn rubbery and expressions turn into caricatures, and wherever two
parts of the picture move apart (a mouth opening, an arm crossing the body), what was behind them can't be shown, since
the picture never held it: the effect stretches the edge of what it has, and the fold guard keeps that from tearing.
Close to whatever moves, the still background is dragged along a little, since the movement is spread over its
neighbors (lower Smoothness drags less and tears more).

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it into input 2. Its beats
push the movement and its loudness grows it. With Song Moments on, a build grows the movement by up to half as it rises,
and a drop makes it twice as large, up in 0.3 s, held for Length and back over 0.8 s. Fosfora's drop detection is
experimental.

**Any input** brings the pushes, the loudness and Follow Tempo. On each beat the movement grows at once, to twice as
large at Beat Kick 1, and eases back over 0.4 s, so whatever is moving lunges further on the beat. Louder music grows
the movement up to half again at Loudness 1, and quiet passages shrink it, eased over half a second. Follow Tempo
centers Timing on one back and forth every two beats, the way a dancer steps one way on a beat and back on the next,
so the movements that keep time with the music grow most. Raw audio (an Audio File In or Audio Device In CHOP) gives
beats from a kick detector and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then come on
the beat even when a kick is missed, and a kick between beats is left out. It stops 8 beats after the kicks do, and
while it isn't locked every kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset channels.

**Nothing wired:** the movement grows by Amount alone.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 3.6 ms on the GPU (95th percentile 5.0 ms) and 0.5 ms on the CPU,
the median of three runs with the Mac otherwise idle. Measuring the motion costs most of it, about 2.4 ms for the
optical flow; everything about the movement is worked out at a quarter of the picture's size, and only moving the
picture runs at its full size. At Amount 0 the motion isn't measured, and the effect costs 0.07 ms. GPU times on this
Mac wander from run to run as its GPU changes speed: the same build measured 2.2 to 3.1 ms while another effect ran
beside it, which kept the GPU busier and faster. Nothing inside cooks while the output is unused.

## Accessibility

- **No flashes of its own.** The effect adds no light, and it changes how far things move, not how often they go back
  and forth, so it has no Flashing setting. Each beat's push measured no more than no beat at all on the dancer, at a
  dance tempo, under the test's 8 beats a second and at Beat Kick 1.
- **Larger movement, the clip's own changes.** Moving things further sweeps their edges across more of the picture, so
  a clip's own changes can count where they didn't: the laughing face measured 1.0 flashes a second against the clip's
  0.5 with no beat (1.5 under the test's 8 beats a second), and the flowers 1.5 against 1.0.
- **Reds kept short of the line.** WCAG counts a pixel as saturated red, all or nothing, once red is 80% of its light, so
  red flowers swaying wider swept reds near that line across it more often: 2 red flashes a second with no beat, the
  clip's own 1. Every red the effect shows is now eased short of that line (the library's red guard, as Slit-Scan's), so
  it shows none, even where the clip had them.
- **No meaning in color.** The effect signals nothing by hue; it shows the picture's own colors, moved.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far busier than music (8
beats, 2 bars and 1 drop a second) and counted the flashes in the worst second by WCAG's area rule, and WCAG's red
flashes separately:

| Clip and settings | Motion Magnify | The clip alone |
|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.0 |
| Dancer, no beat | 1.0 | 1.0 |
| Dancer, Beat Kick 1 | 1.0 | 1.0 |
| Walkers with lanterns at night | 0.5 | 0 |
| People crossing a plaza | 0.5 | 0.5 |
| Red flowers against the sky | 1.5 | 1.0, red 1.0 |
| Flowers, Beat Kick 1 | 1.5 | 1.0, red 1.0 |
| Koi in a black pond | 1.0 | 0.5, red 1.5 |
| A laughing face | 1.5 | 0.5 |
| Face, 140 BPM | 1.0 | 0.5 |
| Face, no beat | 1.0 | 0.5 |
| Flowers, Amount 10, Beat Kick 1, Loudness 1 | 2.0 | 1.0, red 1.0 |

At the defaults no row adds more than a flash a second to the clip's own, and at a dance tempo or with no beat no more
than the half flash a second the count allows for measuring noise. The last row is the far corner of every range,
spot-checked: within WCAG's 3. Red flashes: none in any row.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It takes a few beats
  to lock and can still add or miss beats where the kicks don't keep the beat. Fosfora or audioAnalysis give steadier
  beats.
- The motion is measured, and where a measure goes wrong the picture moves wrong: across a flat area with nothing to
  follow (a plain wall, a clear sky), through smoke or reflections, and wherever one thing slides in front of another.

## Credits and license

MIT. The shaders and operators are written for this library, including the displacement carried with the picture and
leaking back to rest, the timing band, the fold guard, Follow Tempo, the pushes on the beat and the depth focus.

- **Lagrangian motion magnification:** the motion measured, then the picture moved further along it, after C. Liu, A.
  Torralba, W. T. Freeman, F. Durand and E. H. Adelson, ["Motion
  Magnification"](https://people.csail.mit.edu/celiu/motionmag/motionmag.html) (SIGGRAPH 2005), who track points, group
  them into layers and move a layer further, offline. Followed, not copied. Later Lagrangian methods measure dense
  optical flow from a reference frame and warp the picture by it, such as P. Flotho, C. Heiss, G. Steidl and D. J.
  Strauss, ["Lagrangian motion magnification with double sparse optical flow
  decomposition"](https://doi.org/10.3389/fams.2023.1164491) (Frontiers in Applied Mathematics and Statistics, 2023);
  this effect wasn't built after them.
- **The displacement** added up frame by frame, carried with the content and leaking back to rest, so the effect runs on
  live video of any length with no reference frame, and the leak and its easing choose the movements' timing: original
  (no earlier source found). The carrying is semi-Lagrangian advection, as in J. Stam, ["Stable
  Fluids"](https://doi.org/10.1145/311535.311548) (SIGGRAPH 1999), and [Pencil](pencil.md)'s strokes.
- **The fold guard:** a warp stays one to one, folding nothing over, while its displacement changes by less than a pixel
  per pixel, the kind of condition Y. Choi and S. Lee give for warping images, ["Injectivity conditions of 2D and 3D
  uniform cubic B-spline functions"](https://doi.org/10.1006/gmod.2000.0531) (Graphical Models, 2000). Holding the
  displacement back locally, by the largest stretch nearby: original (no earlier source found).
- **Not used:** Eulerian video magnification, which filters each pixel over time and adds the change back (H.-Y. Wu, M.
  Rubinstein, E. Shih, J. Guttag, F. Durand and W. T. Freeman, ["Eulerian Video Magnification for Revealing Subtle
  Changes in the World"](https://people.csail.mit.edu/mrub/evm/), SIGGRAPH 2012), and its phase-based forms (N. Wadhwa,
  M. Rubinstein, F. Durand and W. T. Freeman, ["Phase-Based Video Motion
  Processing"](https://people.csail.mit.edu/nwadhwa/phase-video/), SIGGRAPH 2013, and ["Riesz Pyramids for Fast
  Phase-Based Video Magnification"](https://people.csail.mit.edu/nwadhwa/riesz-pyramid/), ICCP 2014). They are
  patented in the US by MIT, which licenses them for a fee, until 2032 to 2035 (US 9,805,475, 9,811,901, 10,007,986,
  10,217,218, 9,324,005 and 9,338,331), so this effect doesn't filter the picture's pixels over time and has no color
  (pulse) mode. The library's code is MIT-licensed, which covers the code, not anyone's patents; this effect was built
  to stay outside those patents' claims, but that is our reading, not legal advice.
- **The motion** is the library's Lucas-Kanade optical flow, written from B. D. Lucas and T. Kanade, "An Iterative
  Image Registration Technique with an Application to Stereo Vision" (1981), shared with [Datamosh](datamosh.md),
  [Fluid](fluid.md), [Pencil](pencil.md) and [VHS + CRT](vhs_crt.md). **The red guard** (`lib/glsl/red_guard.glsl`)
  is shared with [Bent Cam](bent_cam.md), [Slit-Scan](slit_scan.md) and VHS + CRT.
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Fluid, Paint, Particles, Pencil and Point Cloud.
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump in the low band's
  loudness, and the beat clock takes its tempo from the gaps between kicks, each gap voting for the beat lengths it is
  a whole multiple of. That is inter-onset-interval tempo induction, the idea behind S. Dixon's "Automatic Extraction
  of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed, not copied, and
  written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
