# Ferrofluid

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. BLACK lays a black glossy liquid over the picture: over the bright haze and over her it bristles into rows of sharp black spikes, leaning a little so their tips stand above their bases, their upper flanks lined with light; elsewhere the liquid lies flat and the warehouse shows dimly through it. TINTED raises the same spikes in the picture's own colors, the warehouse at full brightness around them. LARGE SPIKES raises fewer, taller spikes twice as far apart](ferrofluid.webp)

*Ferrofluid on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: Black (the default), Tinted, and Black with Spike Size at Large. The spikes rise over the bright haze and over her, and swell with the bass.*

**New to ferrofluid?** A ferrofluid is an oil full of tiny magnetic particles. Hold a magnet under a dish of it and,
once the field is strong enough, its flat surface rises into a lattice of sharp spikes, all the same distance apart and
packed in hexagons. The spikes stand up as the field passes a threshold and lie down again as it falls. Physicists call
it the Rosensweig or normal-field instability, after Ronald Rosensweig, who described it with Michael Cowley in 1967.
It shows up in science museums and in music videos, where a speaker or an electromagnet under the dish makes the spikes
dance to the bass.

This effect pours that liquid over your picture. Where the picture is bright, or with a depth map on input 3 where
something stands in front, the field is strong and the liquid bristles; elsewhere it lies flat and the picture shows
through it. The bass sets how strong the field is, so the spikes rise and fall with the music, and a magnet under the
liquid wanders a step on each bar. The liquid is a black mirror that reflects the picture and a soft light hung above
it, and the view leans a little, so each spike shows its side. In TouchDesigner I found ferrofluid only as hardware,
spikes on a real dish driven from TouchDesigner, and on the web shaders that draw cones on a fixed grid. None grows the
spikes over a picture.

**[Download ferrofluid.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/ferrofluid.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `ferrofluid.tox` into your network. It shows TouchDesigner's sample movie, and the liquid bristles over its
   bright sand and sky within a second.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Optional: wire music into input 2 (see Audio input). The bass then sets the field's strength, so the spikes rise and
   fall with it, each beat makes them jump, and each bar moves the magnet.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). What stands in front (or is
   inside the mask) then bristles too. Without it, the picture's brightness alone draws the spikes up.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset lays the liquid flat, and the
spikes grow back.

To update, delete your copy and drag in the new `ferrofluid.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Ferrofluid page holds, top to bottom, the look, the field, input 3, the music, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Style | Black | Black: the liquid is black, as a magnetic fluid is, a mirror that reflects the picture, which shows through it where it lies flat. Tinted: the liquid is the picture itself, its colors on the spikes. |
| Spike Size | Medium | How far apart the spikes are, Small, Medium or Large, each twice the last (about 14, 28 and 56 pixels on a 1280-wide picture). The spikes grow on a grid half, a quarter or an eighth of the picture's size, so Small costs about one and a half times as much as Medium. |
| Height | 0.5 | How tall the spikes stand for their spacing, 0 to 1. |
| Tilt | 0.6 | How far the view leans, so each spike shows its side and hides what is behind it, 0 to 1. At 0 the liquid is seen straight on, and the spikes read as beads. |
| Picture | 0.5 | Black only: how much of the picture shows through the liquid where it lies flat, 0 to 1. At 0 a black pool. |
| Strength | 1 | How strong the field is, 0 to 2. Below about 0.3 the liquid lies flat. Past 1 the spikes join into ridges, as a real ferrofluid's do in a strong field. |
| By Brightness | 1 | How much the bright parts of the picture draw the spikes up, 0 to 1. |
| By Nearness | 1 | How much what stands out in front in the depth map on input 3 (or what is inside the mask) draws the spikes up, 0 to 1. |
| Magnet | 0.3 | How strong a magnet under the liquid is, 0 to 1. It draws spikes up wherever it is, and wanders: a step each bar of input 2, or on its own with nothing wired. |
| Reset | | Lays the liquid flat. The spikes grow back. |
| Input 3 Holds | Depth Map | Depth Map: what stands in front of its surroundings draws the spikes up, while floors and walls don't count. Mask: what is inside the mask (white inside) does. |
| Sensitivity | 0.5 | How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask counts as inside. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Bass | 0.6 | How much the bass of input 2 sets the field's strength, 0 to 1. At 1 silence lays the liquid flat and every bass note raises the spikes. |
| Beat Pulse | 0.5 | How far the spikes jump up on each beat of input 2, 0 to 1, as often as Flashing allows. |
| Flashing | Calm | How often the beats may make the spikes jump. Off: never. Calm: at most once a second. Up to 3 per second: the WCAG 2.3.1 limit. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## How it works

**The spikes** grow by the Swift-Hohenberg equation, which Jack Swift and Pierre Hohenberg wrote down in 1977 for
patterns that rise past a threshold with a set spacing, and which physicists still use for the Rosensweig spikes. The
liquid's height h changes each step by r h, minus a term that lets through only ripples of the spikes' spacing, plus
g h² and minus h³. r is how far past the threshold the field is: below 0 every ripple dies away and the liquid lies
flat; above 0 ripples of the spacing grow. The h² term makes them meet in hexagons, spikes up, and makes the onset
abrupt, so a spike snaps up once the field passes the threshold and lingers a little as it falls back. The h³ term
stops them growing. Past about r = 0.5 the hexagons give way to ridges, which is what Strength above 1 reaches.

The effect runs the equation on a grid a quarter of the picture's size (by Spike Size: a half or an eighth), 20 steps
a frame at 60 fps. The spikes sit six cells apart, which is as far apart as the steps allow: the steepest ripples the
grid holds set the longest step that stays stable, and at eight cells apart that step became too short to grow the
spikes within a frame or two. Each frame adds a trace of noise, a hundredth of a spike's height, which the spikes grow
from, as a real liquid's spikes grow from its ripples. The field's r comes from the picture: higher where it is bright,
where something stands out in front, and where the magnet is, scaled by Strength and the bass.

**The look.** The equation's spikes are smooth bumps. Near its peak a bump falls off as the square of the distance, so
knowing the peak's height tells how far from it a point is, and the effect reshapes every bump into a cone with a sharp
tip and flanks that curve in, as a real spike stands. Seen straight on, cones read as beads, so the view leans: each
pixel marches down from above the tallest spike toward the flat liquid, stepping back along the lean, and the first
point of the surface its ray meets is what it sees (steep parallax mapping). The liquid is a glossy mirror. It reflects
more the more steeply it is seen, and what it reflects is the picture itself, slid along with the surface's slope as in
a curved mirror, and a soft light hung above it, which lines the spikes' upper flanks; a lamp's highlight catches every
tip. In Black, the picture shows through where the liquid lies flat (Picture). In Tinted, the liquid is the picture,
lit from the upper left.

**Where the spikes rise.** Bright parts of the picture draw them up (By Brightness), and with a depth map on input 3
so does whatever stands out in front of what lies left and right of it, which leaves floors and walls out: raw
nearness bristled the whole floor. A spike needs about its own spacing of room, so thin arms and fingers don't bristle,
and the field spreads a little past an edge, as a magnet's does.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats, bars and bass. Drag `fosfora_signal.tox` (in
Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw audio** (an Audio File In
or Audio Device In CHOP) gives the bass from its own low band and the beats from a kick detector and a beat clock.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the bass from its low band.

The bass sets the field's strength (Bass): at 0.6, quiet passages leave 40% of the field and the bass adds the rest,
so the spikes pump with every bass note, rising in a twentieth of a second and falling back over a third. Each beat
makes them jump up at once and settle over a third of a second, as often as Flashing allows (Beat Pulse). Each bar
moves the magnet a step along its path, at most once every 2 seconds, eased over a second and a half.

**Nothing wired:** the field holds steady at Strength, and the magnet drifts a step every 8 seconds.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, the dancer's depth on input 3 and a beat far busier than music on input 2. Each
frame took 3.0 ms on the GPU (95th percentile 3.6 ms) and 0.54 ms on the CPU, the median of three runs with the Mac
otherwise idle. The spikes' 20 steps take about 1.4 ms of it, the look 0.8 ms and the cones 0.55 ms. Spike Size Small
grows them on a grid four times as large: 4.4 ms on the GPU. GPU times on this Mac wander from run to run as its GPU changes speed. Nothing
inside cooks while the output is unused.

## Accessibility

- **Flashing setting (Calm by default).** A beat's jump raises the spikes over a wide area at once, so it goes through
  the Flashing setting: Off never jumps, Calm at most once a second, Up to 3 per second at most three times.
- **Measured below the clip's own.** The spikes rise in a twentieth of a second and fall over a third, the noise they
  grow from is too small to see, and every pixel goes through a red guard, so no red near WCAG's saturated-red line
  flips across it as the spikes pump.
- **No meaning in color.** The effect signals nothing by hue. The spikes read by their shape and their light.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully 8 times a second) and counted the flashes in the worst second by
WCAG's area rule, and WCAG's red flashes separately. The dancer had her depth map on input 3:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 0.5 | 0.5 | 0.5 | 1.0 |
| Dancer, Tinted | 1.0 | 1.0 | 1.0 | 1.0 |
| Red flowers against the sky | 0.5 | 0.5 | 0.5 | 1.0, red 1.0 |
| Red flowers, Tinted | 1.0 | 1.0 | 1.0 | 1.0, red 1.0 |
| Red flowers, the corners | 1.0 | 1.0 | 1.0 | 1.0, red 1.0 |
| People crossing a plaza | 0 | 0 | 0 | 0.5 |
| A pair of hands | 1.0 | 1.0 | 1.0 | 1.5 |
| Koi in a black pond | 0.5 | 0.5 | 0.5 | 0.5, red 1.5 |

No row adds to the clip's own flashes, and none flashes red: Black often counts fewer than the clip, since its flat
liquid shows the picture dimmed. The corners set Strength 2, Beat Pulse 1, Height 1 and Spike Size Small together.

## Experimental

- Raw audio's beat clock is experimental and can still add or miss beats.

## Credits and license

MIT. The shaders and operators are written for this library, including the picture and the depth as the field, the
magnet that wanders on the bars, the cones shaped from the field's peaks, the leaning view of the liquid and the
picture showing through where it lies flat.

- **The phenomenon:** M. D. Cowley and R. E. Rosensweig, "The interfacial stability of a ferromagnetic fluid" (Journal
  of Fluid Mechanics 30, 1967): past a critical field a magnetic fluid's flat surface rises in a hexagonal lattice of
  spikes with a set spacing. A. Gollwitzer, I. Rehberg and R. Richter, ["Via hexagons to squares in
  ferrofluids"](https://arxiv.org/abs/nlin/0607059) (Journal of Physics: Condensed Matter 18, 2006): the hexagons
  measured from the flat surface on, and their turn to squares at higher fields. Their squares at higher fields aren't here: the equation below turns from hexagons to
  ridges, not squares.
- **The spikes' growth:** J. Swift and P. C. Hohenberg, "Hydrodynamic fluctuations at the convective instability"
  (Physical Review A 15, 1977), with a quadratic term for hexagons, stepped with the isotropic 9-point Laplacian of
  Y. Oono and S. Puri, "Study of phase-separation dynamics by use of cell dynamical systems" (Physical Review A 38,
  1988). Running it as a ferrofluid's surface over a picture at a frame's pace is this library's design: I found no
  published real-time method for a ferrofluid's height.
- **The view:** steep parallax mapping (T. Kaneko et al., "Detailed shape representation with parallax mapping", ICAT
  2001; M. McGuire and M. McGuire, "Steep Parallax Mapping", I3D 2005 poster); the reflection by C. Schlick's
  approximation of Fresnel's equations ("An Inexpensive BRDF Model for Physically-based Rendering", Computer Graphics
  Forum 13(3), 1994); the highlight Blinn-Phong (J. F. Blinn, "Models of light reflection for computer synthesized
  pictures", SIGGRAPH 1977).
- **Where the spikes rise:** input 3's depth through `lib/glsl/depth_near.glsl` and `depth_find.glsl`. The height is
  read between the grid's cells by Catmull-Rom (`lib/glsl/common.glsl`), and the noise the spikes grow from uses Chris
  Wellons' lowbias32 integer hash ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain). The
  red guard (`lib/glsl/red_guard.glsl`) keeps reds short of WCAG's red flash line.
- **Beats from raw audio** (the library's audio input): a kick is a jump in the low band's loudness; the beat clock
  takes its tempo from the gaps between kicks, inter-onset-interval tempo induction, the idea behind S. Dixon,
  "Automatic Extraction of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed,
  not copied.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Ferrofluid before this one:** installations that drive real ferrofluid from TouchDesigner (Effet de Champ on the
  Derivative forum), and web shaders that draw ferrofluid spikes as cones on a fixed hexagonal grid with a Fresnel
  reflection (the Ferrofluid shader on shadcn.io; a paid Framer background). None takes a picture, and this effect
  follows none of them.

**Patents.** A search of US patents (November 2026) found none on simulating or drawing a ferrofluid, Rosensweig
spikes or a pattern-forming surface over a picture; the ferrofluid patents are hardware. Adobe's US 11,409,423 and
US 11,755,187 claim offering a menu of simulated phenomena (fluid, smoke, reaction-diffusion and others) to pick from
and apply to an image, and steering a simulation by pointing at the image: this effect runs one simulation, its Style
changes only how the liquid is drawn, and it takes no pointer or touch input. A pending Huawei application (US
2025/0117558) moves a phase field by a velocity worked out from it: the liquid's height here rises and falls in place
and is never carried along.

**Not used:** the two patents' methods above. A stronger hexagon term, which spread the spikes over the whole frame;
raw nearness as the field, which bristled the floor; and the spikes seen straight on as the default, which read as
beads.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
