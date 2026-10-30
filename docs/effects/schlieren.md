# Schlieren

![Six views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. KNIFE EDGE shows the warm air rising off her as gray relief, light on one side of each curl and dark on the other, as if carved, curling up past her outstretched arms and off the stage light. RAINBOW shows the same air in color, each curl's sides red, green and violet. SHADOWGRAPH draws its sharpest folds as bright and dark lines. INTERFEROGRAM lays straight white fringes across the warehouse, bent where the warm air rises. BACKDROP 0 is a schlieren photograph: an even gray field, the dancer and the stage light as black silhouettes, the rising air in gray relief around them](schlieren.webp)

*Schlieren on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: Knife Edge (the default), Rainbow, Shadowgraph, Interferogram, and Knife Edge with Backdrop at 0. The air she and the stage light warm rises in plumes that curl and puff up on the beats.*

**New to schlieren?** Warm air is invisible, but it bends light a little: air gets thinner as it warms, and light
slows less in it. A schlieren camera, invented by August Toepler in the 1860s, makes that bending visible. It lights
the scene with a beam brought to a focus and puts a blade at the focus, so light the air bent one way is cut off and
light it bent the other way gets through. The air then shows as gray relief, as if carved and lit from the side. That
is how photographs show the heat rising off a hand, a person's warm plume, a candle flame or a cough. A color filter in
place of the blade shows the bending as color, no blade at all shows the air's sharpest folds as bright and dark lines
(a shadowgraph), and light that went round the air, brought back to meet the light that went through it, shows it as
fringes (an interferogram).

This effect gives your picture that air. What stands in front in a depth map (or inside a mask), the picture's lights
and whatever moves warm the air above them. The warm air rises in a plume that sways and curls, and whatever moves
through it stirs it. The picture is seen through the air, shifted a little where it bends, and the subject stays
opaque, so the air shows around it, as it would through a real schlieren camera. The air is made up from the picture,
never measured: nothing here sees real heat. I found no schlieren effect for TouchDesigner, and the heat effects I
found color a picture as a thermal camera would.

**[Download schlieren.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/schlieren.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `schlieren.tox` into your network. It shows TouchDesigner's sample movie of grass in front of a building with a
   soft white light circling over it, and warm air rises off the light and trails behind it within a second.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Schlieren shows best with someone in
   front of a dark or plain background, and best of all with a depth map or mask on input 3.
3. Optional: wire music into input 2 (see Audio input). Each beat then puffs the warm air up, louder music heats it
   faster, and each bar turns the blade.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). What stands in front (or
   is inside the mask) warms the air above it and hides the air behind it. Without it, the picture's lights and
   whatever moves warm the air, and nothing is opaque.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset clears the air: no heat, and
still.

To update, delete your copy and drag in the new `schlieren.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Schlieren page holds, top to bottom, the look, the air, what warms it, the music, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Style | Knife Edge | Knife Edge shows the warm air as gray relief, lit from the side the blade faces. Rainbow shows it in color, the way the light bends picking the hue. Shadowgraph shows its sharpest folds as bright and dark lines. Interferogram lays straight fringes across the picture that the warm air bends. |
| Strength | 0.35 | How strongly the bending shows, 0 to 1. |
| Edge Angle | 0 | Which way the blade faces, in degrees. At 0 it stands upright and shows a plume's sides, at 90 it lies flat and shows its tops. In Rainbow it turns the colors. Knife Edge and Rainbow only. |
| Fringes | 10 | How many straight fringes the Interferogram lays across a frame height, 0 to 20. At 0 only the air's own fringes show, as contours of its heat. Interferogram only. |
| Backdrop | 1 | How much of the picture shows behind the air, 0 to 1. At 0 it is a schlieren photograph: an even gray field, the subject a dark silhouette, the air in relief on it. |
| Heat | 0.5 | How quickly warm things heat the air above them, 0 to 1. |
| Rise | 0.7 | How hard the warm air rises, 0 to 1. |
| Swirl | 0.5 | How much the air curls into eddies, 0 to 1. |
| Linger | 0.5 | How long the heat lasts once the air carries it away: at 0.5 it halves every 1.5 seconds, at 0 four times as fast, at 1 four times as slowly. |
| Stir | 1 | How much the picture's movement drags the air along, 0 to 2. |
| Reset | | Clears the air: no heat left, and still. |
| Warm by Movement | 0.75 | How much whatever moves warms the air, 0 to 1. It warms quickly and leaves the air to cool behind it. |
| Warm by Nearness | 1 | How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the air, 0 to 1. It also hides the air behind it. |
| Warm by Light | 0.5 | How much the picture's lights warm the air, as a lamp or a candle does, 0 to 1: what is bright and brighter than what is around it, so a bright sky isn't a light. A light hides the air behind it too. |
| Input 3 Holds | Depth Map | Depth Map: what stands in front of its surroundings warms the air, while floors and walls don't count. Mask: what is inside the mask (white inside) warms it. |
| Sensitivity | 0.5 | How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask counts as inside. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Beat Puffs | 0.5 | How hard each beat of input 2 puffs the warm air up, 0 to 1, so it rolls up into eddies. A puff moves a wide area at once, so it goes through the Flashing setting. |
| Loudness | 0.5 | How much faster louder music on input 2 heats the air (and quiet passages slower), 0 to 1. |
| Band Heights | 0.5 | How much each of the music's seven bands heats its own height of the frame, the lowest at the bottom and the highest at the top, 0 to 1. |
| Bar Turn | 45 | How far each bar of input 2 turns the blade, in degrees, 0 to 90. It turns at most once every 2 seconds, over a second and a half. Knife Edge and Rainbow only. |
| Song Moments | On | With Fosfora's signal on input 2, a drop sends up a big puff (Fosfora's drop detection is experimental). |
| Flashing | Calm | How often the beat's puffs may come. Off: never. Calm: at most once a second. Up to 3 per second: the WCAG 2.3.1 limit. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The four styles

**Knife Edge** is the classic schlieren view. The heat stands for the warm air summed along each ray of light, so the
light bends by minus its gradient. The blade lets through light bent toward the side it faces and cuts off light bent
away, so each side of a plume is lit or shaded, and the picture shows the air as relief added to the picture behind
it. Where the air bends the light hard, the relief saturates, as a real blade's cutoff does. Added rather than
multiplied, the relief stays visible over a dark room: multiplied, as a real camera's light is, it vanished there.

**Rainbow** puts a color filter in place of the blade, as Rheinberg's color schlieren does. The way the light bends
picks a color on a wheel of the spectrum, red through violet with the purples closing it (the CIE color matching
functions as Wyman, Sloan and Shirley fit them), and how hard it bends sets how much color shows, so a plume's sides
come out in different colors. Edge Angle turns the wheel.

**Shadowgraph** has no blade. Light gathers where the bending converges and leaves where it spreads, which is the
Laplacian of the heat, so the air's sharpest folds show as bright and dark lines, like light on the bottom of a pool.

**Interferogram** lays straight fringes across the picture, as an interferometer does when its two beams meet at a
slight tilt, and the warm air, slowing the light that crosses it, bends them around the plume. Fringes sets how many
cross a frame height. At 0 there is no tilt, and the fringes are the heat's own contours.

**Backdrop** at 0 turns any style into a schlieren photograph: an even gray field where the blade cuts off half the
light, the subject and the lights as dark silhouettes, and the air on the gray.

## The air

The air runs as a small fluid simulation on a grid a quarter of the picture's size: Jos Stam's stable fluids (1999),
as Mark Harris laid them out for the GPU, with vorticity confinement keeping its eddies alive and a pressure solve (20
passes a frame) keeping it from piling up. It rises in a column above whatever is warm, the lift falling off with
height, and slow noise drifting up through the lift makes the column sway and break into eddies. The picture's
movement drags the air along where something moves, so a hand sweeping through the plume leaves a wake. The air never
goes faster than 0.4 frame heights a second: real plumes rise a few tenths of a meter a second.

The heat the air carries lives on a grid half the picture's size, finer than the air's, so the plume's edges stay sharp.
It is carried by MacCormack's step (Selle and his colleagues' unconditionally stable form, 2008), which corrects the
plain step back along the air by half the error a step back and forth makes, and keeps the result within the cells it
came from. A plain step back blurred the heat a little every frame, and the edges are what the camera sees. Where the
picture is warm, the heat rises toward how warm it is, and once carried away it cools as it mixes into the room.

What warms the air comes from the picture. With a depth map or mask on input 3, what stands in front of its
surroundings (or is inside the mask) warms it. Whatever moves warms it quickly and leaves it to cool over a second and
a half, though a faint movement, such as haze drifting through a dark room, doesn't count. The picture's lights warm
it too, as long as they are bright and brighter than what is around them. That warmth is smoothed and its edge
sharpened, so the air above a warm thing has an edge to see. Unsmoothed, the movement's coarse cells came out as a
grid of bumps in the heat.

Two things keep the air honest to the picture. The air rises above the picture's warmth, which is made afresh every
frame, and the heat it carries never pushes it. And the subject and the lights are opaque, so the air shows around
them rather than over them, as through a real camera. Relief drawn over the subject striped it, and a lamp's bright
point, shifted back and forth by the air over it on a beat, flashed the cells around it.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats, bars, loudness, bands and drops. Drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw
audio** (an Audio File In or Audio Device In CHOP) gives the beats, bars, loudness and bands from the sound itself.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the loudness and bands from its
levels.

Each beat puffs the warm air up at once, so it rolls up into eddies and heats faster for a moment, as often as Flashing
allows. A puff is full strength while a small share of the picture is warm (a person, a hand) and weaker where more of
it is, so it never heaves the whole frame's air at once: flowers swaying in the wind, all warm, flashed whole on every
puff. Louder music heats the air faster and quiet passages slower. Each of the seven bands, from the lowest bass to the
highest cymbals, heats its own height of the frame, so the bass warms the feet and the cymbals the head. Each bar turns
the blade a little, at most once every 2 seconds and over a second and a half, so the light and dark sides of the
relief swap slowly. With Fosfora's signal, a drop sends up a big puff.

**Nothing wired:** the air rises at its own pace.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, the dancer's depth on input 3 and a beat far busier than music on input 2. Each
frame took 3.1 ms on the GPU (95th percentile 4.1 ms) and 0.74 ms on the CPU, the median of three runs with the Mac
otherwise idle. The picture's optical flow takes about 0.6 ms of it, the pressure solve about 0.6 ms and the look
about 0.6 ms. GPU times on this Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the
output is unused.

## Accessibility

- **Flashing setting.** A beat's puff throws the warm air up over a wide area at once, so puffs go through the
  standard Flashing setting: Off never puffs, Calm (the default) at most once a second, Up to 3 per second at most three
  times. The air's own motion needs no rationing at the defaults: it is slow, and the relief over it moves smoothly.
- **No meaning in color.** The effect signals nothing by hue. Rainbow's colors come with the relief's brightness, and
  every pixel goes through the library's red guard, which keeps reds short of WCAG's saturated-red line.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second) and counted the flashes in the worst second by WCAG's area rule at Off, Calm and Up to 3
per second, and WCAG's red flashes separately. The dancer and the hands had their depth maps on input 3:

| Clip | Knife Edge (the default) | Rainbow | Shadowgraph | Interferogram | The clip alone |
|---|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 | 1.0, 1.0, 1.0 | 1.0 |
| Red flowers in the wind | 1.0, 2.0, 2.5 | | | | 1.0, red 1.0 |
| People crossing a plaza | 1.0, 1.5, 1.5 | | | | 0.5 |
| A pair of hands | 1.5, 1.5, 1.5 | | | | 1.5 |
| Koi in a black pond | 1.0, 1.0, 1.0 | | | | 0.5, red 1.5 |

Every row is within its setting's rule. Up to 3 per second never exceeds WCAG's 3, Calm adds at most one flash a second
to the clip's own, and Off adds none beyond the measurement's half-flash margin, which the plaza and the koi reach. The
effect adds no red flashes, and the red guard also takes away the clips' own.

The far corners were spot-checked on the busiest clip, red flowers swaying in the wind, which warm the air all over.
Strength, Rise and Beat Puffs at 1 each stay within their rules on their own. All three at 1 together measured 2.0, 3.5
and 3.5 (Off, Calm, Up to 3 per second), half a flash a second over WCAG's 3, so keep at least one of them lower on
footage that moves all over. Two limits keep the corners that close. The air's speed is capped at 0.4 frame heights a
second, and Rise at 1 lifts it half as hard as the first build did, whose lift churned the air into eddies that flashed
1.5 times a second over the clip with Flashing Off. And the blade turns at most once every 2 seconds: turned on every
bar of the test beat, two a second, the relief swept from light to dark and back half a flash a second more often than
the clip.

## Experimental

- Raw audio's beat clock is experimental and can still add or miss beats, and Fosfora's drop detection is too.

## Credits and license

MIT. The shaders and operators are written for this library, including the picture as the source of the heat, the
rising column above what is warm, the subject and the lights kept opaque, the gray schlieren photograph as a backdrop,
the beat's puffs and the bands by height.

- **Schlieren and shadowgraph optics:** G. S. Settles, *Schlieren and Shadowgraph Techniques: Visualizing Phenomena in
  Transparent Media* (Springer, 2001), [doi:10.1007/978-3-642-56640-0](https://doi.org/10.1007/978-3-642-56640-0): how
  warm air bends light, the knife edge's relief and its cutoff, color schlieren with a Rheinberg filter, and the
  shadowgraph as the bending's convergence.
- **The four looks from a simulated field:** C. Brownlee, V. Pegoraro, S. Shankar, P. McCormick and C. Hansen,
  ["Physically-Based Interactive Flow Visualization Based on Schlieren and Interferometry Experimental
  Techniques"](https://doi.org/10.1109/TVCG.2010.255) (IEEE TVCG 17(11), 2011), whose shadowgraph, schlieren, color
  filter and interferometry views this follows in two dimensions. Followed, not copied.
- **The air:** J. Stam, "Stable Fluids" (SIGGRAPH 1999), as M. Harris laid it out for the GPU, "Fast Fluid Dynamics
  Simulation on the GPU" (GPU Gems, ch. 38, 2004), its pressure solve shared with Fluid (`incompressible()`); vorticity
  confinement from R. Fedkiw, J. Stam and H. W. Jensen, "Visual Simulation of Smoke" (SIGGRAPH 2001).
- **The heat's step:** A. Selle, R. Fedkiw, B. Kim, Y. Liu and J. Rossignac, "An Unconditionally Stable MacCormack
  Method" (Journal of Scientific Computing 35, 2008), with their clamp.
- **Rainbow's colors:** the CIE 1931 color matching functions as C. Wyman, P.-P. Sloan and P. Shirley fit them,
  ["Simple Analytic Approximations to the CIE XYZ Color Matching Functions"](https://jcgt.org/published/0002/02/01/)
  (JCGT 2(2), 2013), shared with Lens Flare (`lib/glsl/spectrum.glsl`). The red guard (`lib/glsl/red_guard.glsl`) is
  the library's own.
- **What warms the air:** the library's warmth (`warmth()`, shared with Frost), its optical flow (`optical_flow()` and
  `flow_speed()`, shared with Datamosh, Fluid and others) and its depth reading (`lib/glsl/depth_near.glsl` and
  `depth_find.glsl`). The noise that sways the lift uses Chris Wellons' lowbias32 integer hash
  ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain), and the bending is resampled
  Catmull-Rom (`lib/glsl/common.glsl`).
- **Beats from raw audio:** the library's audio input finds a kick as a jump in the low band's loudness, and its beat
  clock takes its tempo from the gaps between kicks, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat
  from Expressive Performances" (Journal of New Music Research, 2001). Followed, not copied.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Schlieren before this one:** Brownlee and his colleagues rendered these views of simulated fields for science, and
  heat-haze shaders wobble a picture behind hot air without showing the air. I found no schlieren effect for a live
  picture in TouchDesigner, and this effect follows no earlier one.

**Patents.** A search of US patents (October 2026) found none on a schlieren, shadowgraph, color schlieren or
interferogram view of a made-up field over a picture, and the optics and methods it follows were published from the
1860s to 2013. Active patents near it set what it doesn't do. MIT's US 9,710,917 and US 10,636,149 measure real air
from how a textured background seems to move behind it: this effect measures nothing, and treats the picture's
movement as things moving, never as air bending light. ByteDance's US 12,694,597 shows a fluid's color carried by a
plain step back along its speed: the heat here is never shown as a color, only by how it bends the light, and it is
carried by MacCormack's corrected step. ByteDance's US 12,182,906 moves a fluid by a detected object's change of speed:
nothing here is detected or tracked, and movement drags the air only as the whole picture's optical flow. A pending
Huawei application, US 2025/0117558, works out a velocity from the very density it carries: here the air rises above
the picture's warmth, made afresh every frame, and the heat it carries never pushes it.

**Not used:** measuring real air from a camera's view (the two MIT patents), a dye displayed and carried on a fluid
(ByteDance's US 12,694,597), a fluid moved by a tracked object (ByteDance's US 12,182,906), and a velocity from the
carried density (Huawei's application). Also tried and set aside: relief multiplied into the picture, which vanished
over a dark room; noise on the heating, which striped the subject; the heat carried by a plain step back, which blurred
its edges; and lift twice as strong, which flashed over flowers in the wind.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
