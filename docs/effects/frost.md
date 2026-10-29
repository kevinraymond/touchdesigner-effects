# Frost

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. FERN covers the glass in front of her with gray-white fern frost, darker veins running between its fronds, glowing white where the stage light shines through, thawed in a ragged hole around her. STARS covers the dark room with crisp six-armed crystals of fine needles, larger on the right, a speckle of small ones in the light. DEW covers it with droplets of condensation, big ones with small ones between, bright where the light is behind them, clear around her](frost.webp)

*Frost on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: Fern (the default), Stars and Dew. The frost grows in from the frame and the edges of the room, and thaws around her and wherever she moves.*

**New to frost?** Frost on a cold window grows the way snow crystals grow in the air. Water freezing gives off heat.
An arm of ice that reaches a little ahead of its neighbors sheds that heat into colder air, so it grows faster still
and leaves them behind, and arms branch into ferns and six-armed stars. Physicists grow such crystals on a computer with
a phase field, a smooth map from air to ice whose edge moves wherever it is cold enough (Ryo Kobayashi's 1993 model is
the classic one), or with simple rules on a hexagonal grid (Clifford Reiter's, 2005). Glass that isn't cold enough for
ice gathers dew instead, droplets that grow and merge, which physicists call breath figures.

This effect grows that frost over your picture. Crystals start on the picture's edges and creep in from the frame
where the room behind is far or dark, and a fern's arms run along the edges they grow over. Whatever moves warms the
glass, and with a depth map or mask on input 3 so does what stands in front, so the frost thaws around a dancer and
grows back behind her. The ice blurs the picture behind it and glows where a light is behind it. In TouchDesigner I
found frosted-glass filters (a picture jittered behind static frosted glass) and diffusion-limited aggregation, but
nothing that grows ice over a live picture and thaws it where the picture moves.

**[Download frost.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/frost.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `frost.tox` into your network. It shows TouchDesigner's sample movie of a river running over rocks, and frost
   grows over it within a few seconds.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Frost shows best over a dark or distant
   background with something moving in front of it.
3. Optional: wire music into input 2 (see Audio input). Each beat then starts new crystals and makes the frost glint,
   and louder music grows it faster.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). The far room freezes first,
   and what stands in front (or is inside the mask) thaws the frost around it. Without it, the picture's brightness
   stands in for depth (dark freezes first), and only movement thaws.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset clears the glass, and the frost
grows back.

To update, delete your copy and drag in the new `frost.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Frost page holds, top to bottom, the frost, where it is cold and warm, the look, the music, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Style | Fern | Fern grows soft, branching ferns whose arms follow the picture's edges. Stars grows crisp six-armed stars of fine needles. Dew beads the glass with droplets that grow and merge. A new Style clears the glass. |
| Size | Medium | How big the crystals are, Fine, Medium or Coarse, each twice the last. The ice grows on a grid the picture's size, half or a quarter of it, so Fine draws the finest crystals and costs about four times Medium. |
| Growth | 1 | How fast the frost grows and thaws, 0.25 to 2. |
| Crystals | 0.5 | How many new crystals start each second on the picture's edges where it is cold, 0 to 1. In Dew, how quickly new droplets bead clear glass. |
| From the Rims | 0.5 | How much frost creeps in from the frame's edges, 0 to 1. Not used in Dew. |
| Follow Edges | 1 | How much a fern's arms turn to run along the picture's edges, 0 to 1. At 0 they all point one way. Fern only. |
| Reset | | Clears the glass. The frost grows back. |
| Freeze Evenly | 0.3 | At 0 only the far or dark parts of the picture freeze (the depth on input 3, else the picture's brightness), at 1 all of it alike. |
| Thaw by Movement | 0.7 | How much whatever moves warms the glass, 0 to 1, so the frost thaws there and grows back behind it. |
| Thaw by Nearness | 1 | How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the glass, 0 to 1. |
| Input 3 Holds | Depth Map | Depth Map: what stands in front of its surroundings warms the glass, while floors and walls don't count. Mask: what is inside the mask (white inside) warms it. |
| Sensitivity | 0.5 | How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask counts as inside. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Ice | 0.75 | How much the frost hides the picture behind it, 0 to 1. In Dew, how thick the haze is. |
| Glow | 0.6 | How much the light behind shows through the frost, 0 to 1, so it glows where a lamp is behind it. |
| Tint | 0.93, 0.97, 1 | The frost's color, a cold white. |
| Beat Crystals | 0.5 | How much each beat of input 2 adds, 0 to 1: new crystals along the picture's cold edges (in Dew, new droplets on the clear glass), a spurt of growth, and a glint on the frost's edges and sparkles. |
| Loudness | 0.5 | How much faster louder music on input 2 grows the frost (and quiet passages slower), 0 to 1. |
| Bass Thaw | 0.5 | How much the bass of input 2 warms what stands out in front, 0 to 1, so the frost backs away from it on the bass. Needs a depth map or mask on input 3. |
| Song Moments | On | With Fosfora's signal on input 2, a drop starts crystals all along the picture's edges at once (Fosfora's drop detection is experimental). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The three styles

**Fern** grows the ice as Kobayashi's phase field. A phase goes from 0 (the air at the glass) to 1 (ice) across a thin
interface, and the interface grows where the temperature is below the melting point, faster where it faces one of six
directions 60 degrees apart (ice's six-fold symmetry). Freezing gives off heat that warms the cells around it, and that
is what makes the arms: an arm reaching ahead sheds its heat into colder air and runs on, while the cells beside it,
warmed, fall behind. A little noise at the interface sets off side branches. The effect runs his model with his
constants on a grid half the picture's size, about ten steps a frame. As Ted Kim and Ming Lin steered it for artists
(2003), the six directions follow the picture's edges where it has clear ones, so the arms run along them. The glass
draws the heat out slowly toward its own temperature, colder where the room is far or dark: drawn out fast, the ice
grew in compact sheets that swallowed the frame. Where it has all frozen over, the arms (which froze first) are drawn
whiter than the ice that filled in between them, so the ferns still show, as they do on a real window.

**Stars** grows Reiter's snow crystals. Cells on a hexagonal lattice hold ice (1 or more) or water vapor (less). Ice
and its neighbors keep what they hold and gain a little more each step, and the vapor in the other cells spreads to
its neighbors, which is how ice draws the vapor toward itself and grows needle-like arms with side branches. Here the
glass also condenses new vapor where it is cold. The stars all lie on the one lattice, as the crystals of one grain of
ice would, and a new star starts only where the air is still moist: one started in the dry air around a grown star
stayed a lone speck.

**Dew** beads the glass with breath figures, as Daniel Beysens and Charles Knobler watched them form on cold glass
(1986). Droplets start on the clear glass, grow as it condenses water, and two that touch become one, with their volume
at their center of volume, which frees glass for new small droplets between the big ones. The effect keeps the
droplets in grids of cells, a grid for each size from 4 to 32 pixels, one droplet a cell, so a droplet only has to
look at the cells around it for those it touches, and a droplet that outgrows its cell moves up a size. Droplets too
small to see one by one make a milky haze. Each bigger one is a small lens: through it the picture behind shows shrunk
and turned over, its rim dark and a glint at its top.

**Cold and warm.** The glass is coldest where the room behind it is far, or with nothing on input 3, where the picture
is dark, so the room freezes first and bright or near things last. Whatever moves warms the glass at once and leaves it
to cool over a second and a half, and with a depth map or mask, what stands out in front (or is inside the mask) warms
it too. Warm glass melts the frost, starts no new crystals and dries Dew's droplets, and as soon as the warmth has gone
the frost grows back in from the ice around it. A faint warmth doesn't count: haze drifting through a dark room changes
the picture a little everywhere, and counted, it wore Stars' needles down to specks.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats, loudness, bass and drops. Drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw
audio** (an Audio File In or Audio Device In CHOP) gives the beats, the loudness and the bass from the sound itself.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the loudness from its levels.

Each beat starts new crystals along the picture's cold edges (in Dew, new droplets on the clear glass), makes the frost
grow in a spurt that frame, and makes its edges and sparkles glint for a fifth of a second. The frost grows faster when
the music is loud and slower when it is quiet, and the bass warms what stands out in front, so the frost backs away
from a dancer on the bass. With Fosfora's signal, a drop starts crystals all along the picture's edges at once. Frost
grows over seconds, so the music shows less in any one moment than in how much frost there is: on a song, about half
again as much of the picture frosted over (dev/reaction.py).

**Nothing wired:** the frost grows at its own pace.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, the dancer's depth on input 3 and a beat far busier than music on input 2. Each
frame took 2.5 ms on the GPU in Fern (95th percentile 4.6 ms), 2.8 ms in Stars (5.9 ms) and 2.6 ms in Dew (3.4 ms),
and 0.75, 0.73 and 0.51 ms on the CPU, the median of three runs each with the Mac otherwise idle. Fern's phase field
takes about 1.1 to 1.6 ms of it (ten steps of 13 reads a cell), Stars' lattice about 0.9 to 1.1 ms (twenty half-steps),
and Dew's lenses and droplets about 1.8 ms. Size Fine runs the ice on a grid four times as large and costs about four times as much. GPU times on this
Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **No Flashing setting.** Frost doesn't flash. Its crystals grow and thaw by edges that move a few pixels a frame, the
  glass warms in a fraction of a second and cools over a second and a half, a beat's new crystals are specks, and its
  glint brightens only thin edges and a few sparkles. None of that changes a large area between light and dark the way a
  flash does, so nothing rations it.
- **No meaning in color.** The effect signals nothing by hue. The frost is a cold white that reads by brightness.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second), or a dance beat at 140 BPM, and counted the flashes in the worst second by WCAG's area
rule, and WCAG's red flashes separately. The clips with a depth map had it on input 3:

| Clip and settings | Fern | Stars | Dew | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 | 1.0 | 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 | 1.0 | 1.0 |
| Dancer, the corners | 1.0 | 1.0 | 1.0 | 1.0 |
| Red flowers against the sky | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| People crossing a plaza | 0.5 | 0.5 | 0.5 | 0.5 |
| A pair of hands | 1.5 | 1.5 | 1.5 | 1.5 |
| Koi in a black pond | 1.0, red 1.0 | 0.5, red 1.5 | 0.5, red 1.5 | 0.5, red 1.5 |
| Koi, 140 BPM | 1.0, red 1.0 | | | 0.5, red 1.5 |

No row adds to the clip's own flashes beyond the measurement's half-flash margin, which Fern reaches on the koi: the
frost thaws where a fish swims and freezes over again behind it, a second or two later. Red flashes are the clips'
own, never more. The corners set every growth and music setting to its most (Growth 2, Crystals 1, From the Rims 1,
Beat Crystals 1, Loudness 1, Bass Thaw 1, Thaw by Movement 1, Ice 1, Glow 1).

## Experimental

- Raw audio's beat clock is experimental and can still add or miss beats, and Fosfora's drop detection is too.

## Credits and license

MIT. The shaders and operators are written for this library, including the picture as the glass's cold and warmth, the
glass drawing the heat away, warmth melting the ice, the droplets kept a grid a size, the frost's look, and the beat's
crystals, spurts and glints.

- **The Fern style:** R. Kobayashi, "Modeling and numerical simulations of dendritic crystal growth" (Physica D 63,
  1993), the phase field, its six-fold anisotropy, the latent heat and the noise that sets off side branches, with his
  constants. Steered as T. Kim and M. C. Lin steered it for artists, ["Visual Simulation of Ice Crystal
  Growth"](https://diglib.eg.org/handle/10.2312/SCA.SCA03.086-097) (SCA 2003): the arms' direction set over the picture.
- **The Stars style:** C. A. Reiter, "A local cellular model for snow crystal growth" (Chaos, Solitons and Fractals 23,
  2005), with his beta and gamma for needle-like arms.
- **The Dew style:** breath figures as D. Beysens and C. M. Knobler watched them form, "Growth of Breath Figures"
  (Physical Review Letters 57, 1986), and as D. Fritter, C. M. Knobler and D. Beysens simulated them, "Experiments and
  simulation of the growth of droplets on a surface (breath figures)" (Physical Review A 43, 1991): droplets that grow,
  merge into one at their center of volume when they touch, and leave clear glass for new ones.
- **The direction of the picture's edges:** the smoothed structure tensor (`lib/tox_build.py` structure_tensor(),
  shared with Paint, Reaction-Diffusion and Pencil), after J. E. Kyprianidis, H. Kang and J. Doellner, "Image and Video
  Abstraction by Anisotropic Kuwahara Filtering" (Pacific Graphics 2009).
- **What moves and what stands out:** the library's optical flow input (`optical_flow()`: its luma and its new-frame
  clock) and its warmth (`lib/glsl/warmth.glsl`, written for Frost), and input 3's depth through
  `lib/glsl/depth_near.glsl` and `depth_find.glsl`. Crystals and droplets start where Chris Wellons' lowbias32 integer
  hash says ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain).
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Frost before this one:** frosted-glass filters jitter a picture behind static frosted glass (ogrew's
  TD-PostEffectShader, MIT; the ISF collection), Noisemaker for TouchDesigner and ciphrd's CyclicDLA (MIT) grow
  diffusion-limited aggregates, and web components grow phase-field frost from a pane's frame with no picture. This
  effect follows none of them.

**Patents.** A search of US patents (October 2026) found none on growing frost or ice crystals over a picture, and the
methods it follows were published from 1986 to 2005. Two active patents clear frost or dew from a screen by touch:
Clipo's US 10,216,945 (a finger's trace clears a concealing image, which is redrawn after a set time) and Samsung's
US 11,150,775 (a frost or vapor layer over a picture, cleared where it is touched). This effect takes no touch or
pointer input, and cleared glass refreezes as the ice grows back from around it, never redrawn after a time. A pending
Huawei application (US 2025/0117558) moves a phase field by a velocity worked out from it: Frost's ice never moves.

**Not used:** frost cleared by touch (the two patents above). Drawing the heat out of Fern's ice fast, which grew
compact sheets, and many crystals at once, which crowded into coral. Warming the ice's temperature where something is
warm, which kept a thawed patch from refreezing for 10 seconds and more: warmth melts the ice instead.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
