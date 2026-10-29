# Caustics

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. CAUSTICS shows her under rippling water, a net of bright wavy lines of light moving over the haze, the floor and her clothes. RAINBOW 1 is the same net with orange and blue fringes along its brightest lines. SIZE 0.05 makes the net fine, a mesh of small bright cells over the haze](caustics.webp)

*Caustics on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: at its defaults, with Rainbow 1, and with Size 0.05. Each beat drops a raindrop into the water.*

**New to caustics?** On a sunny day the floor of a swimming pool is covered in a moving net of bright lines. Each
ripple on the water is a weak lens. Where the surface bulges like a magnifying glass it gathers the sunlight into a
line, and where it dips it spreads the light thin, so the floor shows bright lines with dimmer patches between them.
Light focused that way is called a caustic. In 2009 Cem Yuksel and John Keyser showed how to compute caustics quickly
for water over a flat floor. Every point of the floor gathers the light from the patch of surface above it, each bit of
surface bending its light down through its own slope.

This effect makes your picture the floor of such a pool. Slow swells roll across the water, whatever moves in the
picture pushes it into wakes, and each beat of the music drops a raindrop into it. You see the floor through the moving
surface, so it wobbles under the waves, lit by the caustics and colored by the water on the way, deeper water bluer.
With a depth map on input 3, the water is shallower over what is nearer. In TouchDesigner I found water ripples (an MIT
`.tox` that ripples the picture) and caustics as tutorials and 3D scenes, but nothing that puts your picture under
water lit by caustics its own waves make.

**[Download caustics.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/caustics.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `caustics.tox` into your network. It shows TouchDesigner's sample movie of grass swaying in front of a
   building, under rolling water.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. A floor seen from above, such as a
   plaza, tiles or a table, looks most like a pool, and bright pictures show the caustics best.
3. Wire music into input 2 (see Audio input). Each beat then drops a raindrop into the water, and louder music raises
   the waves.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). The water is shallower over
   what is nearer, down to half of Depth over the nearest.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `caustics.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Caustics page holds, top to bottom, the water, the light, what disturbs the water, input 3, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Depth | 1 | How deep the water is, as a share of the picture's height, 0.25 to 2. The waves focus the light sharpest about Depth 1. Shallower water lights the floor more evenly, and deeper water crosses the lines into a busier net, bends the view further and colors it more. With a depth map or mask on input 3, nearer is shallower. |
| Waves | 1 | How high the water's waves are, 0 to 2. At 0 the swells are still, though wakes and drops still ripple the water. |
| Wind | 1 | How fast the swells roll, 0 to 3. At 0 they hold still. |
| Size | 0.12 | How long the swells are, as a share of the picture's width, 0.05 to 0.16. It is the size of the caustics' net. Longer swells are steeper too, so they still focus at the same depth. |
| Caustics | 0.5 | How much of the focused light shows, 0 to 1. At 1 the bright lines and the dark between them are as the water focuses them, and at 0 the floor is lit evenly. |
| Rainbow | 0 | How far the light's colors split as they bend, 0 to 1, giving the bright lines colored fringes, as sunlight through real water does faintly. |
| Refraction | 0.25 | How far the waves bend the view of the floor, 0 to 1, as a share of what the water would bend it. |
| Water Color | 0.18 | How much the water colors the floor, 0 to 1. It takes red first, so deeper water is bluer. |
| Wake | 0.5 | How hard whatever moves in the picture pushes the water, 0 to 1, leaving broad wakes behind it. |
| Beat Kick | 0.5 | How big a raindrop each beat on input 2 drops into the water, 0 to 1, somewhere new each time. |
| Loudness | 0.5 | How much higher louder music on input 2 raises the waves, 0 to 1. |
| Depth Type | Brighter Is Nearer | What input 3 holds, a depth map or a mask. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The water and the light

![Four views from above of people crossing a sunlit plaza, each named in the library's pixel font. INPUT is the clip. DEFAULTS shows the plaza as the floor of a pool, a net of bright lines of light over its pale tiles, tinted a little blue. DEPTH 0.5 is shallower water, the light soft and even, only faint lines. DEPTH 2 is deeper water, a busy net of crisp crossing lines, the floor bluer](caustics_looks.webp)

*People crossing a plaza with a song on input 2, at the defaults, in water half as deep, and in water twice as deep. The swells focus the light sharpest about Depth 1; shallower water lights the floor evenly and deeper water crosses the lines into a busier net.*

The water is a height field, a grid of heights a quarter of the picture's size, stepped once a frame by the damped wave
equation as Evan Wallace's WebGL Water steps it. Each point's motion is pulled toward its neighbors' average height and
damped, and a little viscosity smooths away the finest ripples first. Whatever moves in the picture pushes it, by how
much the picture changed since its last frame, spread into broad wakes. Each beat drops a raindrop into it, somewhere
new each time. On top lies a base sea of ten slow swells heading roughly the same way, their lengths spread about Size,
each moving as waves on deep water do, the longer ones faster. They are worked out every frame from the time, so the
pool is never still and never repeats.

The caustics are Yuksel and Keyser's. At half the picture's size, every sample of the surface refracts the sun's light
down to the floor through its own slope, and a square one pixel wide around where it lands lights the floor pixels it
overlaps, by how much of it each one covers. Over flat water every square lands on its own pixel, so the floor is lit
evenly. Where the surface curves, the squares crowd together into bright lines or spread apart into dim patches. The
paper gathers for each floor pixel the light from a window of surface around the point above it. Here a compute shader
does it a 16 by 16 patch of floor at a time, adding every square that lands in the patch from the surface within 16
pixels of it into a tally in fast shared memory. The squares stay one pixel wide whatever their rays do, and nothing is
carried from one frame to the next (see Patents below).

The floor is your picture seen straight down through the surface. The view bends through the surface's slope too, so
the floor wobbles under the waves, by Refraction of what the water's depth would bend it. The caustics need deep water
to focus, and a floor bent that far wouldn't read. The light the floor gets is the caustics at Caustics of their
strength, and the water on the way takes some of each color (red most, then green, then blue), more the deeper it is.
The sun glints on the surface where a wave tilts to mirror it up.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats and loudness, so each beat drops a raindrop and
the music's swells raise the waves. Drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your
project and wire it into input 2. **Raw audio** (an Audio File In or Audio Device In CHOP) gives the beats and the
loudness from the sound itself. **TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the
loudness from its levels.

Each beat pours a raindrop into the water for a tenth of a second, and its rings spread across the pool and fade. The
waves rise with the loudness, smoothed over a second.

**Nothing wired:** the swells roll and whatever moves makes wakes, with no drops.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters and the dancer's depth on input 3. Each frame took 2.2 ms on the GPU (95th
percentile 2.5 ms) and 0.4 ms on the CPU, the median of three runs with the Mac otherwise idle. The caustics themselves
take about 0.9 ms, the compute shader gathering a 640 x 360 map. Spreading the wakes takes 0.2 to 0.26 ms, the view
through the water 0.15 to 0.18 ms, and softening the depth 0.14 ms. Rainbow computes the light three times, once a
color. GPU times on this Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the output is
unused.

## Accessibility

- **No Flashing setting.** Caustics are bright lines that move, and on a bright floor every line that passes a spot
  is a change between light and dark there. How hard a wave focuses light goes with how sharply it curves, so short,
  steep ripples make the brightest, busiest lines for the least water. Raindrops falling all the time and the picture's
  change pushed into the water as it came made a fine grain of light that flashed 3 to 5 times a second where the clip
  has 1, in an offline test. So the water is kept to broad swells, broad wakes and broad drops. A drop on the beat with a
  radius a fifteenth of the picture's height added half a flash a second on the dancer, one a ninth across added none,
  and wakes half as broad as these added half a flash on flowers in the wind, where everything moves. Each beat's drop
  is a gentle swell spreading in rings, which the counter found adds nothing, so no Flashing setting rations them.
- **The red guard.** The moving light brightens and dims the floor's reds, which moves a red near WCAG's saturated-red
  line across it, so every pixel goes through the red guard, which keeps reds just short of the line.
- **No meaning in color.** The effect signals nothing by hue. The water's blue tint is a tint, and Rainbow's fringes
  are decoration on lines that read by their brightness.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, so 8 raindrops a second), a dance beat at 140 BPM, a song as raw audio, or no music, and
counted the flashes in the worst second by WCAG's area rule, and WCAG's red flashes separately. The clips with a depth
map had it on input 3:

| Clip and settings | Caustics | The clip alone |
|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 |
| Dancer, a song | 1.0 | 1.0 |
| Dancer, no music | 1.0 | 1.0 |
| People crossing a plaza | 1.0 | 0.5 |
| Plaza, 140 BPM | 1.0 | 0.5 |
| Red flowers against the sky | 1.0, red 0 | 1.0, red 1.0 |
| Flowers, 140 BPM | 1.0, red 0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 0 | 0.5, red 1.5 |
| Koi, 140 BPM | 1.0, red 0 | 0.5, red 1.5 |
| A pair of hands, 140 BPM | 1.0 | 1.5 |
| A walker, 140 BPM | 1.0 | 1.0 |
| Walkers with lanterns at night, 140 BPM | 0 | 0 |
| Dancer, 140 BPM, Rainbow 1 | 1.0 | 1.0 |
| Flowers, 140 BPM, Rainbow 1 | 1.0, red 0 | 1.0, red 1.0 |
| Dancer, 140 BPM, Beat Kick 1 | 1.0 | 1.0 |
| Dancer, 140 BPM, Wake 1 | 1.0 | 1.0 |
| Flowers, 140 BPM, Wake 1 | 1.0, red 0 | 1.0, red 1.0 |
| Dancer, 140 BPM, Size 0.05 | 1.0 | 1.0 |
| Plaza, 140 BPM, Size 0.05 | 0.5 | 0.5 |
| Dancer, 140 BPM, Size 0.16 | 1.0 | 1.0 |
| Dancer, 140 BPM, Depth 2 | 1.0 | 1.0 |
| Plaza, 140 BPM, Depth 2 | 1.0 | 0.5 |
| Dancer, 140 BPM, Waves 2 | 1.5 | 1.0 |
| Dancer, 140 BPM, Wind 2 | 1.5 | 1.0 |
| Dancer, 140 BPM, Caustics 1, Waves 2 | 1.5 | 1.0 |
| Plaza, 140 BPM, Caustics 1, Waves 2 | 1.5 | 0.5 |

Every row adds nothing to the clip's own flashes beyond the measurement's half-flash margin, which the plaza and the
koi reach at the defaults (a bright floor under moving light) and Waves 2 and Wind 2 reach on the dancer. The red guard
took every red flash out, the clips' own included. The last two rows are the far corner of the ranges, the light at
full strength on the highest waves, and they stay within half a flash of the clip too. A net finer than the counter's
cells (Size 0.05) averages out within each one.

## Experimental

- The cut that keeps a new shot from slamming the whole pool at once is found from how much the picture changes at
  once. A very fast pan can look like a cut, and then that frame makes no wake.

## Credits and license

MIT. The shaders and operators are written for this library, including the picture as the pool's floor, the swells,
the wakes and the drops on the beat, and the gather done a patch at a time in shared memory.

- **The caustics:** C. Yuksel and J. Keyser, "Fast Real-time Caustics from Height Fields" (The Visual Computer 25,
  2009), the light gathered from the surface above each point of a flat floor, a one-pixel square from each surface
  sample.
- **The water:** the damped wave equation as Evan Wallace's [WebGL Water](https://github.com/evanw/webgl-water) steps
  it (MIT, Copyright 2011 Evan Wallace). None of its rendering is used: it draws its caustics as a mesh, an approach
  this effect avoids (see Patents).
- **The water's color:** Beer-Lambert absorption, red first.
- **What moves:** the library's optical flow input (`lib/tox_build.py` optical_flow(): its luma and its cut detection),
  and input 3's depth through `lib/glsl/depth_near.glsl`.
- **The red guard** (`lib/glsl/red_guard.glsl`) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan
  Processor, Voxel Space and Temporal Resonator.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Water and caustics before this one:** exsstas's MIT `Wave_ripples.tox` ripples a picture, and caustics for
  TouchDesigner are tutorials (a GLSL one on alltd.org, a RayPOP 3D scene). Adobe After Effects has Caustics and Wave
  World effects. This effect follows none of them.

**Patents.** A search of US patents (October 2026) found several on caustics, and the effect is built around the active
ones. NVIDIA's US 11,830,125 claims caustics drawn as shapes at each ray's hit point, sized by how the ray spreads from
its neighbors: here every sample lands a square of the same size. NVIDIA's US 12,315,070 claims light particles whose
footprints update the particles for later frames: here the caustics come from each frame's water alone. NVIDIA's
US 11,010,963 needs a water mesh and a lighting mesh, and Samsung's US 10,127,711 particles with caustic textures joined
by lines, none of which this has. ByteDance's US 11,854,121 claims distorting a video by ripple maps picked from a
prepared sequence: this water is simulated live. ClearSpeed's US 6,809,729 has lapsed and Microsoft's US 6,985,148 has
expired.

**Not used:** raindrops falling all the time, and the picture's change pushed into the water as it came. Both make
short, steep ripples, which focus the light into a fine, fast-moving grain that hid the picture and flashed 3 to 5
times a second in an offline test. Broad swells and broad wakes keep to the clip's own flashes. Pushing the water's
speed instead of its height made bigger waves still.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
