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
                              depth_find.glsl (what stands in front of its surroundings)
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
glsl = mk(comp, glslTOP, 'glsl', 0, 0, [source], comment='What this step does.')
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
  their Window COMP, the About page (Version, Built With, Open Docs), and shows the output
  on the node.
- `save_effect()` runs the save-time checks, saves, and writes the manifest.

Helpers: `mk()` creates, places, comments, sets parameters and wires in one call (`Expr('...')`
for an expression); `custom()` adds a parameter with its default, range and help text;
`docked()` fills the DAT TouchDesigner docked to an operator (a GLSL TOP's `_pixel`, a Script
CHOP's callbacks) instead of adding a second one; `glsl()` makes a GLSL TOP in one call (docked
shader filled, any number of inputs: past the third they go through its TOPs parameter, the
only way that works), and `uniforms()` sets its vector uniforms; `flash_gate()` is the one way
an effect may flash (below); `lib_module(_ROOT, 'font5x7')` loads another `lib/` file, such as
the bitmap font (`glsl_font()` gives the shader `glyph(g, p)`; `ramp()` orders glyphs by ink), and
`lib_glsl(_ROOT, 'depth_near.glsl')` a shared shader.

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
- it isn't readable inside: no README or one without its CREDITS, an operator without a comment,
  a parameter without help, the About page incomplete, no tags, another node color, a node smaller than 480 x 270;
- the inputs aren't a TOP then optionally a CHOP and a TOP, the output isn't one TOP, or anything
  inside makes sound (an Audio Device Out, whose saved state would play the moment a project
  opens);
- an operator renders larger than the Non-Commercial license's 1280 x 1280;
- it breaks a TouchDesigner idiom a script can judge (`assert_idiomatic`, items named in
  [TD_IDIOMS.md](TD_IDIOMS.md)): pages out of order, Version editable, a parameter saved off its
  default, a node that doesn't show the output, extensions not initialized on start, a Script
  CHOP not cooking `WHEN_USED`, Python every frame or a forced cook, or a flashing effect
  without the standard Flashing parameter;
- it doesn't load clean (`assert_loads_clean`): any error or warning with nothing wired, in it
  or in a second copy beside it. TouchDesigner reports a GLSL compile error as a warning, so
  warnings count.

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
definitions and area rule (see The dev loop).

## The audio input

An effect built with `new_effect(..., audio=True)` reads input 2 through `audio_in(comp, _ROOT)`,
which turns whatever is wired there into the same channels on the CHOP `audio`:

| Channel | Value |
|---|---|
| `beat` | 1 on the frame a beat arrives, else 0 |
| `beat_count` | beats so far; for logic, watch the counts, since a one-frame pulse can be missed |
| `bar_count` | bars so far: Fosfora's `bar_count` (or `downbeat` pulses), else one every 4 beats |
| `beat_phase` | 0 to 1 through the current beat: Fosfora's, else timed from the last beats |
| `level` | 0 to 1, how loud right now |
| `build` | 0 to 1, how far into a build: Fosfora only, else 0 |
| `drop_count` | drop-like moments so far: Fosfora's `drop_count` (experimental there), else 0 |
| `section_count` | section changes so far: Fosfora's `boundary_count`, else 0 |
| `source` | 0 nothing, 1 raw audio, 2 analysis channels, 3 Fosfora's signal |

Input 2 may carry:

- [Fosfora](https://github.com/kevinraymond/fosfora)'s signal (`fosfora_signal.tox`): every
  channel comes from it, so an effect can follow bars, builds, drops and sections as well as beats;
- raw audio (Audio File In, Audio Device In): the low band's loudness (30 to 150 Hz, from an FFT
  of the last 40 ms) gives `level`, and a jump above its recent average gives a beat;
- other analysis channels, by name: beats from `beat_count`, or the rising edge of `beat`, `kick`
  or `onset` (TouchDesigner's audioAnalysis and Essentia rhythm CHOPs); level from `energy`,
  `level`, `low`, `bass` or `rms`;
- nothing: no beats, level 0, and the effect still works.

It is one Script CHOP that cooks only when something uses it, so the audio front end does
nothing while the effect's output is unused (TD_IDIOMS C5). An earlier version measured raw
audio's low band with a time-sliced Audio Filter CHOP, which cooked every frame, used or not.

An effect works with any of them and is at its best on Fosfora's signal: `build`, `drop_count` and
`section_count` stay at 0 without it, so use them for extra moments, never for the effect's
basic behavior. `lib/audio_callbacks.py` holds the logic. `dev/selftest.py` feeds it each kind
of input for 3 s: nothing gives 0 beats; `beat_count` and `kick` at 2 a second give 6 (and 1 or 2
bars); a Fosfora-shaped input passes its bars, build and beat phase through; TouchDesigner's
sample MP3 gives 6 (about 120 BPM). Beats that make the picture flash still go through
`flash_gate()`.

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
| `dev/record.py` + `dev/clips.py` | record effects as video with sound (Motion JPEG: the free license can't encode H.264), then MP4s and docs previews (`uv run dev/clips.py dev/out/record --preview`) |
| `dev/tile.py` | tile several effects' recordings into one labeled grid preview, in the library's font (the Showreel's page: `uv run --with pillow dev/tile.py dev/out/record --names ... --titles ... --out docs/effects/showreel`) |
| `dev/idle.py` | checks an effect does nothing while its output is unused, input 2 unwired and wired (TD_IDIOMS C5) |
| `dev/testbed.py` | the clip, its depth (input 3, for an effect that takes one) and the stress beat `flash.py`, `perf.py` and `idle.py` feed every effect |
| `dev/assets.py` | normalize test footage in `private/assets/` (see `PROMPTS.md` there) |
| `dev/realsense_record.py` | record a RealSense camera on the Linux box as test footage: color, its depth (brighter nearer) and the same depth as the RealSense TOP gives it (distance 0-1, black for no reading) |

Nothing under `dev/` goes into a `.tox`.

## Performance notes

Each effect's page states its cost on the reference machine: MacBook Pro, Apple M2 Pro
(16 GB), macOS 15.6, TouchDesigner 2025.33230, at 1280 x 720 input, measured with `dev/perf.py`
(CPU and GPU milliseconds per frame at the defaults, and the frame rate TouchDesigner held) with
the Mac otherwise idle.

## Releasing

Bump `VERSION` in the builders that changed, rebuild them (and any bundle embedding them),
commit, then tag and push:

```sh
git tag v0.1.0 && git push origin v0.1.0
```

`.github/workflows/release.yml` reruns both tests and attaches every `.tox` as its own
release asset with `SHA256SUMS` and build provenance, so
`https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/<name>.tox` always serves the
newest.

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
- A Geometry COMP instances from TOPs, one pixel per instance: Default Instance OP sets the count
  (Instance Count from its length), and Translate, Scale and Color each take their own TOP
  (`instancetop`, `instancesop`, `instancecolorop`) with channels `r`, `g`, `b`, `a`.
