# Detail

![Two views of a woman laughing against a dark background side by side, each named in the library's pixel font. On the left, INPUT, the clip. On the right, DETAIL, the same laugh with every crease, pore and strand of hair standing out more clearly, the shading of her face deeper, her edges as clean as in the clip and no halo around her, crisper still for a moment when the music hits](detail.webp)

*The defaults on a laughing face, the clip on the left, with a song on input 2. The fine detail is twice as strong
and the edges stay as they were, and on a beat it jumps stronger for a moment, at most once a second (Flashing at
Calm).*

**New to local contrast?** Local contrast is the difference in brightness between a small thing and what lies right
around it, such as a wrinkle against the skin beside it, a leaf against its neighbors or a wisp of smoke against the haze. Turn
it up and a picture turns crisp and textured, the "HDR look" of so many landscape photos. The usual way to turn it up,
sharpening or a high pass, can't tell texture from an edge, so it boosts both, and every edge gets a bright or dark
outline, a halo. A local Laplacian filter tells them apart by how large a step in brightness is. Small steps are
detail, and they change; large ones are edges, and they stay put. Sylvain Paris, Samuel Hasinoff and Jan Kautz described
it in 2011, and a faster form followed in 2014. It works on the picture split into octaves of detail, a Laplacian
pyramid, and builds each octave of the result from the picture remapped around the brightness found there. So it
boosts texture without halos, or smooths it away while the edges stay sharp, and it can also flatten or deepen the
picture's large changes of light.

This effect runs the fast form live. Detail makes the fine detail stronger, or below 0 smooths it away while edges
stay sharp, which turns a face into wax and a street into a painting. Tone flattens the picture's big changes of light
(the shadows open, the highlights come down) or deepens them, while the detail stays. Edge Contrast says how large a
step in brightness counts as an edge, and Noise Floor keeps a video's noise and compression blocks from being boosted
with its detail. The music on input 2 makes the detail jump on the beats and swell when it gets loud, and a depth map
or mask on input 3 keeps the change to near things. With Detail at 0 and Tone at 1 the picture comes back exactly as
it was. I found no edge-aware local contrast for TouchDesigner, whose own TOPs sharpen or blur the same way
everywhere, edges included.

**[Download detail.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/detail.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `detail.tox` into your network. It shows TouchDesigner's sample movie of a tree against the light, its detail
   twice as strong.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Pictures full of texture show it best,
   such as faces, leaves and bark, stone, fabric, smoke and water. A plain or very dark picture has little detail to
   bring out.
3. Optional: wire music into input 2 (see Audio input). The detail then jumps on the beats and swells when it gets
   loud.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside). Depth Focus then keeps
   the change to near things, or to what lies inside the mask, while the rest stays as it was. Without it the whole
   picture changes.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `detail.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Detail page holds, top to bottom, the filter, the music, depth, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Detail | 1 | How much stronger the fine detail gets, -1 to 3. At 0 it stays as it is, at 1 it is twice as strong and at 3 four times. Below 0 it smooths away, and at -1 it is gone while the edges stay sharp. See [The look](#the-look). |
| Tone | 1 | How large the picture's big changes of light stay, 0 to 2. At 1 they are as they were. Lower flattens them, so the shadows open and the highlights come down, and higher deepens them. The detail stays either way. |
| Edge Contrast | 0.2 | How large a step in brightness counts as an edge rather than as detail, 0.1 to 0.5 of the way from black to white. Edges are kept as they are (or scaled by Tone). Higher lets Detail reach larger features, such as the shading of a face; lower keeps it to fine texture. |
| Noise Floor | 0.015 | While Detail boosts, detail fainter than this (of black to white) is left nearly as it is, so a video's noise and compression blocks don't grow with the detail, 0 to 0.05. At 0 everything is boosted. Smoothing (Detail below 0) smooths the noise too. |
| Beat Kick | 0.5 | How much the detail jumps on each beat of input 2, 0 to 1. At 1, Detail is 2 higher for a moment, easing back over 0.3 seconds. It jumps as often as Flashing allows. |
| Loudness | 0.5 | How much the detail swells as the music on input 2 gets louder than it has been over the last 4 seconds, and eases as it quietens, 0 to 1. It is smoothed over a second. At 1, music 0.25 louder than usual adds 1 to Detail. |
| Depth Focus | 0.5 | With a depth map or mask on input 3, how much the change is kept to near things, or to what lies inside the mask, 0 to 1. At 1 far things stay as they are. Nothing changes without input 3. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators (Depth Anything) and masks. Distance 0-1 suits the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away, in meters, counts as the far end of the depth. |
| Flashing | Calm | How often the beats may make the detail jump. Off never does, so only Loudness moves it, smoothly. Calm jumps at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The look

![Five views of the same laughing face, each named in the library's pixel font. INPUT is the clip. DETAIL 2 brings out every wrinkle and pore, gritty and hyperreal. DETAIL -1 smooths her skin to wax while her eyes, teeth and outline stay sharp. TONE 0.4 flattens the light on her face, its shading softer and its texture as crisp as at the defaults. TONE 1.6 deepens it, her shading darker and her highlights brighter](detail_looks.webp)

*The same face with no music: Detail at 2 and at -1, then Tone at 0.4 and at 1.6, the other settings at their
defaults.*

Detail and Tone are the filter's two curves. Each octave of the result is taken from the picture remapped around the
brightness found there, and the remapping multiplies the small differences from that brightness (closer than about
Edge Contrast) by 1 plus Detail and the large ones by Tone. So a crease in a cheek, a few levels darker than the skin
around it, is boosted, while the edge of the face against the dark background, a step far larger than Edge Contrast, is
kept. A sharpening filter would boost that edge as well and draw a halo along it.

Detail above 0 gives the hyperreal look, gritty at 2 and more. Below 0 it gives the opposite, a smooth, painted or
waxy picture whose edges are still crisp, as if airbrushed; at -1 most texture is gone. Tone below 1 flattens the
light the way a photo's tone mapping does, opening the shadows without a halo where they meet the light. Above 1 it
deepens the light, darker shading and brighter highlights. Together, a high Detail and a low Tone give the classic
tone-mapped "HDR" look. Edge Contrast moves the line between the two. At 0.5 the shading of a whole face counts as
detail and is boosted with the texture, which can turn heavy. At 0.1 only fine texture changes.

The overall light of the picture, the smallest octave, never changes, and the colors stay as they were, since the
filter works on the brightness alone and adds its change to every channel.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)'s signal** gives the beats and the loudness. Drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. The
loudness is its bass, which swells with each beat and between passages. **Raw audio** (an Audio File In or Audio
Device In CHOP) gives them from the sound itself, a beat on each kick, kept to the tempo once the kicks keep one.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the loudness from its low band.

Each beat makes Detail jump up by Beat Kick times 2 and ease back over 0.3 seconds, as often as Flashing allows (once
a second at Calm, so it follows every other beat or so of a dance track). The loudness is smoothed over a second and
judged against its usual level, its average over the last 4 seconds, so a loud mix doesn't leave the picture crunchy
and a quiet one flat. Music louder than usual adds Loudness times 4 times the difference to Detail, at most 1 either
way, so a swell sharpens the picture and a breakdown softens it. With Detail at -1, a beat brings the texture back for
a moment through the smoothed picture.

**Nothing wired:** Detail and Tone alone.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 2.9 ms on the GPU (95th percentile 3.8 ms) and 0.7 ms on the
CPU, the median of three runs with the Mac otherwise idle. The filter keeps eight remapped copies of the picture's
brightness, four to a 32-bit float texture, and builds seven octaves of each. Every octave is a quarter the size of
the one above, so a pyramid's seven octaves together are about a third the size of the picture, and only four passes
run at full size: the brightness, the two sets of copies and the last, which gives the picture. Eight copies came within 37 dB of 64 at
the lowest Edge Contrast and within 44 dB at 0.3, past the 30 dB the fast filter's authors found invisible. With raw
audio on input 2, measuring it raises the CPU time to about 1.0 ms. GPU times on this Mac wander from run to run as
its GPU changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** Making the detail jump on every hit counts as flashing, as Video Vocoder's octaves showed: pumping
  detail swings each area between crisp and soft, even detail finer than the test's cells. So a beat reaches the
  detail only through the standard flash gate. Off never jumps, and only Loudness moves the detail, smoothly, over a
  second. Calm (the default) jumps at most once a second, and Up to 3 per second is WCAG 2.3.1's limit.
- **Its own contrast.** Boosting detail also boosts what a clip changes by itself. The koi's ripples measured 1.0
  flashes a second with Flashing Off against the clip's 0.5, within the half flash a second the count allows for
  measuring noise. The red flowers kept the clip's own red flashes with Flashing Off and at Calm, so there is no red
  guard.
- **Noise Floor.** A video's frame-to-frame noise, boosted, would shimmer. Noise Floor leaves detail fainter than it
  nearly as it was while Detail boosts (smoothing smooths the noise too).
- **No meaning in color.** The effect signals nothing by hue; it shows the picture's own colors, its detail stronger or
  weaker.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second), a dance beat at 140 BPM, a song as raw audio, or no music, and counted the flashes in the
worst second by WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 | 1.0 | 1.0 |
| People crossing a plaza | 0.5 | 0.5 | 1.0 | 0.5 |
| Red flowers against the sky | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.5 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 2.5 | 0.5, red 1.5 |
| A laughing face | 0.5 | 1.0 | 1.0 | 0.5 |
| Walkers with lanterns at night | 0 | 0 | 0 | 0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, 140 BPM | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.5 | 1.0, red 1.0 |
| Koi, 140 BPM | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 2.0 | 0.5, red 1.5 |
| Face, 140 BPM | 0.5 | 1.0 | 1.0 | 0.5 |
| Dancer, a song | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, a song | 1.0, red 1.0 | 1.0, red 1.0 | 1.5, red 1.5 | 1.0, red 1.0 |
| Koi, a song | 1.0, red 1.5 | 1.0, red 1.5 | 1.0, red 2.0 | 0.5, red 1.5 |
| Dancer, no music | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, no music | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Flowers, 140 BPM, Detail -1, Beat Kick 1 | 1.0, red 1.0 | 1.0, red 1.5 | 2.5, red 2.0 | 1.0, red 1.0 |
| Face, 140 BPM, Detail -1, Beat Kick 1 | 0.5 | 1.0 | 2.5 | 0.5 |
| Flowers, 140 BPM, Detail 3, Edge Contrast 0.5, Beat Kick 1, Loudness 1 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Face, 140 BPM, Detail 3, Edge Contrast 0.5, Tone 2, Beat Kick 1, Loudness 1 | 1.0 | 1.0 | 1.0 | 0.5 |

Every row keeps its setting's promise. Off adds nothing to the clip's own beyond the measurement's half-flash margin,
Calm adds at most one a second, and nothing passes WCAG's 3. The last four rows are far corners of the ranges. The
largest jump is from a smoothed picture (Detail -1) to a crisp one on each beat, which at Up to 3 per second flashes
as often as that setting allows.

## Credits and license

MIT. The shaders and operators are written for this library, including the eight copies packed four to a texture,
Noise Floor as coring in the collapse, the beat's jump through the flash gate and the loudness against its usual level.

- **The filter:** S. Paris, S. W. Hasinoff and J. Kautz, ["Local Laplacian Filters: Edge-aware Image Processing with a
  Laplacian Pyramid"](https://doi.org/10.1145/2010324.1964963) (ACM SIGGRAPH 2011, ACM Transactions on
  Graphics 30(4)): each output coefficient from the picture remapped around the brightness there, details told from
  edges by a step in brightness, its curves for detail and tone, its brightness-only handling of color, and its smooth
  step that keeps the smallest differences from being boosted, which Noise Floor carries over.
- **The fast filter:** M. Aubry, S. Paris, S. W. Hasinoff, J. Kautz and F. Durand, ["Fast Local Laplacian Filters:
  Theory and Applications"](https://doi.org/10.1145/2629645) (ACM Transactions on Graphics 33(5), 2014): a few copies
  remapped around levels spread over the brightness range, each coefficient interpolated between the two nearest, and
  the smooth (Gaussian) remapping, which the copies sample closely.
- **Coring:** J. P. Rossi, ["Digital Techniques for Reducing Television
  Noise"](https://journal.smpte.org/periodicals/SMPTE%20Journal/87/3/5/) (SMPTE Journal 87(3), 1978), whose coring
  Noise Floor follows, leaving a small coefficient, more likely noise than detail, nearly as it was.
- **The octaves of detail:** P. J. Burt and E. H. Adelson, ["The Laplacian Pyramid as a Compact Image
  Code"](https://doi.org/10.1109/TCOM.1983.1095851) (IEEE Transactions on Communications 31(4), 1983), the library's
  pyramid (`lib/glsl/pyramid_down.glsl` and `pyramid.glsl`, shared with Video Vocoder), and their ["A Multiresolution
  Spline With Application to Image Mosaics"](https://doi.org/10.1145/245.247) (ACM Transactions on Graphics 2(4), 1983)
  for Depth Focus, which blends the picture and the result octave by octave. The pyramid expands by the cubic B-spline
  in four bilinear reads, after C. Sigg and M. Hadwiger, ["Fast Third-Order Texture
  Filtering"](https://developer.nvidia.com/gpugems/gpugems2/part-iii-high-quality-rendering/chapter-20-fast-third-order-texture-filtering)
  (GPU Gems 2, chapter 20, 2005).
- **Depth Type:** the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth
  reading (`lib/glsl/depth_near.glsl`) is shared with Fluid, Motion Magnify, Paint, Particles, Pencil, Point Cloud and
  Video Vocoder.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (October 2026) found none on local Laplacian filters by their authors or their
institutions, and a patent filed after 2011 can't validly claim the published filter. Adobe's US 8,831,340 and US
9,230,312 claim tone mapping a high dynamic range picture by packing a base layer into the lower part of the output's
range, which this effect doesn't do. Stewart's US 10,839,487 claims strengthening a picture's pyramid levels through a
blender that keeps each level within the dynamic range; this effect has no such per-level limit, only a clamp on the
finished picture.

**Not used:** Retinex (Land, 1964 to 1971; Jobson, Rahman and Woodell's multiscale Retinex, 1997, whose NASA patent
expired in 2016), the other classic way to flatten a picture's light by dividing it by a blurred copy. Tried on the
same clips, it took the color out of the lights (the lanterns turned white, the koi's pond brown), left halos where
light met shadow and blotched the noise in the darks, while Tone flattens the light without halos.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
