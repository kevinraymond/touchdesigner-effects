# Photoelastic

![Five views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. DARK FIELD shows her as clear plastic between crossed polarizers on a dark ground: rainbow fringes run down her body and ring her outline, fan out above her where her arms swept, and stream from the stage light along its beam, while the empty room stays dark. LIGHT FIELD shows the same fringes on a pale gray ground, the colors their complements, outlined in brown and blue. PLANE is the dark field crossed by dark bands where the stress lies along the polarizers. TINT PLATE turns the ground deep purple, the fringes in magenta, blue and yellow](photoelastic.webp)

*Photoelastic on the dancer, the clip top left, with her depth map on input 3 and a song on input 2: Dark Field (the
default), Light Field, Plane and Tint Plate.*

**New to photoelasticity?** Clear plastic under stress splits light into two waves polarized at right angles, and one
travels a little slower than the other. Put the plastic between two polarizers and the waves interfere, so white light
comes out in rainbow bands: black where the plastic is unstressed, then gray, white, yellow, red, blue, green and pinks
as the stress grows, in the order of Michel-Lévy's chart that geologists use to identify minerals. Each band is a
fringe, a line of equal stress, and the fringes crowd together where the stress gathers. Engineers have used this for
about a century to see where a part is stressed, with plastic models of hooks, gears and bridges between polarizers.

This effect gives your picture that plastic. What stands in front in a depth map, the picture's light and whatever
moves warm the plastic, and a plastic warmed unevenly is stressed, since its warm parts swell against the cool ones
around them. So the fringes ring a warm subject and crowd at its outline, follow her as she moves, and fade behind her
as the plastic cools. The plastic is cast to the warmth, thick where the picture warms it, so the colors gather on the
subject and the rest stays dark. I found no photoelastic effect for TouchDesigner. On the web, a paid WebGPU shader on
shadcn.io draws photoelastic fringes, and it takes no picture.

**[Download photoelastic.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/photoelastic.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `photoelastic.tox` into your network. It shows TouchDesigner's banana with a soft white light circling over
   it: fringes ring the banana, and the light warms the plastic as it passes and leaves fringes fading behind it.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Optional: wire music into input 2 (see Audio input). Its loudness then loads the plastic, its beats squeeze it and
   its bars turn the polarizers.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). What stands in front (or is
   inside the mask) then warms the plastic, so the fringes gather on the subject. Without it, the picture's light and
   whatever moves warm it.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Reset cools the plastic at once.

To update, delete your copy and drag in the new `photoelastic.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Photoelastic page holds, top to bottom, the polariscope, what warms the plastic and input 3, the music, then the
window.

| Parameter | Default | What it does |
|---|---|---|
| Style | Dark Field | Dark Field: crossed circular polarizers, so unstressed plastic is black and the stress shows in its interference colors. Light Field: the light passes where the plastic is unstressed, and the stress shows in the complementary colors. Plane: crossed straight polarizers, which also darken the plastic wherever its stress lies along them (the isoclinics). Tint Plate: a full-wave plate added, so unstressed plastic is magenta, and stress turns it blue one way and yellow the other. |
| Stress | 0.5 | How strongly the warmth stresses the plastic, 0 to 1: more stress, more fringes. |
| Polarizer Angle | 0 | Which way the polarizers face, in degrees (Plane and Tint Plate). The dark isoclinics and the blue and yellow turn with them. |
| Backlight | 0.25 | The light behind the plastic, 0 to 1: at 0 the picture itself, at 1 a plain white light, so the colors show in the picture's dark parts too. |
| Cast | 1 | How much the plastic is cast to what warms it, 0 to 1. At 1 it is thick where the picture is warm and thin elsewhere, so the colors gather on the subject and the rest stays dark. At 0 it is an even sheet, and the stress shows wherever it reaches. |
| Backdrop | 0.2 | How much of the picture shows as it is where the plastic is unstressed, as polarizers short of perfect let it through (all but Light Field, which shows it anyway). |
| Warm by Movement | 0.75 | How much whatever moves warms the plastic, quickly, leaving it to cool behind it. |
| Warm by Nearness | 1 | How much what stands out in front in the depth map on input 3 (or what is inside the mask) warms the plastic. |
| Warm by Light | 0.5 | How much the picture's light warms the plastic, as light falling on it would: the brighter, the warmer. An evenly bright area is stressed only at its outline. |
| Linger | 0.5 | How long the plastic stays warm once what warmed it has gone: at 0.5 it cools over about 1.5 s, at 0 four times as fast, at 1 four times as slowly. |
| Input 3 Holds | Depth Map | Depth Map: what stands in front of its surroundings warms the plastic, while floors and walls don't count. Mask: what is inside the mask (white inside) does. |
| Sensitivity | 0.5 | How easily something in the depth map counts as standing out (farther counts as well), or how gray a mask counts as inside. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading. Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Reset | | Cools the plastic at once: no warmth left, no stress. |
| Beat Squeeze | 0.5 | On the beats of input 2 the plastic is squeezed, and every fringe jumps outward and settles back over 0.3 s. It goes through Flashing. At 0 the beats leave it be. |
| Loudness | 0.5 | How much louder music on input 2 loads the plastic harder (more fringes) and quiet passages lighter, following the loudness over about a second. |
| Bar Turn | 22.5 | How far each bar of input 2 turns the polarizers, in degrees (Plane and Tint Plate), at most once every 2 s and over 1.5 s. At 0 they stay still. |
| Flashing | Calm | Off: the beats never squeeze the plastic. Calm: at most one squeeze a second. Up to 3 per second: every beat up to 180 BPM. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## How it works

**The warmth.** What stands out in front of what lies left and right of it in the depth map warms the plastic, and so
do the picture's light and whatever moves, through the library's warmth, which Frost thaws by and Schlieren's air
rises from. It warms quickly and cools slowly, so a moving arm leaves a warm trail. A faint change, such as haze
drifting through a dark room, warms nothing.

**The stress.** A plate warmed by T swells there, and J. N. Goodier showed in 1937 that its displacement is the
gradient of a potential ψ with ∇²ψ = T. The stress that makes plastic birefringent is the part of ψ's Hessian that
isn't its trace: (ψxx − ψyy) / 2 and ψxy. Inside an evenly warm patch that part is zero, at its outline it is strongest,
and outside it falls away as 1 / r². So the fringes outline a warm subject and ring it. A plate warmed evenly only
grows, so the warmth's mean is taken away first.

**Solved every frame.** ψ is solved afresh each frame on the warmth's pyramid, coarse to fine, by cascadic multigrid
(Bornemann and Deuflhard, 1996). The coarsest level, 20 x 11 cells, is summed directly: each cell adds its warmth
times the square lattice's Green's function at its distance, which treats the plastic as an infinite plate. Each finer
level starts from the coarser one's ψ and is smoothed by six Jacobi passes, with the frame's edges held. Clamping ψ at
the edges drew fringes along the frame instead. Nothing is carried over from the last frame but the warmth.

**The light.** The stress's size gives each pixel a fringe order, how many waves of 550 nm one polarized wave falls
behind the other, and its direction gives the angle to the polarizers. A chart worked out once per Style says what
white light comes out at each order and angle: each wavelength's transmission through the polariscope, summed through
the CIE 1931 color matching functions as Wyman, Sloan and Shirley fit them, which gives Michel-Lévy's colors as B. E.
Sørensen computes them from first principles (2013). The tint plate's colors come from Jones calculus. The light behind
the plastic is the picture, evened toward a plain white light by Backlight, and the orders stop crowding past four,
where the fringes would alias.

**The cast.** The retardation grows with the plastic's thickness as well as its stress. An even sheet showed the stress
wherever it reached, and a large warm patch, a dancer with her arms' trails and the stage light's beam, spread first-order
grays and pastels over the whole frame. Cast makes the plastic thick where the picture warms it, read from the warmth
at a sixteenth of the size, and thin elsewhere. The stress is still worked out for an even sheet.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its beats, bars and loudness. Drag `fosfora_signal.tox`
(in Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw audio** (an Audio File
In or Audio Device In CHOP) gives the beats from a kick detector and a beat clock, and the loudness from its low band.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels.

Louder music loads the plastic harder, so the fringes multiply and spread, and quiet passages lighter (Loudness). The
load follows the loudness over about a second, so the fringes swell with the music rather than pumping on every hit.
Each beat squeezes the plastic, so every fringe jumps outward and settles back, as often as Flashing allows (Beat
Squeeze). Each bar turns the polarizers a little, slowly and at most once every 2 seconds (Bar Turn, Plane and Tint
Plate).

**Nothing wired:** the load stays even, nothing squeezes, and the polarizers stay at Polarizer Angle.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, the dancer's depth on input 3 and a busy beat on input 2. Each frame took 1.95 ms
on the GPU (95th percentile 3.3 ms) and 0.67 ms on the CPU, the median of three runs with the Mac otherwise idle. The
look costs the most, about 0.55 ms, then the finest level of the solve and the depth reading, about 0.27 ms each. Each
GLSL pass costs about 0.04 ms on this Mac whatever its size, so the solve is kept to 29 passes: a first version that
solved the coarsest level by 60 Jacobi passes took 5.4 ms. GPU times on this Mac wander from run to run as its GPU
changes speed. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing setting:** Off, Calm (the default) or Up to 3 per second. A beat's squeeze moves every fringe at once, so
  it is a flash and goes through it.
- **Moving fringes flash.** Each fringe that passes a spot takes it through light and dark, so fringes that follow a
  moving subject add flashes by themselves. The load follows the loudness over a second, the polarizers turn at most
  once every 2 seconds, and the orders stop crowding past four. With Flashing Off the dancer measured 1.5 flashes a
  second against the clip's 1.0, at the limit.
- **Red guard.** The interference colors pass near WCAG's saturated red (the first order's red, the second's), so every
  pixel goes through the library's red guard. No setting measured a red flash.
- **No meaning in color.** The fringes' colors follow the stress, and so does their brightness. Tint Plate's blue and
  yellow say which way the stress lies, and Plane's dark bands say it by brightness.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully 8 times a second) and counted the flashes in the worst second by
WCAG's area rule, and WCAG's red flashes separately. The dancer had her depth map on input 3:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.5 | 1.5 | 2.0 | 1.0 |
| Dancer, Light Field | | 1.5 | | 1.0 |
| Dancer, Plane | | 1.0 | | 1.0 |
| Dancer, Tint Plate | | 1.0 | | 1.0 |
| Dancer, Stress, Beat Squeeze and Loudness all 1 | | 2.0 | | 1.0 |
| Red flowers against the sky | 1.0 | 1.5 | 2.0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0 | 1.0 | 1.0 | 0.5, red 1.5 |
| People crossing a plaza | 0.5 | 1.0 | 1.0 | 0.5 |
| Hands | 2.0 | 1.5 | 1.5 | 1.5 |

## Experimental

- Raw audio's beat clock is experimental and can still add or miss beats.

## Credits and license

MIT. The shaders and operators are written for this library, including the picture's warmth as the plastic's heating,
the stress as its thermal stress, the plastic cast to the warmth, the backlight and backdrop, the beat's squeeze and the
bars turning the polarizers.

- **Stress birefringence and the polariscope:** D. Brewster, "On the communication of the structure of doubly
  refracting crystals to glass, muriate of soda, fluor spar, and other substances, by mechanical compression and
  dilatation" (Philosophical Transactions of the Royal Society 106, 1816); the stress-optic law after J. C. Maxwell,
  "On the equilibrium of elastic solids" (Transactions of the Royal Society of Edinburgh 20, 1853); the dark and light
  fields, plane and circular polariscopes and isoclinics as M. M. Frocht lays them out, *Photoelasticity* (Wiley,
  1941).
- **The interference colors:** A. Michel-Lévy's chart (1888) as B. E. Sørensen computes it, ["A revised Michel-Lévy
  interference colour chart based on first-principles calculations"](https://doi.org/10.1127/0935-1221/2013/0025-2252)
  (European Journal of Mineralogy 25, 2013), each wavelength's transmission summed through the CIE 1931 color matching
  functions as C. Wyman, P.-P. Sloan and P. Shirley fit them, ["Simple Analytic Approximations to the CIE XYZ Color
  Matching Functions"](https://jcgt.org/published/0002/02/01/) (JCGT 2(2), 2013), shared with Lens Flare and Schlieren
  (`lib/glsl/spectrum.glsl`). The tint plate's colors by R. C. Jones's calculus, "A new calculus for the treatment of
  optical systems" (JOSA 31, 1941).
- **The stress from the warmth:** the thermoelastic displacement potential of J. N. Goodier, "On the integration of the
  thermo-elastic equations" (Philosophical Magazine 23, 1937), solved by cascadic multigrid after F. A. Bornemann and
  P. Deuflhard, "The cascadic multigrid method for elliptic problems" (Numerische Mathematik 75, 1996), with Jacobi
  smoothing on the warmth's Gaussian pyramid (P. J. Burt and E. H. Adelson, 1983; `lib` `pyramid()`). The coarsest
  level is summed through the square lattice's Green's function, the potential kernel of the plane's simple random
  walk, in its large-distance form (F. Spitzer, *Principles of Random Walk*, 1964).
- **What warms the plastic:** the library's warmth (`lib` `warmth()`, shared with Frost and Schlieren), its change
  detection (`optical_flow()`) and its depth reading (`lib/glsl/depth_near.glsl`, `depth_find.glsl`). The stress is
  resampled Catmull-Rom (`lib/glsl/common.glsl`), and the red guard is `lib/glsl/red_guard.glsl`.
- **Beats from raw audio** (the library's audio input): a kick is a jump in the low band's loudness; the beat clock
  takes its tempo from the gaps between kicks, inter-onset-interval tempo induction, the idea behind S. Dixon,
  "Automatic Extraction of Tempo and Beat from Expressive Performances" (Journal of New Music Research, 2001). Followed,
  not copied.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (November 2026) found none on a polariscope's look applied to a picture, on
interference colors worked out from a stress taken from a picture, or on thermal stress drawn as fringes; the
photoelastic patents are about real polariscopes, display panels and measuring parts. The closest are Dolby's US
8,929,654 and US 9,077,942, which build a spectrum for each pixel from its color by a lookup of its chromaticity: the
picture here only multiplies the polariscope's white-light colors, channel by channel. ByteDance's US 12,694,597 and
GritWorld's application US 2023/0106802 carry a displayed field or texture coordinates along a velocity: the stress here
stays where it is and is worked out afresh every frame from the warmth. Adobe's US 11,409,423 and US 11,755,187 claim
offering a menu of simulated phenomena to pick from and apply to an image, and steering a simulation by pointing at the
image: this effect runs one kind of stress, Style changes only how it is seen, and it takes no pointer or touch input.

**Not used:** those patents' methods. Stress from the depth map's curvature or from the optical flow's strain rate,
tried first: both drew fringes over every bit of noise in the picture.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
