# Building the library

Every `.tox` here is generated, never edited by hand. A builder script assembles each one
inside TouchDesigner from plain source files (shaders, callbacks), checks it, and saves it
with a manifest beside it. Review the sources; ship the `.tox`.

## Layout

```
lib/tox_build.py              shared by every builder: the standard effect shell, helpers, save-time checks, manifests
lib/font5x7.py                a 5 x 7 bitmap font for text drawn in shaders (labels, glyph grids)
lib/audio_callbacks.py        the audio input's logic (audio_in() puts it in a Script CHOP)
lib/glsl/                     shaders several effects share: depth_near.glsl (input 3 as nearness, by Depth Type),
                              depth_find.glsl (what stands in front of its surroundings); lum, change, clock and lk
                              (the input's motion: optical_flow() builds them); pace and speed (that motion as a
                              speed: flow_speed()); common.glsl (Catmull-Rom resampling, a hash);
                              red_guard.glsl (keeps reds short of WCAG's red flash line); tensor, tensor_blur,
                              tensor_ease and tensor_flow (the direction of the picture's edges: structure_tensor());
                              paper.glsl (gradient noise and a paper's grain, drawn rather than loaded: Paint, Pencil);
                              pyramid_down.glsl and pyramid.glsl (the picture's octaves of detail: pyramid());
                              divergence, pressure and project (a fluid's velocity made incompressible:
                              incompressible()); warmth.glsl (what the picture warms: what stands out and what
                              moves, warmth()); spectrum.glsl (the CIE color matching functions: Lens Flare)
effects/<name>/
  build_<name>.py             the builder (has a VERSION = 'x.y.z' line)
  src/                        what it is built from: *.glsl, *.py
  <name>.tox, <name>.json     built in TouchDesigner, committed together
bundles/<name>/               same shape; a bundle embeds effects (the showreel)
docs/effects/<name>.md        the effect's page, its preview beside it (_template.md to start)
tests/check_tox.py            the stale-file test
tests/test_guards.py          breaks each rule check_tox.py enforces, once, and checks it fails
dev/                          dev loop, self-test and measuring tools; never shipped
```

## Building an effect

Open a textport in TouchDesigner (Alt+T) and run the builder with `__file__` set to its path:

```python
__file__ = '/path/to/touchdesigner-effects/effects/glow/build_glow.py'; exec(open(__file__).read())
```

It creates `/project1/glow` (replacing any previous copy), checks it, and writes
`effects/glow/glow.tox` and `effects/glow/glow.json`. Commit both.

Every build of an effect in progress goes into the demo as well, so it can be watched as it grows on the
Mac, from the first build that passes the save checks: `dev/td.sh dev/demo.py` after the builder (see
The dev loop) reloads whatever changed into `/tdlib_demo`.

A builder has this shape:

```python
"""Build Glow. Run from a textport: __file__ = '/path/to/build_glow.py'; exec(open(__file__).read())"""
import os

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    raise RuntimeError("set __file__ to this script's path before exec()")
_ROOT = os.path.dirname(os.path.dirname(_HERE))
exec(compile(open(os.path.join(_ROOT, 'lib', 'tox_build.py')).read(), 'tox_build.py', 'exec'), globals())

VERSION = '0.1.0'

comp, page, source = new_effect('glow', 'Glow', 'Glow 0.1.0: ... (one-line summary)', README, tags=('glow',), audio=True)
custom(page, 'Float', 'Amount', 'Amount', 0.5, 'How strong the glow is.', 0, 1, True)
section('glow', 'The glow: bright parts spread into their surroundings')
glsl = mk(comp, glslTOP, 'glsl', [source], comment='What this step does.')
docked(glsl, '_pixel', open(os.path.join(_HERE, 'src', 'glow.glsl')).read(), 'The glow shader.')
finish_effect(comp, glsl, VERSION, page)
save_effect(comp, _HERE, _ROOT)
```

What the shell provides:

- `new_effect()` creates the COMP with the library's node color, tags and node size, a README
  DAT, and the inputs: `in1_top` (input 1), a Switch TOP `source` that shows a sample picture
  from `app.samplesFolder` until something is wired in, with `audio=True`, `in2_audio`
  (input 2, an optional CHOP), and with `depth=True` as well, `in3_top` (input 3, an optional
  TOP: a depth map or mask, brighter nearer or inside). `depth_in()` reads it: input 3 when
  something is wired in, else a stand-in made from input 1 (its brightness, unless the effect
  passes its own), so a depth effect works with nothing on input 3.
- `finish_effect()` adds `out_top`, the Open Window / Full Screen / Display parameters and
  their Window COMP, the About page (Version, Built With, Open Docs), shows the output
  on the node, and lays out the network (below).
- `save_effect()` runs the save-time checks, saves, and writes the manifest.

Helpers: `mk()` creates, comments, sets parameters and wires in one call (`Expr('...')` for an
expression), and puts the operator in the current `section()`; `custom()` adds a parameter with its
default, range and help text; `docked()` fills the DAT TouchDesigner docked to an operator (a GLSL
TOP's `_pixel`, a Script CHOP's callbacks) instead of adding a second one; `glsl()` makes a GLSL TOP
in one call (docked shader filled, any number of inputs: past the third they go through its TOPs
parameter, the only way that works), and `uniforms()` sets its vector uniforms; `flash_gate()` is
the one way an effect may flash (below); `optical_flow(comp, _ROOT, source)` gives the input's
motion as Datamosh and Fluid use it (luma at 1/8 and 1/4, whether this frame is a new input frame or
a cut, and Lucas-Kanade optical flow, each size following the input; `levels=(8,)` stops at 1/8, as Words, whose cells
are 8 pixels, needs no finer, and `flow=False` leaves the flow out, as Temporal Resonator and Caustics need only the luma
and the clock), and `flow_speed()` turns that
flow into a speed, held between the input's frames, as Fluid and VHS + CRT's plasma use it (Pencil passes a smaller
`dead` zone, so a slow pan carries its strokes too);
`structure_tensor(comp, _ROOT, source)` gives the direction of the picture's edges at every pixel
and how clear it is (the smoothed structure tensor's minor eigenvector and anisotropy, as Paint,
Reaction-Diffusion and Pencil use it), and with `ease=` seconds eases the tensor over time
first, so the direction turns smoothly instead of jittering with the picture's noise (Reaction-Diffusion);
`pyramid(comp, _ROOT, source, levels)` gives the picture's Gaussian pyramid, `[source, g1, g2, ...]`, each level half
the size of the one before (Video Vocoder, Detail): a shader that pastes `lib_glsl(_ROOT, 'pyramid.glsl')` in front reads a
Laplacian band as a level minus `expand()` of the next, and summing the bands back up through the same `expand()` gives
the picture back exactly (within a fraction of an 8-bit step at 32-bit float). An effect with several pyramids names each
one's levels with `prefix=` (Detail's `l1`..., `a1`..., `b1`...) and says what it halves with `what=`;
`incompressible(comp, _ROOT, advected, passes)` makes a fluid's velocity incompressible, the pressure solve of stable
fluids (divergence, then `passes` Jacobi iterations of the pressure in one TOP, then the projection), as Fluid runs it;
`warmth(comp, _ROOT, subject, mo, start)` blends what stands out or is inside the mask (subject) and what moves
(`optical_flow()`'s change and clock, held between the input's frames, past a dead zone) into one field that rises
quickly and falls slowly, which Frost thaws by;
`lib_module(_ROOT, 'font5x7')` loads another `lib/` file, such as the bitmap font (`glsl_font()` gives
the shader `glyph(g, p)`; `ramp()` orders glyphs by ink), and `lib_glsl(_ROOT, 'depth_near.glsl')` a
shared shader.

A shader takes the time as `clock_seconds()`, never `absTime.seconds` itself. A uniform is a
32-bit float and `absTime.seconds` counts from TouchDesigner's start, so after 12 hours it is good to
1/256 s and after 3 days to 1/32 s: frame-timed noise, gaps between frames and smooth motion all
coarsen the longer a show runs, and two passes that each work out "which update is this" from it
disagree near its start (VHS + CRT's e-ink replayed updates as flashes, board #4680).
`clock_seconds()` wraps it every `CLOCK` seconds (16384, about 4.6 hours), which keeps it to 1 ms:
take differences modulo `CLOCK` (lib's clock, pace and speed do), accept that smooth motion driven by
it jumps once at each wrap, and count anything that must be exact (which update, which frame) in
Python, whose floats are 64-bit. `assert_idiomatic` refuses a uniform whose expression grows with
`absTime.seconds` (not wrapped with `%`, not turned into an angle with `math.sin` or `math.cos` in
Python); CHOP channels are 32-bit too, so a script reads `absTime.seconds` itself.

## Laying out the network

Someone who opens an effect should be able to follow it, so every network has the same shape.
The builder only says which part of the effect each operator belongs to, and
`finish_effect()` works out where everything goes (`lay_out()`, from `plan_layout()`, which is
plain Python).

- The network reads left to right. Everything wired into an operator sits to its left. So does
  anything it reads by expression or operator parameter from its own box. A reference to another
  box is left free, since TouchDesigner draws no line for it and the picture's shaders read the
  audio's values all along the way. A Feedback TOP's Target TOP is the loop it closes and is exempt.
- Each part of the effect sits in a Network Box (an Annotate COMP in Network Box mode) whose
  title says in plain words what that part does, such as "The tape: the deck's time base, its
  filters and noise, the signal into the TV". Every operator sits in exactly one box, boxes
  never overlap, and each box is wide enough for its title.
- Boxes run in lanes, one row of boxes each. "Read me" (the README and the parameter script)
  sits at the top left. The picture's lane runs along the top, from input 1 to the output, which
  takes the last column. Any other lanes come next, in the order the builder first names them.
  The audio and depth lanes come last, since they start from inputs 2 and 3. Within a lane,
  boxes run in the order they are wired.
- Inside a box, each operator sits as far right as what it feeds allows and level with what it
  reads. Columns are `LAYOUT_COL` (200) apart, wider after a column holding a wider node (the
  Showreel's effects), and operators stack by their own heights.
- The DATs docked to an operator sit right under it, its shader or callbacks first, then its
  Info DAT. TouchDesigner docks a pixel shader, a compute shader and an Info DAT to every GLSL
  TOP; `lay_out()` drops the shader its mode doesn't run, which would read as part of the effect,
  and keeps the Info DAT, which says where a shader fails to compile (the node only says that
  it did).

A builder names its parts with `section(key, title, lane=...)` before the operators that belong
to them. `mk()` refuses to make an operator inside the effect before any `section()`.
`new_effect()` opens "Read me", the input box, and the `audio` and `depth` boxes with their In
operators, which the builder titles when it builds on them (`section('audio', 'Audio (input
2): ...')`). `finish_effect()` opens the output box, which the builder may title too (VHS +
CRT's holds the Switch that picks a screen). Lib helpers such as `audio_in()` and
`optical_flow()` put their operators in whatever section is current. An operator made some other
way (a loaded `.tox`) joins one with `put(op, key)`. Outside the effect, `mk(..., at=(x, y))`
places an operator by hand, as the dev tools do.

`assert_laid_out` checks the result at save time (TD_IDIOMS D7). It refuses an operator outside
every box or in two, boxes or operators that overlap, a docked DAT away from its operator, an
untitled box, a wire running right to left, and an operator reading one to its right in its own
box. To see a network without opening TouchDesigner, `dev/probes/layout_dump.py` writes every
component's operators, wires, references and boxes as JSON. To show that a change moved
operators and nothing else, compare two `dev/probes/structure_dump.py` runs with
`dev/probes/structure_diff.py`.

## Building a bundle

A bundle is a component that embeds others: `bundles/showreel/build_showreel.py` finds every
built `effects/<name>/<name>.tox`, loads each one into the shell unchanged (its Flashing follows the
bundle's, its node viewer off) and puts them behind one View menu. It saves with `save_tox()` and a
manifest that records each embedded file's hash under `embeds`, with `embeds_all` set: the bundle
takes every effect. So adding or rebuilding an effect needs only a rebuild of the showreel:

```sh
dev/td.sh bundles/showreel/build_showreel.py
```

Until then `tests/check_tox.py` fails, naming the effect it lacks or embeds an older build of. A
bundle is a component like any other: the same save-time checks, a docs page, an idiom review. The
dev tools load one when it is named (`TD_ARGS='showreel' dev/td.sh dev/perf.py`).

## Save-time checks

`save_tox()` refuses to save, naming each offender, when:

- anything points outside the component: an external `.tox`, a clone, a global shortcut, an
  operator parameter or expression naming an absolute path, a script calling `op('/...')`,
  or a file parameter with an absolute path (sample media comes from `app.samplesFolder`).
  TouchDesigner's own `/sys` and `/ui` are allowed;
- a docked DAT is unused (the builder wired its own beside it);
- it isn't readable inside: no README, one without its CREDITS or one wrapped by hand, an operator
  without a comment, a parameter without help, the About page incomplete, no tags, another node color,
  a node smaller than 480 x 270;
- the inputs aren't a TOP then optionally a CHOP and a TOP, the output isn't one TOP, or anything
  inside makes sound (an Audio Device Out, whose saved state would play the moment a project
  opens);
- an operator renders larger than the Non-Commercial license's 1280 x 1280;
- it breaks a TouchDesigner idiom a script can judge (`assert_idiomatic`, items named in
  [TD_IDIOMS.md](TD_IDIOMS.md)): pages out of order, Version editable, a parameter saved off its
  default, a node that doesn't show the output, extensions not initialized on start, a Script
  CHOP not cooking `WHEN_USED`, Python every frame or a forced cook, a shader handed the raw clock
  (below), or a flashing effect without the standard Flashing parameter;
- it doesn't load clean (`assert_loads_clean`): any error or warning with nothing wired, in it
  or in a second copy beside it. TouchDesigner reports a GLSL compile error as a warning, so
  warnings count;
- its network isn't laid out (`assert_laid_out`, Laying out the network above).

`dev/selftest.py` breaks each of these once inside TouchDesigner and checks it refuses, checks
that a flashing effect built the standard way passes, and that the intact effect loads
elsewhere without errors, as a drag-in would.

## The idiom review

[TD_IDIOMS.md](TD_IDIOMS.md) lists what an experienced TouchDesigner developer expects of a
component they download. Items marked *auto* are the checks above; items marked *review* are
judged by hand, once per version, in `effects/<name>/review.md`:

```sh
uv run tests/check_tox.py --review-template glow > effects/glow/review.md
```

Tick each box (`- [x]`) with a few words on how it holds. `tests/check_tox.py` fails while a
box is open, when the review is for an older version than the builder's, and when the checklist
gains an item the review doesn't have, so adding an idiom reopens every effect's review. The
review isn't one of the sources, so writing it doesn't call for a rebuild.

## Credits

Every component says where it comes from, in two places: a CREDITS section in its README DAT
(inside the `.tox`, so it travels with every copy) and a "Credits and license" section on its docs
page. Both name every paper, technique, project, piece of code, font, model and media it uses,
follows or was built after, with links and licenses; the docs page also credits the preview's
footage. Each entry is one of:

- **From or after a source:** a paper (authors, title, venue, year), a project or a piece of code
  (author, link, license), or a widely known technique. Code taken from elsewhere is credited
  where it sits too, in a comment in the shader or script, with its license when that asks for one.
- **Followed, not copied:** a project or video whose approach the effect follows, or that was read
  while building it, without its code ("follows the approach Acerola showed in ...").
- **Original (no earlier source found):** designed here, and a search found no earlier source.
  Only for what was designed here: code recalled from elsewhere that can't be traced is replaced
  with something that can, never called original.

The README DAT holds one line per paragraph and per list item, with a blank line between
paragraphs. TouchDesigner's text viewer wraps lines to its own width, so a README wrapped by hand
breaks again wherever the viewer is narrower than the wrap, which reads jolting. A list item or an
indented line may follow a line directly, and anything may follow a heading (CREDITS, USE).
`new_effect()` turns the README's Word Wrap on, and `assert_readable` refuses a README wrapped by
hand (`hard_wrapped()`; `dev/selftest.py` breaks it).

Write the credits while building, from what the prototypes and the board recorded, and check them
before the review: TD_IDIOMS D6 asks for it by hand in every version's review, `save_tox()` refuses
a README without CREDITS (`dev/selftest.py` breaks it), and `tests/check_tox.py` fails a docs page
without its Credits and license (`tests/test_guards.py` breaks it).

## Flashing

Every effect follows [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html).
One that can flash is built with `new_effect(..., flashing=True)`, which adds the standard
Flashing parameter: Off never flashes; Calm, the default, allows at most one flash a second;
Up to 3 per second is the WCAG limit, which no setting exceeds. Every flash goes through
`flash_gate(comp, trigger, x, y)`: a Trigger CHOP whose Re-Trigger Delay follows the setting
(`FLASH_INTERVAL`) and a Math CHOP that passes nothing when it is Off. `dev/selftest.py` feeds
it 4 pulses a second for 6 s: Off lets 0 through, Calm 6, Up to 3 per second 16. The effect
shapes the flash after the gate, and the limits are measured again on its output before release
(TD_IDIOMS.md A2): `dev/flash.py` records the output's luminance, cell by cell, under a beat
far busier than music at each setting, and `dev/flashcount.py` counts the flashes with WCAG's
definitions and area rule (see The dev loop). WCAG's red test works in linear light: a color counts
as saturated red when red is 80% of the three there, so a dark orange (green at 0.35 of red in sRGB,
0.1 in linear light) still counts. A color that flickers keeps green at 0.6 of red or more (Fluid's
flames, whose red edges measured 2.5 red flashes a second with Flashing Off).

Three more traps, from VHS + CRT. The red test is all or nothing at that 80%, and `dev/flash.py` takes
it per pixel: noise that changes every frame, however faint, makes any red sitting near the line flash
(the flowers: 2 red flashes a second with Flashing Off), and a CRT mask's red stripes over an orange
are saturated-red pixels by themselves. VHS + CRT eases every red share past 0.73 toward 0.775 by
adding green and blue (`lib/glsl/red_guard.glsl`, which Bent Cam uses too), on the picture and again on every
output pixel; a share is linear, so no area can average past it. A pattern whose sign flips every
frame (NTSC's subcarrier phase, every field) flickers wherever it doesn't cancel over a cell, which is
everywhere on fine detail. And one gated event that moves the whole picture (a roll) passes every
point through light and dark several times: several flashes, whatever the gate counts. A jump and a
jump back is one.

Two more from Bent Cam. Damage that runs to the end of a line (a clock slip, or a stream error up to its
restart marker) piles up on the right edge, where every such slip ends, so that edge flashed when the beat
added slips everywhere at once: keep slips to stretches spread over the frame, and a beat's to a sliver. And a
feedback loop that zooms outward echoes every movement outward, so each echo passing a point is another swing
between light and dark there, with Flashing Off as much as on (Feedback 0.95 at Zoom 1.1 measured 4.5 a second).
No gate reaches that, so the parameters' ranges have to: measure the corners of every range that feeds a loop
(`TD_ARGS='<effect> flashing=off Feedback=... Zoom=...' dev/td.sh dev/flash.py` records only that setting).

Three more from Slit-Scan, whose picture is the input re-timed. A beat that moves an area back and forth in time is a
jolt wherever the picture moves (a band of extra delay running through the time map flashed red flowers and koi at
Calm, 3 and 4 red flashes a second), so its beats tear a few thin slivers instead, as Glitch's do. Anything that moves
the time map sweeps time past each point at the delay times the map's rate, and faster than the picture's own
movement it shows the picture's changes, flashes included, faster, with Flashing Off as much as on: limit the product,
not the rate alone (a drift that measured clean at a 1.5 s delay added a flash a second at 8 s). And strip photography
spreads one line's flicker over a whole area, wider the faster the film runs, so its speed stops where the flowers
stopped adding flashes, and the red guard covers every pixel it shows (guarding only the film as it was laid still
measured 2 red flashes a second: resampling the moving film mixed one pixel's red with another's green and blue).

One more from Paint. A hard threshold turns any change in what it thresholds into flips between its two tones: a beat's
band of broader strokes, which keeps each area's colors in Oil and Watercolor, flipped whole patches between ink and paper
in Ink (the flowers measured 2 flashes a second under the stress beat, 1 without the band), so Ink doesn't sweep.

One more from Reaction-Diffusion. A pattern whose features are about the size of the flash test's cells (its stripes are
18 pixels apart at Medium, the cells 20) swings a cell between light and dark wherever it moves, though it changes no
area's share of ink. So whatever moves it flashes: its stripes turning and thickening as they followed drifting smoke
measured 1.5 flashes a second over the clip's own with no beat (the direction of the edges now eases over half a
second and the tone over a quarter), the pattern growing in on blank paper measured 1.5 to 2.5 in its worst second
(it now starts as an even tone and crossfades into the grown pattern), and a ripple sliding the stripes on every beat
added a flash a second at its full depth (it goes through the flash gate). Measure the pattern after it has grown in as
well as from the start: flash.py's recording began while it was still growing.

Two more from Pencil, whose drawing has a drawing's contrast. Its lines multiply small changes in the picture's
edges many times over (a faint edge in drifting smoke comes out a dark line), so a video's noise, followed at once,
flickered them: half a flash a second over the dancer clip's own with no beat at all, and a loud input pressing the
lines harder tipped it over again after a tenth of a second of easing; the edges now ease over a fifth. And a pencil
drawing has few true darks, so its tone map lifts a picture's darks to mid tones: the koi's near-black pond is drawn
mid-gray, and ripples too dark to count in the clip (0.006 to 0.02 in linear light) move the drawing by about 0.1,
WCAG's step. Capping the histogram (contrast-limited, at three times an even share a level) keeps a narrow band of
tones from being stretched over every tone and took the koi's worst cell from 4 flashes a second to 3, but what remains
is the clip's own change at a drawing's contrast (1.5 against the clip's 0.5), within WCAG's 3.

One more from Pixel Sort. A sort ties every pixel of a span to every other: when a span gains or loses a pixel at an
end, its whole streak sorts anew. So whatever moves the ends of spans from frame to frame flashes, with Flashing Off as
much as on. Noise in the picture at a threshold did (hysteresis keeps a pixel in or out until it is clearly past it),
and so did turning the angle, which moves the steps in the digital lines so pixels change lines: Spin 20 measured 1.5
flashes a second on the plaza with Flashing Off, where the clip alone measures 0.5, and Spin stops at 10.

One more from Motion Magnify, which moves the picture further than it moved. It adds no light, and it changes how far
things go, not how often, but a red near WCAG's saturated-red line that sways further crosses it more often: the red
flowers measured 2 red flashes a second with no beat, the clip alone 1. Its warp runs the red guard on every pixel, as
Slit-Scan's does, and shows none.

Two more from Video Vocoder, whose picture follows the music's levels rather than its beats. A level that jumps up on
each hit and falls between them pumps the picture at the hits' rate, and pumping detail counts as flashing, even detail
finer than the test's cells: its octaves pumped on every eighth note at 140 BPM flashed red flowers 4 times a second,
the fine octaves alone 2.5. The stress beat hid it, since easing a level's fall smooths 8 hits a second more than 4,
so `beat=music` now pulses the bands as drums would. A level may jump up at once only through `flash_gate()`, all the
bands together, and between jumps it follows the level smoothed over a second. Rising slowly but falling fast instead,
it rippled at every hit, and the ripple flipped reds near WCAG's line 3 times a second. And a red guard added before
that gate turned every red flower orange. With the gate in, the effect kept its Flashing promises without the guard, so the guard went: it is for what
a gate can't reach.

Two more from Pixel Art, whose few flat colors turn small changes into whole art pixels changing. A palette that takes
shape by splitting changes large areas a few frames apart, each split a transition, so it flashed while it formed, and
`dev/flash.py` caught that every time, since an effect first cooks when the recording starts. The art shows its
superpixels' own colors until the palette is whole, then fades into it. And WCAG's red test is all or nothing at 80%, so a
palette color whose share sat near the line and drifted across it as the palette followed the picture flipped every
pixel it covered between saturated red and not at once, though nothing visible changed (the flowers' dark red-brown,
bursts of 2.5 to 3 red flashes a second with Flashing Off). Each palette color keeps to one side of the line with
hysteresis, at most 0.77 or at least 0.83. The red guard would do it too, but it turned the red flowers orange.

Two more from Lens Flare, whose ghosts sit far from their lights at multiples of where the lights are. Whatever moves a
light moves its ghosts further, and they are big and bright where the light was a few pixels. Lights found by gathering
tiles around the brightest one jumped whenever another tile became the brightest and a tile changed lights, and the
headlights flashed 1.5 times a second more than the clip with Flashing Off: a tile's share in a light now fades with
distance instead of stopping at an edge, and the flare is eased over a tenth of a second. And walkers carrying lanterns
bob them twice a second, which swept each lantern's ghosts back and forth over the dark field (a flash a second with
Flashing Off, where the clip has none): the lights are eased over a fifth of a second, so their ghosts trail a little
behind a light that moves fast.

Three more from Words, whose picture is small text. Text that moves flashes: each stroke passing a spot is light, each
gap dark, so lines of text about as far apart as the test's cells (Lines' rings, a line every 21 pixels) swing every
cell they sweep through between text and gap, a flash for each line that passes. Rings following a dancer at once
measured 2 flashes a second with Flashing Off where the clip has 1, and white words riding her through Portrait's
packed page did the same. Lines' rings now move at most a line's spacing a second, and Portrait's words stay put while
the picture moves under them. A word pushed out of all of its overlap with an older one each frame, when it sits
between two older ones, is pushed past the middle to the mirror position and back the next frame, a shake every other
frame that flashed every cell it covered in white (19 a second in one cell): pushed out of half, it settles between
them. And fading every word out at a cut, to lay the new shot out afresh, took the whole picture to black and back at
each of the dancer clip's loops; the words now stay through a cut and only those that no longer fit go.

One more from Scan Processor, whose Colorizer gives each band of brightness a hue and keeps the pixel's brightness, so
that a band changing changes only the hue, which WCAG doesn't count unless it is red. A dark hue such as its dark blue,
scaled up to a bright pixel's brightness, runs past 1, and clipped it lost a quarter of that brightness. Where the
brightest band wraps around to the darkest, the picture's noise flipped pixels between the two, and one cell of the
flowers flashed 6.5 times a second with Flashing Off. Blended toward gray of the same brightness instead of clipped, the
brightness stays exact, and that cell measured 2.5, the clip's own.

Three more from Voxel Space, which shows the picture as land seen in perspective. The near ground is the picture enlarged,
so the picture's own changes cover more of the view than they do in the picture: the picture lying flat, the camera
still and no light, measured 2 flashes a second where the clip has 1, and the dancer's figure standing up close by 3. A
cliff face shows the few pixels between the cliff's foot and its top spread over hundreds of rows, and where a depth
map's edge and the picture's don't quite meet, every move of the subject swung the face between the floor's dark and her
clothes' light; faces now take the color of their tops. The land's heights and its colors ease together over a quarter of
a second (easing the heights alone measured worse, since the colors ran ahead of the hills). And a moving camera streams
the land through every part of the view: a bright, busy picture (a plaza from above) flown over at 70 world units a second
measured 3 flashes a second over the clip's half, so the flight is slow (28) and the view eases over a tenth of a second,
less while a beat dips the camera, since that move is already rationed by the gate and eased as much it smeared.

Three more from Temporal Resonator, whose echoes replay the picture's movement a beat later, and again. Each echo of an
arm sweeping across the haze passes over the same spots as the arm did, so every echo strong enough to swing a spot by
WCAG's step is another flash there. At 140 BPM the dancer measured 1.5 flashes a second against the clip's 1 while the
first echo came back brighter than the arm, and 1 once each echo came back softer than the last. A beat-shaped pluck that
fell to nothing between beats made the echoes of everything that moves pulse at the beat, and a picture that moves all
over (red flowers in the wind) pulsed whole, 2 flashes a second against the clip's 1. A pluck that falls only to half
measured the clip's own. And the red guard applied only where an echo showed switched on and off as echoes came and went,
which flipped the flowers' reds across WCAG's line more often than no guard at all (2 red flashes a second against 1.5).
Every pixel goes through it instead, as Slit-Scan's and Motion Magnify's do, which measured none.

Three more from Caustics, whose light is the water's waves focused into bright lines. How hard a wave focuses light goes
with how sharply it curves, so short, steep ripples make the brightest, busiest lines for the least water. Raindrops
three pixels wide and the picture's change pushed into the water as it came made a fine grain of light that flashed 3 to
5 times a second where the clip has 1. Slow swells a tenth of the picture wide and wakes spread over ten of the water's
pixels (a quarter of the picture's size) kept to the clip's own. A beat's drop with a radius a fifteenth of the picture's
height added half a flash a second on the dancer, and one with a radius a ninth of it added none. Wakes spread over six pixels did the same
on flowers in the wind, where everything moves and the wakes cover the whole pool, and over ten they added none. And the
caustics' own contrast mattered less than how they move: halving it changed nothing the counter saw.

Three more from Schlieren, whose picture is seen through warm air that bends it. A bright point the bending shifts
flashes however small the shift: the air over a stage light, shaken by every beat's puff, slid its bright point back and
forth over the dark room and flashed the cells around it 16 times a second, so the lights are opaque (the air shows
around them, not over them) and the picture shifts at most a few pixels. A puff that lifts all the warm air at once
moves the whole picture when all of it is warm: red flowers swaying in the wind, warm all over, measured 3.5 flashes a
second at Calm, so a puff weakens in proportion where more than a twentieth of the picture is warm. And relief that
turns with the blade, or air that rises fast enough to churn, sweeps light and dark past every cell it covers: turned on
every bar of the stress beat the blade added half a flash a second with Flashing Off, and twice today's lift added one
and a half, so the blade turns at most once every 2 seconds and the air never rises faster than 0.4 frame heights a
second.

## The audio input

An effect built with `new_effect(..., audio=True)` reads input 2 through `audio_in(comp, _ROOT)`,
which turns whatever is wired there into the same channels on the CHOP `audio`:

| Channel | Value |
|---|---|
| `beat` | 1 on the frame a beat arrives, else 0 |
| `beat_count` | beats so far; for logic, watch the counts, since a one-frame pulse can be missed |
| `bar_count` | bars so far: Fosfora's `bar_count` (or `downbeat` pulses), else one every 4 beats |
| `beat_phase` | 0 to 1 through the current beat: Fosfora's, else timed from the last beats |
| `beat_period` | seconds a beat lasts: Fosfora's `bpm` (or another input's `bpm` or `tempo`), else raw audio's beat clock, else the gaps between the last beats; 0.5 (120 BPM) until there are beats |
| `level` | 0 to 1, how loud right now: raw audio's low band, Fosfora's `bass` |
| `build` | 0 to 1, how far into a build: Fosfora only, else 0 |
| `drop_count` | drop-like moments so far: Fosfora's `drop_count` (experimental there), else 0 |
| `section_count` | section changes so far: Fosfora's `boundary_count`, else 0 |
| `source` | 0 nothing, 1 raw audio, 2 analysis channels, 3 Fosfora's signal |
| `sub_bass`, `bass`, `low_mid`, `mid`, `upper_mid`, `presence`, `brilliance` | 0 to 1, how much is in each band of the sound now, lowest to highest: Fosfora's seven-way split (20, 60, 250, 500, 2000, 4000, 6000 Hz and up) |

Input 2 may carry:

- [Fosfora](https://github.com/kevinraymond/fosfora)'s signal (`fosfora_signal.tox`): every
  channel comes from it, so an effect can follow bars, builds, drops and sections as well as beats.
  `level` comes from its `bass`, not its `energy`: over a song `energy` sits between 0.7 and 0.9 and
  moves about 0.01 in two seconds, so nothing that follows it moves, while `bass` swells with each
  beat and between passages (median 0.67, like raw audio's level). The bands come from its feature
  bus (`fosfora --signal --feat-bus`: `feat_sub_bass` to `feat_brilliance`), else from its `bass`,
  `melody` and `drums` (bass for the lowest two, melody for the middle, drums for the top);
- raw audio (Audio File In, Audio Device In): the low band's loudness (30 to 150 Hz, from an FFT
  of the last 40 ms) gives `level`, and a jump above its recent average is a kick. Once the kicks
  keep to a tempo, a beat clock locks to their grid: beats come on it, so a missed kick is filled in
  and a kick between beats is left out, and a bar is every 4 of its beats (which beat is the one is a
  guess). It stops 8 beats after the last kick on its grid (a breakdown goes quiet), and while it is
  unlocked every kick is a beat. On the library's songs it finds every beat of the drop the previews
  use, where the kicks alone found three in four (`dev/beat_bench.py`). Each band is the loudness
  of its FFT bins over its own running peak (falling by half in 4 s), so every band uses the whole
  range whatever the mix's balance: the lowest three from the last 4096 samples (about 90 ms), the
  rest from the last 1024, which follow a hi-hat closely. They add about 0.1 ms of CPU a cook;
- other analysis channels, by name: beats from `beat_count`, or the rising edge of `beat`, `kick`
  or `onset` (TouchDesigner's audioAnalysis and Essentia rhythm CHOPs); level from `energy`,
  `level`, `low`, `bass` or `rms`; the bands by their own names, else from `low`, `mid` and `high`
  (audioAnalysis: low for the lowest two, mid for the middle three, high for the top), else all
  from the level;
- nothing: no beats, level 0, the bands 0, and the effect still works.

It is one Script CHOP that cooks only when something uses it, so the audio front end does
nothing while the effect's output is unused (TD_IDIOMS C5). An earlier version measured raw
audio's low band with a time-sliced Audio Filter CHOP, which cooked every frame, used or not.

An effect works with any of them and is at its best on Fosfora's signal: `build`, `drop_count` and
`section_count` stay at 0 without it, so use them for extra moments, never for the effect's
basic behavior. `lib/audio_callbacks.py` holds the logic. `dev/selftest.py` feeds it each kind
of input for 3 s: nothing gives 0 beats; `beat_count` and `kick` at 2 a second give 6 (and 1 or 2
bars); a Fosfora-shaped input passes its bars, build and beat phase through, its level follows
`bass` rather than `energy`, and its bands come from the feature bus where it sends them and from
the stand-ins where it doesn't; TouchDesigner's sample MP3 gives 6 (about 120 BPM) and bands between
0 and 1. The beat clock is
checked outside TouchDesigner (`uv run --with numpy dev/beat_bench.py --selftest`). Beats that make
the picture flash still go through `flash_gate()`.

## Manifests and the stale-file test

`<name>.json` records the effect's version, the TouchDesigner build it was saved in, a hash
of its sources (every `lib/*.py` and `lib/glsl/*`, the builder, everything in `src/`) and a hash of the
`.tox`. A bundle's also records the hash of every `.tox` it embeds (`embeds`), and whether it
takes every effect (`embeds_all`).

`tests/check_tox.py` fails when a source changed since the last build, the `.tox` isn't the
file its manifest describes, the builder's `VERSION` isn't the built one, a component (effect or
bundle) has no docs page (or it doesn't link `releases/latest/download/<name>.tox`, doesn't state
the build the `.tox` was saved in, has no Credits and license section, or its preview is missing), its idiom review is missing or out
of date (above), a bundle embeds an older build, or a bundle that takes every effect leaves one
out. `tests/test_guards.py` breaks each of those on purpose. Both run in CI and before every
commit:

```sh
git config core.hooksPath .githooks      # once per clone
uv run tests/test_guards.py
uv run tests/check_tox.py
```

Because the source hash covers `lib/`, changing anything there means rebuilding every effect.

## The dev loop

TouchDesigner has no Linux build. `dev/td.sh` runs a repo script inside TouchDesigner on
another machine and prints what it printed:

```sh
dev/td.sh dev/selftest.py
dev/td.sh effects/glow/build_glow.py
```

It copies the repo to `~/tdlib` on the Mac, writes a `cmd.py` that runs the script into the
folder a watcher Execute DAT polls, waits for the watcher's `out.txt`, and copies back built
`.tox` files, manifests and anything saved under `dev/out/` (save frames there with
`top.save(path)` to look at them). Builds land in `/tdlib_dev`, one COMP at the root, away
from the project the watcher lives in.

Defaults (override with the environment): `TD_HOST=kevin@mbpm2`, `TD_WATCH=fosfora-td-dev`
(the folder `fosfora_dev_watcher` in `~/Desktop/fosfora-dev.toe` polls), `TD_REPO=tdlib`,
`TD_PARENT=/tdlib_dev`. If that watcher is gone, `dev/watcher.py` says how to install a copy.
Check the first line of the watcher's `out.txt` before a run: another session may be using it.
`TD_ARGS='a b'` hands the script the words `a` and `b` as `TDLIB_ARGS`.

Everything a script does runs on TouchDesigner's main thread, so the interface waits for it: a
build with its save checks stalls the Mac's TouchDesigner for a few seconds, and a measurement
that reads the output every frame slows it for as long as it runs. Keep that in mind when
someone is using the Mac.

The other dev tools, each run through `dev/td.sh` (their headers say more):

| Script | What it does |
|---|---|
| `dev/demo.py` | `/tdlib_demo`: every built effect on a test clip, with Fosfora's signal (or a sample track) as the beat, one effect running at a time; reloads what changed |
| `dev/capture.py` | exec'd by a script: save frames of some TOPs over the next seconds; `dev/sheet.py` lays them out |
| `dev/flash.py` + `dev/flashcount.py` | record each Flashing setting's output under a stress beat, then count flashes per second the WCAG way (`uv run --with numpy dev/flashcount.py dev/out/flash`; `--selftest` checks the counting) |
| `dev/perf.py` | each effect's CPU and GPU cook time per frame at its defaults, for the performance note |
| `dev/beat_bench.py` | `lib/audio_callbacks.py` outside TouchDesigner: feeds it a song as raw audio and scores its beats and bars against the song's beat grid (`uv run --with numpy dev/beat_bench.py`); `--selftest` checks the beat clock on a made-up kick track with missing and extra kicks |
| `dev/reaction.py` + `dev/reaction_report.py` | record each effect with a song as raw audio on input 2 and without audio, then measure what the music does to the picture: how much more it changes after a beat than before (the take without audio at the same times is the control), what a bar adds, and how brightness follows loudness (`uv run --with numpy dev/reaction_report.py dev/out/reaction`) |
| `dev/record.py` + `dev/clips.py` | record effects (and, named `input` and `depth`, the clip and its depth map) as video with sound (Motion JPEG: the free license can't encode H.264), then MP4s and docs previews (`uv run dev/clips.py dev/out/record --preview`) |
| `dev/tile.py` | tile `dev/record.py`'s takes into one labeled grid, rows centered, in the library's font: the README's hero and the Showreel's preview, the clip and its depth map alone on the top row as the inputs, the effects in rows of three (two where they don't fill a row) below (`TD_ARGS='input depth ascii ... seconds=8' dev/td.sh dev/record.py`, then `uv run --with pillow dev/tile.py dev/out/record --rows 'input,depth\|ascii,...' --titles 'input=INPUT,...' --out dev/out/record/hero --still 6.5`) |
| `dev/social.py` | the repository's social preview (GitHub, Settings, Social preview) from the same takes: the name, a line, input + depth map (optional) = every effect in two centered rows, each frame at one moment and named at a size that reads (`uv run --with pillow dev/social.py dev/out/record docs/social-preview.png --at 6.5`): `docs/social-preview.png`, uploaded by hand |
| `dev/idle.py` | checks an effect does nothing while its output is unused, input 2 unwired and wired (TD_IDIOMS C5) |
| `dev/testbed.py` | the clip, its depth (input 3, for an effect that takes one) and the stress beat `flash.py`, `perf.py` and `idle.py` feed every effect; the stress beat swings all seven bands fully 8 times a second too, and `beat=song` plays a track as raw audio instead (`song=<name>` for another than `m1x_ease_from_drop`). It finds the clips from the path of the script that runs it, so a probe in `dev/probes/` that exec()s it sets `READY` itself, or it quietly gets TouchDesigner's sample movie |
| `dev/assets.py` | normalize test footage in `private/assets/` (see `PROMPTS.md` there) |
| `dev/realsense_record.py` | record a RealSense camera on the Linux box as test footage: color, its depth (brighter nearer) and the same depth as the RealSense TOP gives it (distance 0-1, black for no reading) |

Nothing under `dev/` goes into a `.tox`.

## Performance notes

Each effect's page states its cost on the reference machine: MacBook Pro, Apple M2 Pro (16 GB),
macOS 15.6, TouchDesigner 2025.33230, at 1280 x 720 input, measured with `dev/perf.py` (CPU and GPU
milliseconds per frame at the defaults, and the frame rate TouchDesigner held) with the Mac
otherwise idle: pause `/tdlib_demo`'s clip (Play off on its Demo page) while measuring. Its memory
counts too: with 15 of its 16 GB in use and 5 GB compressed, Blob Track alone read 7 ms on the GPU
against its page's 2.3 (Schlieren's session, 2026-10-30). The GPU's times wander from run to run as
it changes speed, a third or more (an operator with a fixed amount of work read 0.26 to 0.50 ms
across Paint's runs), so a page gives the median of three runs.

## Releasing

Every change reaches `main` through a pull request. A ruleset on `main` requires one, with the
Checks workflow passing, and allows only squash merges, so each pull request lands as one commit
whose subject is the pull request's title (with its number) and whose message is its description.
Direct pushes and force pushes to `main` are refused, except from the repository's admin, who can
bypass the ruleset when a fix needs it (rewording a merged commit's message, say).

```sh
git switch -c pixel-sort-0.2.0
git push -u origin pixel-sort-0.2.0
gh pr create --title "Pixel Sort 0.2.0: ..." --body "..."
gh pr merge --squash
```

To release, bump `VERSION` in the builders that changed, rebuild them (and any bundle embedding
them) and merge that. The README's Status paragraph names the latest release and what it adds, so
the last pull request before the tag points it at the new one ("README names the v0.4.0 release"),
and the release ships with a README that already describes it. Then tag `main` and push the tag:

```sh
git switch main && git pull
uv run tests/check_tox.py --release v0.4.0
git tag v0.4.0 && git push origin v0.4.0
```

`check_tox.py --release` fails while the README doesn't link the release it names, and the release
workflow runs it too, so a tag the README doesn't name is not released.

`.github/workflows/release.yml` reruns both tests and attaches every `.tox` as its own
release asset with `SHA256SUMS` and build provenance, so
`https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/<name>.tox` always serves the
newest. Its notes list the subject of every commit since the previous tag, so the pull request
titles are the changelog, followed by a link to the full comparison. A release that deserves more
can have a few lines added afterward with `gh release edit <tag> --notes-file <file>`.

## TouchDesigner behaviors found here

Beyond those in [BRIEF.md](BRIEF.md#touchdesigner-behaviors-that-silently-broke-things):

- A COMP orders its inputs by the In operators' names, not their positions on the network
  (2025.33230, `dev/probes/input_order.py`): hence `in1_top`, `in2_audio`, `in3_top`.
- A Switch TOP whose index is `0 if parent().inputConnectors[0].connections else 1` follows
  wiring and unwiring on later frames without a forced cook (`dev/selftest.py`).
- Things that keep an unused effect cooking every frame (`dev/idle.py` finds them): a
  time-sliced CHOP (an Audio Filter CHOP, say) inside it; a Script CHOP that has read its
  input's `.rate` (from then on the input cooks every frame; reading channels, names or
  `numpyArray()` doesn't do this, `dev/probes/in_chop_cook.py`); a size expression such as
  `op('source').width` that keeps a sample movie playing.
- A new Geometry COMP holds a Torus POP and a new Camera COMP a File In POP (2025.33230); a builder
  that draws its own geometry destroys them, or the readability check flags them for lacking comments.
- A GLSL TOP writes several buffers with Number of Color Buffers (`numcolorbufs`) and
  `layout(location = 0) out vec4 fragColor[TD_NUM_COLOR_BUFFERS];`; a Render Select TOP (`top`,
  `bufferindex`) picks one out, and a Feedback TOP can read it back (Particles' three buffers).
- A GLSL TOP's Input Extend Mode UV (`inputextenduv`) defaults to Zero (2025.33230): `texture()` a
  pixel off an input's edge reads black, so a shader that differences neighbors (a slope, a curl)
  sees a cliff at the frame's edges. Particles' sim sets Hold.
- A GLSL TOP's Passes (`npasses`) runs its shader that many times a frame, each pass reading the last
  one's output as `sTD2DInputs[0]` while the other inputs stay put, with `uTDPass` the pass index
  (2025.33230, `dev/probes/glsl_passes.py`): Fluid's 40 Jacobi iterations of the pressure are one TOP.
- A GLSL TOP takes its size from input 0 (Output Resolution at its default, Use Input). Fluid starts its
  Feedback TOPs from a 1 x 1 Constant TOP, so each stateful pass puts a TOP of the size it should be
  first (the picture, the motion) and reads its feedback by UV as a later input; no expression reads
  another operator's size (that kept an unwired sample movie cooking, above).
- A Texture 3D TOP (Type 2D Texture Array works the same) is a ring of Cache Size slots: each cook writes the next
  slot, whether or not its input changed, and nothing says which slot that was (`uTD3DInfos[0].depth.z` isn't it).
  Replace Single with a changing Replace Index writes that slot as well as the next one, so it can't steer the writes;
  Active off skips the write and the ring waits. Slots never written hold garbage, not zeros, and forced cooks inside
  one Python call write nothing (2025.33230, `dev/probes/texture3d.py`, `texture3d_writes.py`). It writes only while
  something pulls it, so its history goes stale while the effect is unused. Slit-Scan stamps every slot with which cook
  wrote it in a third ring beside the picture and its flow, and finds its slots from the stamps.
- A GLSL TOP runs a compute shader with Mode Compute (`mode`), the shader in the DAT it docked as `<name>_compute` (a new
  GLSL TOP docks `_compute`, `_pixel` and `_info`, so a compute TOP fills `_compute` and leaves `_pixel` at its default,
  as a pixel TOP leaves `_compute`). Auto Dispatch Size, on by default, dispatches enough workgroups to tile the output;
  a shader that gives each workgroup one line turns it off and sets Dispatch Size. Shared memory with
  `memoryBarrierShared(); barrier();` works on the Mac, `local_size_x` up to 1024 compiles, and
  `imageStore(mTDComputeOutputs[0], ...)` writes any pixel, not only the invocation's own (2025.33230,
  `dev/probes/compute_sort.py`). Pixel Sort sorts lines of up to 2,048 pixels in shared memory, one workgroup a line.
- `TOP.gpuMemory` gives a TOP's GPU memory in bytes (Slit-Scan's history: 503 MB for 128 slots of 1280 x 720 8-bit,
  about 7% over width x height x 4 x slots). `TOP.sample()` returned red in the alpha place on 32-bit float GLSL
  outputs: don't trust a pixel's alpha read that way.
- A Geometry COMP instances from TOPs, one pixel per instance: Default Instance OP sets the count
  (Instance Count from its length), and Translate, Scale and Color each take their own TOP
  (`instancetop`, `instancesop`, `instancecolorop`) with channels `r`, `g`, `b`, `a`.
- A GLSL TOP's Input Smoothness (`inputfiltertype`) at Mipmap gives its inputs mipmaps, and `textureLod()` reads their
  levels: level 3 of a checkerboard of 1-pixel squares reads 0.502 (2025.33230, `dev/probes/glsl_mipmap.py`). Paint
  reads its brush from the level that averages the pixels between its samples, so a broad brush costs no more than a
  fine one. Only the wired inputs (0 to 2) get mipmaps: an input the TOPs parameter adds (`sTD2DInputs[3]` and on) reads
  its base level at any `textureLod()` (`dev/probes/glsl_mipmap_tops.py`), so Pencil wires its stroke textures. And
  the last level (1 x 1) of a 512 x 512 input's mipmap reads black, as does any level asked for past it; the 2 x 2
  level read at its middle gives the texture's mean (`textureQueryLevels()` counts the 1 x 1 level).
- Passes (`npasses`) with an Output Resolution of Half halves the picture again on every pass (two passes made 320 x
  180 of 1280 x 720), since each pass's input is the last pass's output. Paint's passes are separate TOPs behind a
  Switch.
- TouchDesigner's Python reads a builder's files as ASCII (2025.33230 on macOS): one accented letter in `lib/` or a
  `src/` file stops the build with a UnicodeDecodeError. Sources stay ASCII (Doellner, Winnemoeller); the docs pages,
  which only GitHub reads, keep the accents.
- A Feedback TOP shows black on its first frame, not its input, and alpha 0 with it. A pass that eases toward its own
  last frame writes alpha 1 and takes the new value at once while its feedback's alpha is 0, rather than easing up from
  black (Reaction-Diffusion's where and exposure). Pulsing the Feedback TOP's Reset brings that first frame back.
- A GLSL TOP's Passes can follow the frame (`npasses` an expression of `absTime.stepSeconds`): Reaction-Diffusion runs as
  many steps of its model as the time since the last frame asks for, up to 48, so a dropped frame doesn't slow it.
  One step of a 9-tap pass on 32-bit float RGBA cost 0.055 ms at 640 x 360 and 0.19 ms at 1280 x 720 on the M2 Pro.
- A shader whose every invocation walks a few hundred texels one after another is slow even when the total is small:
  Pixel Art's update of 14,400 superpixels, each summing its 17 x 17 window, took 2.2 ms as a pixel shader on the M2 Pro.
  As a compute shader, one workgroup a superpixel whose 64 invocations share the window and add their sums up in shared
  memory, it took 0.8 ms (2025.33230). A compute GLSL TOP writes several outputs with Number of Color Buffers
  (`mTDComputeOutputs[1]`...).
- A GLSL MAT's vertex shader can place every instance itself: a Geometry COMP with Instance Count Mode Manual
  (`instancecountmode`, `numinstances`) and no instance TOPs, the shader reading a data texture by
  `texelFetch(sTable, ivec2(TDInstanceID(), row), 0)` and writing `gl_Position` in clip space, added up by the
  material's blending (2025.33230, `dev/probes/flare_instancing.py`). A new GLSL MAT docks `_vertex`, `_pixel` and
  `_info`; its samplers are the `sampler` sequence (`sampler0name`, `sampler0top`). Lens Flare draws each ghost of each
  light so, from a Table DAT turned into a texture (DAT to CHOP with one channel a column, CHOP to TOP at 32-bit float).
- A DAT to CHOP's row and column filters (`rowexpr`, `colexpr`) default to expressions of `me.inputCell`, which exists
  only while it cooks, so evaluating them anywhere else fails and `assert_loads_clean` refuses the effect (it passed on
  some builds and not others). Set them constant when the whole table goes through.
- `TOP.save()` of a 1280 x 720 PNG stalls TouchDesigner for a frame or more, so `dev/capture.py` shots scheduled under
  about 0.15 s apart land on the same frame (Paint's beat measurements saw identical frames until they were spread
  out).
- A COMP's own operator parameter (a custom DAT parameter, Words' Text) resolves a plain name among the COMP's siblings,
  as a Geometry COMP's `material` does: `text` finds nothing inside it, and `./text` finds its child, whatever the COMP
  is renamed to (2025.33230, `dev/probes/words_datpar.py`). Its `eval()` is the operator, so `assert_idiomatic`'s P3
  compares such a parameter's path with its default.
- A Select DAT's `extractcols` at `byname` takes the columns from `colnamestart` to `colnameend`; a list of names in
  `colnames` is `bynames`. Its `rowexpr` and `colexpr` default to expressions of `me.inputCell`, as a DAT to CHOP's do,
  and fail the same way outside a cook: set them constant.
- A Text TOP measures text without drawing it: `evalTextSize(text)` gives a word's width and height at its font
  settings, and `ascender` and `descender` the font's. With a Specification DAT of `text`, `x` and `y` columns it
  draws every row in one cook, `x` the left edge and `y` the baseline counted from the bottom (69 words in 0.35 ms of
  CPU), so one Text TOP can draw a whole atlas of words (`dev/probes/words_text.py`). A Script DAT whose callback reads
  a parameter cooks again when that parameter changes, which is how Words' word list follows Font and Case.
- Shared-memory atomics (`atomicOr`, `atomicMax`, `atomicMin`, `atomicAdd`) work in a compute shader on the Mac, and
  28 KB of shared memory compiles (2025.33230, `dev/probes/words_text.py`). Words keeps its grid of free cells as bits
  and picks the best spot for a word with one `atomicMax` on a key.
- A GLSL TOP can keep its own past outputs in a Texture 3D ring and read them back: a Render Select TOP picks the buffer,
  a Feedback TOP targeting it hands the ring the last cook's output, and the GLSL TOP reads the ring as a 2D array, with
  no cook loop (2025.33230). A stamp written the same way into a second ring beside it says which cook made each slot:
  the newest slot holds the last cook's serial. Temporal Resonator's strings read their state from a beat back so.
- A compute GLSL TOP can tally into shared memory with `atomicAdd` on `uint`: three `uint` arrays of 48 x 48 (27.6 KB)
  compile and run on the Mac, and Auto Dispatch Size tiles the output with workgroups of the shader's local size
  (2025.33230). Caustics gathers its light so, each 16 x 16 workgroup tallying in 256ths every surface sample's square
  that lands in its patch from within 16 pixels, in about 0.9 ms for 640 x 360 on the M2 Pro.
- A TOP's GPU cook time (`gpuCookTime`, and so `dev/perf.py`'s list of the costliest operators) can carry another
  operator's work: of a dozen Blur TOPs on one Noise TOP, whichever cooked first read about 3 ms at any size and the rest
  0.003 ms (2025.33230, `dev/probes/blur_cost.py`). Relight's two smallest blurs read 0.7 and 1.0 ms that way. Read the
  per-operator times as a guide to where the cost is, and the effect's total as its cost.
- The Blur TOP's Type (`type`) offers `catmull`, `gaussian`, `box`, `bartlette` (a triangle), `sinc`, `hanning` and
  `blackman` (2025.33230, `dev/probes/blur_pars.py`). Relight's broad smoothings are triangles, since it never adds two
  Gaussian blurs together (its docs page, Credits and license).
