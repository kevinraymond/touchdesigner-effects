# Relight

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. RELIGHT lights her and the warehouse again with violet, teal and amber lamps, the haze glowing lilac and her clothes catching the colors on their sides. SUN lights them with a low warm sun and a blue sky, the beams and walls of the warehouse standing out in relief. TWO TONE lights her amber from the left and blue from the right](relight.webp)

*Relight on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: at its defaults (Stage), with Look Sun, and with Look Two Tone. Each beat flares the lights.*

**New to relighting?** A picture already has its light baked in. To light it again you need its shape, and a depth map
gives one: how near each point of the picture is. Treat the depth as a surface standing out of the picture, and the
slope at each point says which way it faces. A light then brightens what faces it, leaves in shadow whatever something
nearer stands in front of, and glints where the surface mirrors it toward you. Not every surface is hard. Light goes
into skin, wax or marble, spreads and comes out again redder, and a thin part such as a finger's edge or an ear glows
when lit from behind. Film post-production calls this relighting, and phone portrait modes do a still version of it.

This effect relights your video live. Its own light is flattened, then colored lamps sweep over it on slow paths, each
casting shadows and highlights, their light spreading a little under the surface and glowing through thin parts. Each
beat of the music flares the lights and louder music brightens them. A depth map or mask on input 3 gives the shape.
Without one, the picture's brighter parts bulge a little, like a relief lit across. In TouchDesigner the nearest I
found is Prismatic's SSDR, a paid component that lights a depth map with physically based materials. Nothing free
relights a picture by its own depth with moving lights and shadows.

**[Download relight.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/relight.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `relight.tox` into your network. It shows TouchDesigner's sample picture of a banana under moving lights.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). The light then falls on the shapes in
   it, and nearer things cast shadows on what is behind them. A depth estimator such as Depth Anything gives one from
   any video. Without input 3 the picture's brighter parts stand in, which works best on faces and lit figures.
4. Wire music into input 2 (see Audio input). Each beat then flares the lights, and louder music brightens them.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `relight.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Relight page holds, top to bottom, the lights, the surface, how light passes under it, the music, input 3, then
Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Look | Stage | Which lights. Stage: violet, teal and amber lamps sweeping over the picture. Studio: a warm key light, a cool fill and a white light from above. Sun: a warm, low sun swinging slowly round, with long shadows, and a blue sky. Two Tone: amber from the left, blue from the right. |
| Brightness | 1 | How bright the lights are, 0 to 2. |
| Ambient | 0.1 | How much light reaches everything evenly, 0 to 1, so what no light reaches isn't black. |
| Height | 1 | How high the lights hang over the shapes, 0.25 to 2. Lower lights cast longer shadows and light the picture more unevenly. For Sun, how high the sun stands. |
| Speed | 1 | How fast the lights move, 0 to 3. At 0 they hold still. |
| Relief | 0.25 | How far what is nearest stands out of the picture, as a share of its height, 0 to 1: the depth of the shapes the light falls on. At 0 the picture is lit flat. |
| Roundness | 0.5 | How far the shapes round off at their edges, 0 to 1, so a figure cut out of a depth map lights like a relief rather than a flat cutout. |
| Flatten | 0.5 | How much of the picture's own light is taken out before the new lights light it, 0 to 1. Its bright parts are dimmed toward its average. |
| Shininess | 0.5 | How sharp the highlights are, 0 to 1, from broad and soft to small and glossy. |
| Specular | 1 | How bright the highlights are, 0 to 2. |
| Shadows | 1 | How dark the shadows are, 0 to 1. At 0 nothing casts one. |
| Softness | 0.5 | How soft the shadows' edges are, 0 to 1. |
| Occlusion | 0.5 | How much darker what lies below its surroundings is, 0 to 1: creases, folds and the gaps between fingers. |
| Scatter | 0.5 | How far light spreads under the surface before it comes out, 0 to 1, red furthest, as in skin, wax or marble. It softens the light and warms the edges of shadows. |
| Glow | 0.5 | How much light from behind comes through thin parts, 0 to 1, glowing red at the edges of fingers and ears. |
| Beat Kick | 0.5 | How bright a flare each beat on input 2 gives the lights, 0 to 1. Flashing limits how often. |
| Loudness | 0.5 | How much brighter louder music on input 2 makes the lights, 0 to 1. |
| Depth Type | Brighter Is Nearer | What input 3 holds, a depth map or a mask. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Bumps | 0.5 | With nothing on input 3, how far the picture's brighter parts bulge, 0 to 1, as the shape the light falls on. |
| Flashing | Calm | How often the beats may flare the lights. Off never, Calm at most once a second, Up to 3 per second the WCAG 2.3.1 limit, which no setting exceeds. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The looks

![Six views of a pair of hands held up against black, each named in the library's pixel font. INPUT is the clip and DEPTH MAP its depth, the hands white on black. STAGE lights them with pools of violet, teal and amber light that fall on the backdrop too. STUDIO lights them with a warm key light from above, their shadows soft on a gray backdrop. SUN lights them warm against a blue backdrop. TWO TONE lights them amber from the left and blue from the right](relight_looks.webp)

*A pair of hands with their depth map on input 3 and a song on input 2, in each look. Stage and Two Tone color the
light; Studio and Sun light the hands as a photographer or the sky would, Sun with a blue sky over everything.*

Each look is a set of up to four lights with their colors and paths. Stage's three colored lamps sweep widely over the
picture, so its colors move across everything. Studio's warm key light hangs high at the top left and barely moves,
with a dim cool fill at the right and a white light just above the picture's top, grazing it. Sun is a sun low in the
sky, swinging its heading slowly back and forth over half a minute, so its long shadows turn, and a faint blue sky
straight above lights what it doesn't. Two Tone holds an amber lamp at the left edge and a blue one at the right, each
swaying a little up and down. Height scales every lamp's height and the sun's elevation, Speed every path's pace, and
Brightness all their intensities.

## How it works

The depth becomes a height field at half the picture's size. Relief says how high the nearest point stands, as a share
of the picture's height. A depth map's 8-bit steps are smoothed finely, and Roundness averages the depth more broadly
with a triangle filter and mixes that in, only where it lowers the surface. So a figure's edges round off inward, while
the backdrop behind it stays down right up to its edge. A smoothing that spread outward left a slope of a few pixels
from a figure down to a wall meters behind it, and that slope shadowed itself into a black outline round every figure.
Each pixel's normal comes from the height's slope toward whichever neighbor is nearer in height, so a pixel at a depth
edge keeps the normal of its own side. Taking the cliff's sideways normal, the backdrop beside a figure lost the
backdrop's sheen and ringed the figure in black. The slope is held to at most 45 degrees, since a figure's own edges
are steep and, facing sideways, caught no light from lights in front. Without input 3, the picture's brightness, less
its broad average, stands in. A cheek, a brow or a lit arm bulges while a sky or a bright wall stays flat, and what is
darker than its surroundings stays on the plane (sunk, it dug a moat round everything bright). The picture's brightness
as a whole made a landscape's sky the nearest thing in it, and its finest detail made skin look pitted.

Each light is a lamp hanging at a height above the top of the relief, or a sun at an elevation. A lamp sways about its
place on a slow Lissajous path, two sines with their own periods, and a sun swings its heading the same way. The light
on each pixel is Lambert's diffuse, the cosine of the angle between the light and the normal, falling off with a
lamp's distance. The highlights are GGX's microfacet distribution with Smith's shadowing and Schlick's Fresnel, as
real-time engines draw a glossy plastic, the view straight down.

Each light's shadow comes from marching the height field from the pixel toward the light, at a quarter of the picture's
size. Each sample where the surface rises above the ray takes away some of the light, by how far it rises over how far
away it is, so a near occluder casts a sharp shadow and a far one a soft one, and the light the samples let through is
multiplied. The samples start a fraction of a step further on at each pixel, by Jorge Jimenez's interleaved gradient
noise, fixed in place, which turns the stepped edge of a long shadow into a fine grain that a small blur smooths away.

Ambient occlusion darkens what lies below what surrounds it, after Luft, Colditz and Deussen's unsharp masking of the
depth buffer: each pixel samples the height around it at three radii in eight directions and counts how far each rises.
A neighbor far higher is something standing in front, a dancer meters before the back wall, not a wall around the
pixel, so its rise counts only up to the radius and fades out by twice it, the range check screen-space occlusion
makes. Without it every figure wore a black halo.

Light scatters under the surface as Jimenez's separable subsurface scattering scatters it under skin: the diffuse light
is blurred across and then down, here by one Gaussian a color, red widest, and each blur follows the surface, so light
doesn't bleed across a depth edge. Light from behind a thin part comes through it, after Jimenez's skin translucency:
how far a pixel stands above the surface around it, as a share of its height, says how thin it is there, a finger more
than a palm, and the light grazing it from behind comes through redder the thicker it is. Both work the same on every
pixel.

The picture's own light is flattened before the new light falls on it. Where the picture is brighter than its average,
it is divided down toward it by its blurred brightness, or by its own brightness where that is lower, so a dark pixel
beside a bright one isn't dimmed with it. It is never lifted, since a video's darks are mostly noise and compression
blocks, and dividing them up posterized smoke into contours. The picture's colors, lit by the ambient and the lights
and darkened by the occlusion, plus the highlights, make the output. Bright light rolls off above 0.8 instead of
clipping, and every pixel goes through the red guard.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats and loudness, so each beat flares the lights and
the music's swells brighten them. Drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your
project and wire it into input 2. **Raw audio** (an Audio File In or Audio Device In CHOP) gives the beats and the
loudness from the sound itself. **TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the
loudness from its levels.

Each beat flares every light, up at once and fading over 0.6 s, as often as Flashing allows. The lights brighten with
the loudness, smoothed over a second.

**Nothing wired:** the lights keep moving, with no flares.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters and the dancer's depth on input 3. Each frame took 4.6 ms on the GPU (95th
percentile 5.6 ms) and 0.5 ms on the CPU, the median of three runs with the Mac otherwise idle. The shadows' march is
the largest part, about 2 ms for Stage's three lamps at a quarter of the picture's size (at half size it took about
1.2 ms more), then the lit picture about 0.4 ms and the scattering about 0.2 ms a pass. Looks with fewer lamps (Sun,
Two Tone) march fewer shadows. GPU times on this Mac wander from run to run as its GPU changes speed: an earlier build
measured 3.3 ms. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** A beat's flare brightens most of the picture at once, so the flares go through the Flashing setting:
  Off never flares, Calm (the default) at most once a second, and Up to 3 per second is WCAG's limit. A flare fades
  over 0.6 s. Fading over 0.35 s, three flares a second each fell all the way back, which measured 3.5 flashes a
  second on the dancer at Up to 3 per second, past WCAG's 3. Overlapping, they measured 2.0.
- **The lights' movement.** The lamps sweep slowly enough that their moving light adds no flashes: at Speed 3, the
  fastest, the dancer and the flowers measured their clips' own with Flashing Off.
- **The red guard.** Colored light on red flowers or skin moves reds across WCAG's saturated-red line, so every pixel
  goes through the red guard, which keeps reds just short of the line.
- **No meaning in color.** The effect signals nothing by hue. The looks' colors are decoration, and each look also
  differs in where its light falls and how hard its shadows are, which read by brightness. Two Tone is amber against
  blue, a colorblind-safe pair.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second) or a dance beat at 140 BPM, and counted the flashes in the worst second by WCAG's area
rule, and WCAG's red flashes separately. The clips with a depth map had it on input 3:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 2.0 | 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.5 | 3.0 | 1.0 |
| Red flowers against the sky (no depth map) | 1.0, red 0 | 1.5, red 0 | 1.5, red 0 | 1.0, red 1.0 |
| Koi in a black pond (no depth map) | 1.0, red 0 | 1.5, red 0 | 1.0, red 0 | 0.5, red 1.5 |
| People crossing a plaza (no depth map) | 0.5 | 1.5 | 1.5 | 0.5 |
| A pair of hands, 140 BPM | 1.0 | 1.0 | 1.5 | 1.5 |
| A walker, 140 BPM | 1.0 | 1.5 | 2.0 | 1.0 |
| Walkers with lanterns at night, 140 BPM | 0 | | | 0 |

With Flashing Off at 140 BPM, the looks and the far corners of the ranges measured the clip's own 1.0 each: Studio,
Sun and Two Tone on the dancer and on the flowers, Speed 3 on both, Height 0.25, Relief 1, and Brightness 2 with Two
Tone. Off adds nothing to any clip, Calm adds at most a flash a second, and Up to 3 per second reaches WCAG's 3 on the
dancer at 140 BPM and no further. The red guard took every red flash out, the clips' own included.

## Credits and license

MIT. The shaders and operators are written for this library, including the looks and the lights' paths, the depth
rounded inward and held to its edges, the occlusion's range check on Luft et al.'s unsharp mask, the thinness from the
height field, and the flares on the beat.

- **The light:** Lambert's diffuse; the GGX microfacet distribution (B. Walter, S. Marschner, H. Li and K. Torrance,
  "Microfacet Models for Refraction through Rough Surfaces", EGSR 2007) with Smith's shadowing and C. Schlick's Fresnel
  approximation (Computer Graphics Forum 13(3), 1994).
- **Ambient occlusion:** after T. Luft, C. Colditz and O. Deussen, "Image Enhancement by Unsharp Masking the Depth
  Buffer" (SIGGRAPH 2006), sampled, with screen-space ambient occlusion's range check.
- **Scattering and glow:** J. Jimenez, K. Zsolnai, A. Jarabo, C. Freude, T. Auzinger, X.-C. Wu, J. von der Pahlen,
  M. Wimmer and D. Gutierrez, "Separable Subsurface Scattering" (Computer Graphics Forum 34(6), 2015), here with one
  Gaussian a color; J. Jimenez, D. Whelan, V. Sundstedt and D. Gutierrez, "Real-Time Realistic Skin Translucency" (IEEE
  Computer Graphics and Applications 30(4), 2010).
- **The shadows' noise:** J. Jimenez's interleaved gradient noise, "Next Generation Post Processing in Call of Duty:
  Advanced Warfare" (SIGGRAPH 2014 course).
- **Input 3's depth** through `lib/glsl/depth_near.glsl`.
- **The red guard** (`lib/glsl/red_guard.glsl`) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan
  Processor, Voxel Space, Temporal Resonator and Caustics.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Relighting before this one:** Prismatic's SSDR for TouchDesigner (paid, Patreon) lights a depth map with physically
  based materials, and phone portrait modes relight still photos. This effect follows neither.

**Patents.** A search of US patents (October 2026) found many on relighting a picture by its depth, and the effect is
built around the active ones that came near. Canon's US 11,948,282 and US 11,106,938 claim shading a region found in a
picture so that pixels at the same distance with different normals change differently: nothing here finds or sets apart
any region, so skin isn't found by its color, and light scatters and glows the same on every pixel. Adobe's US
8,379,021 claims shadows on a height field from the highest point seen from each position: here a shadow multiplies the
light its samples let through and never looks for the highest. NVIDIA's US 8,064,726 claims rendering with a sum of
Gaussians: here the scattering is one Gaussian a color and the broad smoothings are triangle averages. Canon's US
11,037,279 claims adding several virtual lights' reflections onto the input picture: here the picture's own light is
replaced, never kept under the new. Google's US 10,916,051 and its family build a 3D mesh from the depth, and Google's
US 12,469,227 places a light where the user points: here there is no mesh, and the lights move on their own. Apple's US
11,669,985 lights a still photo with depth in response to a request to show it, and US 10,528,243 offers lighting
effects in a camera's picker: this is a video effect that runs continuously, and the Look menu is a parameter.

**Not used:** finding skin by its color (Chai and Ngan's YCrCb box) to scatter light only there, which the first builds
did before the patent search; d'Eon's multi-Gaussian skin profiles; and lifting the picture's darks while flattening
its own light, which turned a video's compression blocks and smoke into contours.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
