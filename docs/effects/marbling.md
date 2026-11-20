# Marbling

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. PICTURE INKS floats the picture on a marbler's tray: round drops in the picture's own grays and skin tones sit in the haze and push it aside, and the haze is combed into rows of scallops and feathered edges, while the dancer stays clear in front. EBRU INKS does the same with drops of indigo, ochre, rose, off-white, umber and sea green, some round and fresh, some combed into hearts and teardrops. SUBJECT COMBED combs the dancer too, her legs drawn out into wavy ribbons](marbling.webp)

*Marbling on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: Picture inks (the
default), Ebru inks, and Keep Subject off, so she is combed with the rest. Each take started with the tray already a
few strokes in.*

**New to marbling?** Marbling is the old craft behind the swirled end papers of books, called ebru in Turkey. A marbler
floats inks on a tray of thickened water, the size. Each drop spreads into a disc and pushes the inks already there
aside. Then the marbler draws combs and styluses through the tray, and the inks are pulled into patterns with names:
gel-git, a rake drawn across and back, nonpareil, a fine comb drawn after it at right angles, and bouquet, a comb drawn
along curved tracks. A sheet of paper laid on the surface takes the pattern.

This effect floats your picture on the size, as if it were the first ink. On each beat a drop of ink falls and pushes
the picture aside, and on each bar a comb is drawn through the tray in the order a marbler would draw them. The picture
stays live through it all, so a dancer is combed into feathers mid-step. Every drop and stroke holds for a few bars and
then relaxes, so the picture comes back while new ones are made. With a depth map on input 3 the subject stays clear in
front of the marbled room. I found no marbling effect for TouchDesigner. On the web, marbling shaders and sketches make
their own inks (a WGSL marbling shader on shadcn.io, p5.js sketches, paint.toys), and none takes a picture.

**[Download marbling.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/marbling.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `marbling.tox` into your network. It shows TouchDesigner's sample movie, marbled at 120 BPM by itself.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Optional: wire music into input 2 (see Audio input). Its beats then drop the ink and its bars draw the strokes.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). What stands in front (or is
   inside the mask) then stays the live picture, clear of the marbling. Without it, the whole picture is marbled.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset clears the tray at once.

To update, delete your copy and drag in the new `marbling.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Marbling page holds, top to bottom, the tray, input 3, the music, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Inks | Picture | Picture: each drop is the picture's own color where it falls, taken the moment it falls. Ebru: traditional marbling pigments, indigo, ochre, rose, off-white, umber and sea green, in turn. |
| Pattern | Bouquet | How far each tray is combed, a stroke a bar over four bars. Stone: drops only. Gel-Git: a comb drawn across and back. Nonpareil: then a fine comb at right angles. Bouquet: then a comb drawn along a wave. |
| Drop Size | 0.5 | How big the drops are, 0 to 1. At 0 no drops fall. |
| Comb | 0.5 | How hard the combs pull, 0 to 1. Past about 0.6 the picture is combed past knowing; at 0 the combs leave it be. |
| Tine Spacing | 0.5 | How far apart the combs' tines are, 0 to 1: a tenth to a half of the frame's height, the nonpareil's a quarter of that. It applies to the next strokes. |
| Hold | 4 | How many bars a drop or a stroke holds before it relaxes, 1 to 16. It applies to the next ones. |
| Relax | 2 | How many bars a drop or a stroke takes to relax, so the picture comes back, 0.5 to 8. It applies to the next ones. |
| Reset | | Clears the tray: every drop and stroke is gone at once. |
| Keep Subject | On | What stands out in front in the depth map on input 3 (or what is inside the mask) stays the live picture, clear of the inks and the combs. With nothing on input 3 the whole picture is marbled. |
| Input 3 Holds | Depth Map | Depth Map: what stands in front of its surroundings is kept clear, while floors and walls don't count. Mask: what is inside the mask (white inside) is. |
| Sensitivity | 0.5 | How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask counts as inside. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Drops | Every Beat | Which beats of input 2 drop ink: every beat, every other beat or the first of each bar, at most 3 a second. |
| Loudness | 0.6 | How much the loudness of input 2 sizes the drops, 0 to 1. At 1 a quiet beat drops a speck and a loud one a big drop. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## How it works

**The tools.** Shufang Lu, Aubrey Jaffer and their colleagues worked out marbling's tools as closed-form maps of the
tray onto itself, each keeping every area the same, as an incompressible liquid does ("Mathematical Marbling", 2012). A
drop of radius r at a point C moves every point P out along the line from C, to C + (P − C) √(1 + r² / |P − C|²): the
disc it lands on takes the drop, and the ring around it is pushed out just far enough to keep its area. A comb drawn in
a direction M moves each point along M by α λ / (d + λ), d its distance to the nearest tine: points near a tine are
dragged along with it, and points between tines less. A wave moves points along M by a sine of how far across they lie,
and after a comb it gives a comb drawn along a wave, which stands in here for the bouquet. A marbler's bouquet comes from
two rakes on curved tracks.

**Undone at every pixel.** Each of those maps is easy to undo: a comb moves points only along M by an amount that
depends on how far across they lie, which the comb doesn't change, so undoing it subtracts the same pull. So each pixel
finds its color by undoing the tools one by one, newest first. If the point lands inside a drop, the pixel takes that
drop's ink. If it gets past every tool, it takes the picture where the point started. This is the second way the paper
draws a marbling, after Karl Sims' "Choreographed Image Flow" (1992): every tool at once, from scratch, so nothing blurs
however many strokes there are, and nothing carries over from one frame to the next. The list of tools is the whole of
the marbling. Each pixel takes four samples on a rotated grid, as the paper does, since the inks' edges and the threads
the combs draw come out finer than a pixel.

**The tray.** A Script CHOP keeps the list: a drop on each beat, spread over the tray by Martin Roberts' R2 sequence so
each lands well away from the last few, and a stroke on each bar. A tray is four bars: gel-git across, gel-git back with
its tines between the first pass's, the nonpareil's fine comb at right angles, then the comb along a wave. Trays take
turns combing across and down. Each comb gives back its mean pull, as pst-marble's shift does, so a comb moves the inks
past each other without carrying the whole tray off the frame, and the tray runs on past the frame's edges as a mirror
of the picture. Every tool rises as it is made (a drop spreads over a quarter of a second, a stroke is drawn over a
beat), holds for Hold bars and relaxes to nothing over Relax bars. A drop's ink is taken from the picture where it falls,
the moment it falls, and kept for as long as the drop lasts.

**The subject.** With a depth map on input 3, whatever stands out in front of what lies left and right of it stays the
live picture, clear of the marbling. The marbled tray behind still holds the subject's own colors, so combed copies of a
dancer can trail around her.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats, bars, loudness and sections. Drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw
audio** (an Audio File In or Audio Device In CHOP) gives the beats from a kick detector and a beat clock, and the
loudness from its low band. **TouchDesigner's audioAnalysis** gives beats from its kick or onset channels.

Each beat drops ink (Drops: every beat, every other beat or the first of each bar), at most three a second, and the
louder the beat, the bigger the drop (Loudness). Each bar draws the tray's next stroke, at most one every 2 seconds. A
stroke takes a beat to draw, and Hold and Relax are counted in bars at the music's tempo. A new section of the song
(Fosfora only) relaxes the whole tray over a bar and starts a new one.

**Nothing wired:** the tray keeps 120 BPM by itself, a drop every half second and a stroke every 2 seconds.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, the dancer's depth on input 3 and a song on input 2. Each frame took 1.8 ms on the
GPU (95th percentile 3.7 ms) and 0.6 ms on the CPU, the median of three runs with the Mac otherwise idle. The marbling
itself takes about 1 ms of it, and its cost grows with the drops and strokes on the tray, about 25 at the defaults:
with Hold at 16 bars the tray filled with about 50, and the frame took about 6 ms on the GPU. GPU times on this Mac
wander from run to run as its GPU changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **No Flashing setting.** Nothing jumps at once: a drop spreads over a quarter of a second and a stroke is drawn over
  a beat, at most three drops a second and one stroke every 2 seconds.
- **Measured at the clip's own, or half a flash over it.** The combs sweep the picture's light and dark past each
  other, so a picture of bright shapes on a dark ground (koi in a black pond) gains half a flash a second.
- **No meaning in color.** The effect signals nothing by hue. Ebru's rose stays well short of WCAG's saturated red.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully 8 times a second) and counted the flashes in the worst second by
WCAG's area rule, and WCAG's red flashes separately. The dancer had her depth map on input 3:

| Clip and settings | Marbling | The clip alone |
|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 |
| Red flowers against the sky | 1.0, red 1.0 | 1.0, red 1.0 |
| Red flowers, Ebru | 1.0, red 1.0 | 1.0, red 1.0 |
| People crossing a plaza | 0.5 | 0.5 |
| Koi in a black pond | 1.0, red 1.5 | 0.5, red 1.5 |
| Koi, the corner | 1.0, red 2.0 | 0.5, red 1.5 |

The koi at a dance tempo (140 BPM) and with a song as raw audio measured the same as under the busy beat: 1.0 against
the clip's 0.5. The corner sets Comb 1, Tine Spacing 0 and Drop Size 1 together, and stays within WCAG's 3.

## Experimental

- Raw audio's beat clock is experimental and can still add or miss beats.

## Credits and license

MIT. The shaders and operators are written for this library, including the live picture as the first ink, the drops on
the beats and the strokes on the bars, the tools relaxing so the picture comes back, and the subject kept clear.

- **The method:** S. Lu, A. Jaffer, X. Jin, H. Zhao and X. Mao, ["Mathematical
  Marbling"](https://doi.org/10.1109/MCG.2011.51) (IEEE Computer Graphics and Applications 32(6), 2012): ink drops,
  straight and wavy combs as closed-form maps that keep areas, each undone by its inverse, and a raster image drawn by
  undoing every tool at each pixel, sampled on a rotated 2 x 2 grid. A. Jaffer, [Mathematical
  Marbling](http://people.csail.mit.edu/jaffer/Marbling/): the drop's inverse, the nonpareil drawn in pst-marble's
  How-To, and pst-marble's shift, after which each comb here gives back its mean pull. Drawing all the tools from
  scratch at each pixel follows K. Sims, "Choreographed Image Flow" (Journal of Visualization and Computer Animation
  3(1), 1992), as the paper does.
- **The drops' places:** M. Roberts, ["The Unreasonable Effectiveness of Quasirandom
  Sequences"](https://extremelearning.com.au/unreasonable-effectiveness-of-quasirandom-sequences/) (2018), the R2
  sequence.
- **The subject:** input 3's depth through `lib/glsl/depth_near.glsl` and `depth_find.glsl`.
- **Beats from raw audio** (the library's audio input): a kick is a jump in the low band's loudness; the beat clock
  takes its tempo from the gaps between kicks, inter-onset-interval tempo induction, the idea behind S. Dixon,
  "Automatic Extraction of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed,
  not copied.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (November 2026) found none on marbling, ink drops or comb strokes applied to a
picture, or on composing closed-form maps that keep areas; the marbling patents are about stone, meat and toys. Three
applications carry something along from frame to frame: GritWorld's application US 2023/0106802 (its status unknown) carries texture coordinates
along a velocity, ByteDance's US 12,694,597 carries a displayed fluid's color along by a backtrace, and Huawei's pending
US 2025/0117558 carries a phase field along a velocity worked out from it. Nothing here is carried over from the last
frame: the picture is read through the tools undone afresh each frame. Adobe's US 11,409,423 and US 11,755,187 claim
offering a menu of simulated phenomena to pick from and apply to an image, and steering a simulation by pointing at the
image: this effect runs one kind of marbling, Inks changes only the drops' colors, and it takes no pointer or touch
input.

**Not used:** those patents' methods. A single warp map kept from frame to frame and moved by each new tool, which would
have been cheaper but is the carried-along coordinates above, and blurs a little with each step. Placing the drops by
the music's bands, which piled them into rows: the bands barely change from beat to beat.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
