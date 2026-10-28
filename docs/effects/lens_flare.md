# Lens Flare

![Two views of five hooded walkers carrying lanterns across a field at night, each named in the library's pixel font. On the left, INPUT, the clip. On the right, LENS FLARE, the same walkers with the ghosts a 1953 camera lens would throw: bright blue-white hexagons below and beside the lanterns, each lantern's own set of them on the line from the lantern through the middle of the picture, fainter violet hexagons behind them, and a thin six-pointed star on each lantern; the hexagons move as the lanterns swing, and on the beat the whole flare brightens and settles](lens_flare.webp)

*The defaults on walkers with lanterns at night, the clip on the left, with a song on input 2. Each lantern throws its
own ghosts, which move as it moves, and the flare brightens on a beat at most once a second (Flashing at Calm).*

**New to lens flare?** A lens flare is light that went where it shouldn't inside a camera lens. Every glass surface in
a lens reflects a little of the light that reaches it, so some light from a bright lamp bounces off one surface, back off
another and reaches the sensor somewhere else. There it makes a ghost, a faint copy of the shape of the lens's iris (a
hexagon for a six-bladed iris), tinted by the coating on the glass. A lens has a ghost for every pair of surfaces the
light can bounce between, and they line up along the line from the lamp through the middle of the picture, some on the
lamp's side and some across the middle, all moving as the lamp moves. Bright lamps also get a starburst, spikes drawn
by light bending around the iris's blades. Photographers long treated flare as a fault; films, music videos and games
use it as a look.

Most flare effects draw made-up ghosts along that line, or flip the picture's highlights through the middle and blur
them. This one works the ghosts out from real camera lenses, the way Sungkil Lee and Elmar Eisemann described in 2013.
Simple optics tells, for every pair of surfaces in a lens, where its ghost lands for a lamp in any place, how big it is,
where the lens's front element cuts it off and what color its two surfaces' coatings leave it. The effect finds the
brightest lights in the picture and draws every ghost of every light, so a stage light, a headlight or the sun throws
the ghosts that lens would throw. The lenses are real designs from their patents: a 1953 Heliar, a 1934 Sonnar, a 1931
Topogon wide angle and a 2004 phone camera.

**[Download lens_flare.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/lens_flare.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `lens_flare.tox` into your network. It shows TouchDesigner's sample movie of a tree with the sun behind it, and
   the sun's flare.
2. Wire a TOP with bright lights in it into input 1: stage lights, headlights, the sun, lanterns, a phone's torch. The
   result is on output 1, at the input's size. A picture with no light near white gets no flare; lower Threshold for
   one whose highlights aren't clipped.
3. Wire music into input 2 (see Audio input). The flare then flares up on the beats and grows with the loudness.

Open Window (on the effect's page) shows it full size, and Esc closes the window. Show Flare Only gives the flare alone
over black, to add onto something else (with an Add TOP, say).

To update, delete your copy and drag in the new `lens_flare.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Lens Flare page holds, top to bottom, the lens, the iris, how strong, the lights, what to show, the music,
Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Lens | Heliar (1953) | Which lens the flare comes from: Heliar (1953), Sonnar (1934), Topogon (1931) or Phone Camera (2004), each from its patent. Each throws its own ghosts, in its own places and sizes. |
| Coating | Single Coated | The lens's anti-reflection coating, which colors its ghosts. Uncoated lenses (before the 1940s) give pale, colorless ghosts, a single coating (from the 1940s) pale violet ones, a modern multicoating ghosts in deeper colors. Each is shown about as strong; real uncoated lenses flare far more. |
| Aperture | 8 | The f-number, 1.4 to 22. Stopped down (a bigger number) the ghosts get smaller, crisper and brighter; wide open they spread into veils. A lens can't open wider than its design: f/3.5 for the Heliar, f/1.5 the Sonnar, f/4.5 the Topogon, f/4 the phone camera. |
| Blades | 6 | How many blades the iris has, 3 to 12. The ghosts take the iris's shape, and the starburst has that many spikes (twice as many for an odd number). |
| Roundness | 0.15 | How rounded the iris's blades are, 0 to 1. At 1 the iris is a circle: round ghosts and no spikes. |
| Blade Angle | 15 | How far the iris is turned, in degrees. |
| Amount | 1 | How strong the ghosts are, 0 to 4. |
| Starburst | 1 | How strong each light's starburst is, 0 to 4. |
| Starburst Size | 0.5 | How wide a starburst is, 0.05 to 1. At 1 it is as wide as half the picture's diagonal. |
| Threshold | 0.85 | How bright a part of the picture must be to count as a light, 0.5 to 0.99. Lower it for a picture without clipped highlights. |
| Lights | 6 | How many lights may flare at once, 1 to 16: the brightest ones. Fewer costs less. |
| Show | Picture and Flare | The picture with its flare, or the flare alone over black. |
| Beat Kick | 0.5 | On each beat on input 2 the flare flares up and settles, 0 to 1, as often as Flashing allows. |
| Swell | 0.5 | How much the music getting louder than usual strengthens the flare, 0 to 1. It follows the loudness over a second. |
| Flashing | Calm | How often the beat may flare the flare up. Off never does. Calm does at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The lenses and coatings

![Eight views of five hooded walkers carrying lanterns across a field at night, each named in the library's pixel font. INPUT is the clip. HELIAR, the defaults, throws bright blue-white hexagons from the lanterns, below and beside them, behind fainter violet ones. SONNAR throws only big faint veils of hexagons over the walkers. TOPOGON wraps the lanterns in a broad lavender haze. PHONE CAMERA strings many small bright ghosts in a band through the lanterns. UNCOATED turns the Heliar's ghosts into a pale gray veil. MULTICOATED makes them vivid magenta hexagons inside a teal veil. F/16 5 BLADES makes them small crisp pentagons](lens_flare_lenses.webp)

*The defaults (the Heliar, single coated, at f/8) and each other lens, then the Heliar uncoated and multicoated, and
stopped down to f/16 with five blades, on the same walkers with a song on input 2. Each lens throws its own set of
ghosts, and each coating colors them its own way.*

## How it works

**Ghosts.** In paraxial optics, the first-order optics of rays close to the lens's axis, a ray is two numbers, its
height and its slope, and everything that happens to it is a 2 x 2 matrix: traveling along the axis, bending through a
curved glass surface, reflecting off one. A lens is its surfaces, each a radius of curvature, a distance to the next and
the glass behind it (its refractive index and how that changes with color), and a ray through the whole lens is the
product of their matrices. A ghost is the path that reflects off surface j, back off surface i and on to the sensor.
Lee and Eisemann split each ghost's matrix at the iris, and the split says everything about it. The rays that get
through the iris are the iris's shape, and on the sensor that shape lands at a fixed multiple of the light's offset from
the middle (negative: across the middle), at a fixed size. The front element, whose glass only reaches so far out, cuts
the ghost where its circle falls, which for a light near the edge of the picture shaves the ghost into a crescent. How
bright the ghost is comes from how much of the light its path lets through against the intended one, spread over its
size, times how much its two surfaces reflect.

`src/optics.py` works this out from each lens's prescription when the effect is built. Each lens's ghosts sit in a
table inside the effect (`lens_heliar` and the others), one row a ghost: the two surfaces, then for red, green and blue
light (650, 510 and 475 nm, the paper's) where it lands, how big it is, where the front element cuts it, how bright it
is and how much each coating reflects. Every row is a few numbers; nothing about a ghost's shape is precomputed or
stored. The glass bends each color its own amount, so a ghost's three colors land slightly apart and its edges fringe.
Aperture scales the table: a ghost's size goes with the iris's opening.

**Coatings.** Each surface's reflection is a thin-film calculation (characteristic matrices, as in Macleod's *Thin-Film
Optical Filters*). Uncoated glass reflects about 4% of every color. A single quarter-wave layer of magnesium fluoride,
as lenses were coated from the 1940s on, cuts that to about 1.3% in the middle of the spectrum and less well at its
ends, so its ghosts come out violet. A modern multicoating (a quarter-half-quarter stack) reflects almost nothing,
except a little green and violet, which is the color of a modern lens's ghosts. Each surface's coating is tuned a little
differently, so the ghosts vary. Each coating is shown about as strong as the others; real uncoated lenses flare far
more.

**Lights.** A flare is linear in the light that makes it: two lamps make the sum of their flares, and a big lamp makes
the flare of its parts. So the effect finds lights by adding the picture up. Each pixel counts by how far its brightness
is past Threshold, squared, so what is near white counts far more than a pale wall. Tiles of 32 x 32 pixels sum that,
with where it lies and its color. A compute shader then takes the brightest tile as a light, with the tiles around it,
then the brightest light left, Lights times. Each light keeps its place (its tiles' centroid), its energy, its color and
its spread, how far its light lies from its middle. A big lamp's ghosts are blurred by its spread times how far they sit
from it, as a real one's are. Everything is clipped to white in a picture, so a light's energy says only how much of it
is white, and it is compressed: the sun flares more than a lantern, but doesn't whiten the whole picture.

**Starburst.** The starburst is the iris's diffraction: the far-field pattern of light passing an opening is the
square of the opening's Fourier transform (Fraunhofer). The effect draws the iris (with a few specks of dust, which
add fine streaks), takes its 2D Fourier transform in two passes of plain sums, and adds the pattern up over 24
wavelengths across the spectrum, each scaled by its wavelength, so the spikes come out white near the light and end in
rainbows (Hullin and his colleagues' method). This runs only when the iris changes. A real light is far brighter than
its clipped pixels show, so the pattern is shown with its faint spikes raised.

**Drawing.** Every ghost of every light is one square, drawn by a Geometry COMP with an instance for each and placed,
sized and colored by its material's shaders from the light and the ghost table, then added up by a Render TOP at half
the picture's size (ghosts are soft, and it costs a quarter as much). Ghosts much bigger than the picture would only gray
it over, so they are kept faint. The lights are eased over a fifth of a second and the flare over a tenth, so a light's
small wobbles don't flicker its ghosts, and the flare is added to the picture in linear light, rolling off toward white
rather than clipping flat.

**Limits.** First-order optics is exact near the lens's axis and less so far from it, so a real lens's ghosts bend and
stretch as a light nears the edge of the picture, and these don't; they keep the iris's shape, shaved by the front
element. A picture clips every light to white, so how bright a light really is can't be read from it: a light counts by
how much of it is white, compressed, and Amount sets the rest. And the ghosts trail a fifth of a second behind a light
that moves fast, a price of keeping them from flickering.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends beats and loudness. Drag `fosfora_signal.tox` (in
Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw audio** (an Audio File In or
Audio Device In CHOP) gives the beats and the loudness from the sound itself. **TouchDesigner's audioAnalysis** gives
beats from its kick or onset channels and loudness from its level.

On each beat the flare flares up, its ghosts and starbursts up to 1.75 times as bright at the default Beat Kick (2.5 at
1), and settles over 0.4 seconds, as often as Flashing allows (once a second at Calm). The loudness, smoothed over a
second and judged against its usual level over the last 4 seconds, strengthens the flare as the music swells (Swell).

**Nothing wired:** the flare of the picture's lights, with no flaring up and no swell.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. On the dancer clip each frame took 1.4 ms on the GPU (95th percentile 1.8 ms) and
0.6 ms on the CPU, the median of three runs with the Mac otherwise idle. Most of it is drawing the ghosts (1.1 ms), so
the cost follows the lights: 1.7 ms on the walkers with five lanterns, 3.2 ms on a street full of headlights. Each light
draws all of its lens's ghosts (13 for the Heliar, 21 for the Sonnar, 20 for the Topogon, 29 for the phone camera), and
a ghost costs what it covers of the picture, so Lights caps the cost and a wide-open aperture, whose ghosts are big,
raises it. Finding the lights is about 0.45 ms (the tiles and the compute shader that gathers them). The ghosts are
drawn at half size, which their soft edges hide. The starburst's
Fourier transform takes about 1.7 ms, once, when the iris changes. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** The flare flaring up on a beat changes large parts of the picture at once, which counts as flashing, so
  a beat does it only through the standard flash gate. Off never does, Calm (the default) at most once a second, and Up
  to 3 per second is WCAG 2.3.1's limit.
- **The lights' own changes.** A flare puts big ghosts far from its lights, so a light that wobbles (noise, a car's
  lamp coming and going) swept their edges back and forth over large areas: on the headlights the first build flashed
  1.5 times a second more than the clip with Flashing Off. Two things fixed it. A tile's share in a light fades out
  with distance instead of stopping at an edge, so a light no longer jumps when another tile becomes the brightest. And
  the flare is eased over a tenth of a second. With Flashing Off every clip now measures within the clip's own flashes.
- **No meaning in color.** The effect signals nothing by hue. Ghosts are brighter where the picture's lights are
  brighter, and they move as the lights move.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, the loudness swinging 8 times a second), a dance beat at 140 BPM, or no music, and counted
the flashes in the worst second by WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse, a stage light | 1.0 | 1.0 | 1.0 | 1.0 |
| A street of headlights at night | 1.0 | 1.5 | 1.0 | 1.0 |
| Walkers with lanterns at night | 0.5 | 0.5 | 0.5 | 0 |
| Red flowers against the sun | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 | 1.0 | 1.0 |
| Headlights, Beat Kick 1 | 1.0 | 1.5 | 1.0 | 1.0 |
| Flowers, the phone camera multicoated | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 | 1.0, red 1.0 |

Every row keeps its setting's promise, and nothing comes near WCAG's 3. With Flashing Off the flare adds nothing to the
clip's own beyond the measurement's half-flash margin; the lanterns, carried by people walking, use that margin. The
beat's flare-up, which rises over a tenth of a second rather than at once, added no more than half a flash a second to
any of these clips, even at Up to 3 per second. The last two rows are corners, spot-checked: the strongest beat, and the most colorful lens over red
flowers.

## Credits and license

MIT. The shaders and operators are written for this library, including finding the lights by tiles gathered around the
brightest, each with its spread; blurring a ghost by its light's spread, into a blob when that is wider than the ghost;
normalizing each coating to the same total; fading ghosts much bigger than the picture; the iris's Fourier transform as
two passes of plain sums; easing the flare; the flare up on the beat through the flash gate and the swell with the
loudness.

- **The method:** S. Lee and E. Eisemann, ["Practical Real-Time Lens-Flare
  Rendering"](https://cg.skku.edu/pub/papers/2013-lee-egsr-matrixflare-cam.pdf) (EGSR 2013, Computer Graphics Forum
  32(4)): paraxial ray transfer matrices for each two-reflection ghost, split at the iris, the ghost as the iris's shape
  cut by the entrance pupil, a color channel each at 650, 510 and 475 nm, brightness from the area ratio.
- **Coatings and the starburst:** M. Hullin, E. Eisemann, H.-P. Seidel and S. Lee, ["Physically-Based Real-Time Lens
  Flare Rendering"](https://doi.org/10.1145/2010324.1965003) (SIGGRAPH 2011, ACM TOG 30(4)): anti-reflection coatings
  as thin films, the starburst as the iris's far-field diffraction summed over wavelengths, dust on the iris.
- **The lenses:** from expired patents, as transcribed in Nathan Hagen's
  [LensLibrary](https://github.com/nzhagen/LensLibrary) (MIT, Copyright (c) 2021 Nathan Hagen; its notice is in
  `src/lenses.py`): A. W. Tronnier, US 2,645,156 (1953, the Heliar, the paper's own lens); L. Bertele, US 1,975,678
  (1934, the Sonnar); R. Richter, US 1,792,917 (1931, the Topogon); K. Isono, US 6,744,570 (2004, a phone camera lens).
- **Thin films:** H. A. Macleod, *Thin-Film Optical Filters* (characteristic matrices); the quarter-half-quarter
  broadband coating after A. Thelen and others.
- **Glass:** each glass's index for a color from its Abbe number (E. Abbe), with A.-L. Cauchy's two-term formula.
- **Color:** the CIE 1931 color matching functions, by C. Wyman, P.-P. Sloan and P. Shirley's analytic fit (["Simple
  Analytic Approximations to the CIE XYZ Color Matching Functions"](https://jcgt.org/published/0002/02/01/), JCGT 2(2),
  2013), into sRGB (IEC 61966-2-1).
- **The sums in shared memory:** a parallel reduction, as in W. D. Hillis and G. L. Steele, ["Data parallel
  algorithms"](https://doi.org/10.1145/7902.7903) (CACM 29(12), 1986).
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (October 2026) found Lee and Eisemann's method patented by Sungkyunkwan University
as US 9,595,132, which expired in March 2025 (its maintenance fee went unpaid). Hullin and his colleagues' patent
application (US 2014/0210844) was abandoned. No other patent on rendering a lens flare turned up.

**Not used:** a table of ghost shapes worked out ahead for every angle of the light and blended with the linear ghosts,
to catch the bending a first-order model misses (the paper's Section 5 tries it and leaves it out). Sungkyunkwan
University's continuation patent, US 10,074,195, claims it. Here every ghost is its few numbers and nothing more.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
