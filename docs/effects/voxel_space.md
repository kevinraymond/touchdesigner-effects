# Voxel Space

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. FLY glides low down an avenue of pale mesas on a dark plain, each one the dancer's figure standing up out of the floor in the colors of her clothes, the stage light's pool glowing on the ground between them. ORBIT circles the whole picture as an island in a dark sea, her figure a tall draped ridge in the middle and the light's pool spreading across the plain beside it. HOVER looks across the picture from its near edge, her figure rising in front like a tall cloth sculpture](voxel_space.webp)

*The three flights at their defaults on the dancer, the clip top left, with its depth map on input 3 and a song on
input 2. Each beat dips the camera, at most once a second (Flashing at Calm).*

**New to Voxel Space?** In 1992 the helicopter game Comanche showed hills and valleys that looked solid, on computers
that could hardly draw a few hundred triangles a frame. Kyle Freeman at NovaLogic called the method Voxel Space. The
world was two pictures, a height map saying how tall the ground is at each point and a color map saying what color it
is. For each column of the screen the program stepped out from the camera across the two maps, and at each step drew a
strip in that step's color, as tall as its ground looked from that far away. Only the part rising above what was
already drawn in the column showed, so nearer hills hid the ones behind them. NovaLogic's later games, such as Delta
Force (1998), drew their landscapes the same way.

This effect does the same with your picture. Its colors are the land and its depth map (input 3) the hills, so a dancer
becomes a range of mountains in the colors of her clothes, moving as she moves, and the camera flies over them. With
nothing on input 3 the picture's brightness, softened, is the height, and its bright parts stand up as hills. A depth
map is brightest where the floor runs up to the camera, which would tilt the whole land into a ramp, so each row of the
picture is measured from its own far baseline. The floor and the far wall lie flat and whatever stands in front of them
stands up. The bass lifts the hills, each beat dips the camera and the tempo sets the pace. In TouchDesigner a terrain
from a picture is usually a grid of geometry displaced by it, or a height field raymarched in a shader (RayTK's tools,
a few files on the forum). I found nothing that draws it as Voxel Space did, a column at a time, and nothing that flies
it to music.

**[Download voxel_space.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/voxel_space.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `voxel_space.tox` into your network. It shows TouchDesigner's sample movie of mist over a lake as land, its
   bright mist and sky the hills, flown over slowly.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Optional: wire a depth map into input 3, grayscale and brighter nearer, such as a depth estimator's (Depth Anything)
   or a depth camera's (set Depth Type). People and things in front of the background become hills. Without it the
   picture's brightness, softened, is the height.
4. Optional: wire music into input 2 (see Audio input). The bass lifts the hills, the beats dip the camera and the
   tempo sets the pace.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `voxel_space.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Voxel Space page holds, top to bottom, the flight and the land, the music, the depth, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Flight | Fly | How the camera flies. Fly goes forward over the picture, repeated mirrored at its edges, weaving along the seam where it meets its mirror image, banking into its turns and keeping clear of the hills ahead, as the helicopter in Comanche flew. Orbit circles the picture as an island in a flat sea, looking down at it. Hover stands just off its near edge and looks across it, swaying from side to side. See [The flights](#the-flights). |
| Speed | 1 | How fast the camera flies, circles or sways, 0 to 2, faster with a faster tempo on input 2. At 1, Fly crosses the picture's height in about 20 seconds, Orbit circles it in about a minute and a half and Hover sways over about 20 seconds. 0 holds the camera still. |
| Height | 1 | How tall the hills stand, 0 to 2. At 1 the tallest is about a sixth of the picture's width. |
| Smooth | 0.4 | How rounded the hills are, 0 to 1. At 0 every edge of the depth stands as a cliff or a spire, and at 1 the hills roll gently. |
| Light | 0.7 | How much a low sun from the left shades the hills, 0 to 1. Flat ground keeps the picture's own colors. |
| Fog | 0.5 | How soon the distance fades into the sky, 0 to 1. At 0 only the farthest ground fades. |
| Bass Lift | 0.5 | How much the bass on input 2 lifts the hills, 0 to 1. The bass is smoothed over a second and lifts them further while it's above its usual level. |
| Beat Kick | 0.5 | How far each beat on input 2 dips the camera, 0 to 1. It drops over a quarter of a second and rises again over half a second, as often as Flashing allows. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away, in meters, counts as the far end of the depth. |
| Flashing | Calm | How often a beat may dip the camera. Off never dips it. Calm dips it at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The land

![Four views named in the library's pixel font. WALKERS is a clip of two hooded figures in raincoats walking down a brick alley toward the camera, and beside it FLY glides along the alley's brick wall, standing up as a ridge, with the walkers on either side as long mountains in their yellow and gray coats, smiley faces on top. KOI is a clip of orange and white fish in a black pond, and beside it FLY, with no depth map, makes the fish a field of orange and white peaks over dark valleys](voxel_space_looks.webp)

*Fly on two more clips with a song. The walkers with their depth map on input 3, the koi with nothing there, so the
picture's brightness is the height.*

The land is the picture, laid flat, 1024 units wide whatever its size. Its heights come from input 3 at half size, read
as nearness by Depth Type, or from the picture's brightness at a quarter size and blurred. Brightness is no depth, and
its fine detail, left sharp, bristled into spikes that shimmered in flight, so it stays in the land's colors. For each
row of it the effect finds the row's far baseline (its 12th percentile) and how far above that the row reaches (its
97th), and a line fitted down the rows smooths the baselines, so the floor's ramp is followed right to the picture's
edge. Each point's height is its nearness above its row's baseline. The tallest row's reach, eased over a second and a
half, sets the land's scale, so hills from a depth map, where people stand half the depth's range above the floor, and
from brightness, which uses all of it, come out about as tall. Smooth then rounds them. The baselines suit a scene with
a floor or a far wall behind its subject, as most have. A scene without one, such as a room seen close up, comes out in
soft terraces where a row's contents change from one row to the next.

The land moves slowly. Its heights and its colors both ease toward the picture's over a quarter of a second, so the
hills move with the land and a video's noise doesn't shake them. Seen in perspective, the near ground is the picture
enlarged, and a dancer's every turn, which changes little of the picture, swept large parts of the view between light
and dark. Where a depth camera got no reading, the heights stay where they were. A low sun from the left lights the
hills, as Comanche's maps had their light painted in, with flat ground at the picture's own brightness.

The view is drawn as Voxel Space drew it. For each column of the picture, 512 steps go out from the camera to about 2.4
times the picture's width, each a little longer than the last, and each step's ground is projected to the screen by
its distance. A column is drawn from the bottom up. A pixel shows the first step whose ground reaches it, and above
the last step drawn is the sky, colored from the picture's mean color. On a slope the pixel takes the land's color
between that step and the one before, where the ground crosses its row, so the far ground isn't striped by the steps.
On a cliff it takes the color of the cliff's top, as Comanche drew its cliff faces. Taken between the cliff's foot and
its top, a face showed a few pixels of the picture spread over hundreds of rows, and where a depth map's edge and the
picture's edge don't quite meet, it swung between the floor's dark and the dancer's light at her every move. The far
ground fades into the sky by Fog.

Comanche walked each column's steps one after another. Here a column is one workgroup of a compute shader. Each of its
512 invocations projects one step, a scan over the steps in shared memory gives the highest point drawn after each of
them, and each pixel finds its step by a binary search, since that highest point only ever rises.

## The flights

- **Fly.** The camera flies up the picture, which repeats mirrored at its edges, so its edges meet and the land goes on
  to the horizon. It weaves along the seam where the picture meets its mirror image, on a long path that repeats every
  sixteen pictures, so whatever stands in the middle of the picture passes on both sides at a distance, like an avenue,
  and it banks into its turns. Weaving about the middle itself, it brushed past the subject, a blurred wall filling
  half the view. It stays clear of the ground up to 650 units ahead, climbing slowly and sinking back more slowly
  still. At Speed 1 it covers 28 units a second, a slow glide. Faster, a bright and busy picture streamed past fast
  enough to flash (see Accessibility).
- **Orbit.** The camera circles the picture's middle, high, looking down at it. The picture is an island in a flat sea
  the color of the sky's shadow, and its heights fall to the sea along its shore.
- **Hover.** The camera stands just off the picture's near edge and looks across it, swaying from side to side over
  about 20 seconds. What stands at the front of the picture stands closest, often filling half the view.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends the seven bands from its feature bus. Run `fosfora
--signal --feat-bus`, drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and
wire it into input 2. Its beats dip the camera. Without the feature bus, its bass stands in for the low bands. **Raw
audio** (an Audio File In or Audio Device In CHOP) gives the bands and the beats from the sound itself.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the low bands from its low level.

The low end (the sub bass and the bass, averaged) is smoothed over a second and lifts the hills, more while it sits
above its usual level over the last 4 seconds, so the land swells as the music builds. Each beat dips the camera, down
over a quarter of a second and back up over half a second, as often as Flashing allows (once a second at Calm). The
tempo, counted over the last 6 seconds, sets the pace, from 0.75 to 1.3 times Speed with 120 BPM as 1, eased over 2
seconds.

**Nothing wired:** the camera flies at Speed, the hills stand at Height and nothing dips.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters and the dancer's depth map on input 3. Each frame took 2.2 ms on the GPU (95th
percentile 2.4 ms) and 0.49 ms on the CPU, the median of three runs with the Mac otherwise idle. Drawing the view takes
about 0.4 ms, for 1280 columns of 512 steps each. The rest goes to the land at half size (rounding it 0.34 ms, lighting
it 0.3 ms, its heights 0.23 ms and each row's baseline) and to easing the picture's colors (0.3 ms) and the view.
GPU times on this Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the output is
unused.

## Accessibility

- **Flashing.** A dip moves the whole view down and back up, which counts as flashing, so a beat dips the camera only
  through the standard flash gate. Off never dips it, Calm (the default) at most once a second, and Up to 3 per second
  is WCAG 2.3.1's limit.
- **Motion.** A flight moves the whole view, and moving land passes bright and dark ground through every part of it,
  each pass a change between light and dark. Seen in perspective the near ground is the picture enlarged, so the
  picture's own changes cover more of the view than in the picture: the picture lying flat, the camera still, flashed a
  second more than the clip, and the dancer's mesa up close two. What keeps it within the promises at the defaults: the
  land's heights and colors ease over a quarter of a second, cliff faces take the color of their tops, brightness
  standing in for depth is softened, the view itself eases over a tenth of a second (less while a beat dips the camera,
  which the gate already rations, since eased as much each dip smeared into a blur), the pace stays between 0.75 and
  1.3 of Speed, and Fly glides at 28 units a second (at 70, then 45, a plaza seen from above streamed past fast enough
  to add a flash a second). Faster settings were spot-checked (below).
- **The red guard.** Flown over, the land sweeps its reds back and forth, and red flowers that cross WCAG's
  saturated-red line once a second in the clip crossed it 3.5 times. Every pixel the effect shows goes through the
  library's red guard, which keeps reds just short of the line.
- **No meaning in color.** The effect signals nothing by hue. The land keeps the picture's colors, and its shape reads
  by light and shade.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully on and off 8 times a second), a dance beat at 140 BPM, a song as
raw audio, or no music, and counted the flashes in the worst second by WCAG's area rule, and WCAG's red flashes
separately. The dancer and the walkers have their depth maps on input 3. The flowers, the koi and the plaza have none,
so their brightness is the height:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 1.5 | 1.0 |
| Walkers in a brick alley | 1.0 | 1.0 | 1.5 | 1.0 |
| Red flowers against the sky | 1.0, red 0 | 1.5, red 0 | 2.0, red 0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 0 | 1.0, red 0 | 1.5, red 0 | 0.5, red 1.5 |
| People crossing a plaza, seen from above | 1.0 | 1.5 | 1.0 | 0.5 |
| Dancer, Orbit | 0.5 | 1.0 | 1.0 | 1.0 |
| Dancer, Hover | 1.0 | 1.5 | 1.5 | 1.0 |
| Plaza, Orbit | 0.5 | 1.0 | 1.0 | 0.5 |
| Plaza, Hover | 1.0 | 1.0 | 1.0 | 0.5 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 | 1.5 | 1.0 |
| Dancer, a song | 1.0 | 1.0 | 1.5 | 1.0 |
| Dancer, no music | 1.5 | 1.0 | 1.0 | 1.0 |
| Dancer, Beat Kick 1 | 1.0 | 1.5 | 1.5 | 1.0 |
| Dancer, Speed 2 | 1.0 | | | 1.0 |
| Plaza, Speed 2 | 1.0 | | | 0.5 |
| Dancer, Height 2 | 1.5 | | | 1.0 |

Every row keeps its setting's promise. Off adds nothing to the clip's own beyond the measurement's half-flash margin,
Calm adds at most one a second, and nothing passes WCAG's 3. The red guard took every red flash out, the clips' own
included. The plaza with Flashing Off, and the dancer with no music (where every setting is the same, since nothing
dips), sit at that margin. Rows that name no flight are Fly, the default. The last three rows are the far corners of
the ranges, measured with Flashing Off, since a corner moves the camera and the land, not the beat.

## Credits and license

MIT. The shaders and operators are written for this library, including each row's heights from its own far baseline,
the land's scale from its tallest row, the land easing as one, a workgroup a column with a binary search for each
pixel, the colors taken between steps and cliff faces in their tops' colors, the three flights, and the music's lift,
dip and pace.

- **Voxel Space:** Kyle G. Freeman and NovaLogic, *Comanche: Maximum Overkill* (1992; US patents 5,550,959 and
  6,020,893, both expired), the land drawn a screen column at a time, front to back, over a height map and a color map,
  only what rises above the highest point drawn so far in the column showing.
- **Sebastian Macke's write-up and code:** [s-macke/VoxelSpace](https://github.com/s-macke/VoxelSpace) (code MIT),
  followed for the method. None of its code is used, and none of Comanche's maps, which it excludes from its license.
- **The scan** over the steps: W. D. Hillis and G. L. Steele, "Data parallel algorithms" (Communications of the ACM
  29(12), 1986).
- **Input 3 as nearness** through the library's `lib/glsl/depth_near.glsl`, shared with Words, Pixel Art and others.
- **The red guard** (`lib/glsl/red_guard.glsl`) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan and Scan
  Processor.
- **The seven bands:** Fosfora's split (its `AUDIO-FEATURES.md`), measured from raw audio by the library's audio input
  (`lib/audio_callbacks.py`).
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** NovaLogic's patents on Voxel Space, US 5,550,959 and US 6,020,893, have both expired, as has Evans and
Sutherland's US 5,579,456 on rendering height fields. A search of US patents (October 2026) found none on land made
from a video frame, or land flown over and moved by music; Dan Neame's Audio Landscape and XMMS's terrain plugins did
the latter in the open years ago. Sony's US 10,198,848, active, claims a height map kept as a paged virtual texture and
drawn as a mesh, which this effect never does: it draws no geometry at all.

**Not used:** the depth map's own values as the heights. A depth map is brightest where the floor runs up to the
camera, and the land came out as one long ramp with a wall at its near edge. Also tried and set aside were easing only
the heights, which let the picture's colors run ahead of its hills and flashed more, and easing big changes faster
than small ones, which left a faint trace of each of a clip's frames that the light drew as lines.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
