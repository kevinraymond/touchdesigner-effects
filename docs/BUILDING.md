# Building the library

Every `.tox` here is generated, never edited by hand. A builder script assembles each one
inside TouchDesigner from plain source files (shaders, callbacks), checks it, and saves it
with a manifest beside it. Review the sources; ship the `.tox`.

## Layout

```
lib/tox_build.py              shared by every builder: the standard effect shell, helpers, save-time checks, manifests
lib/font5x7.py                a 5 x 7 bitmap font for text drawn in shaders (labels, glyph grids)
lib/audio_callbacks.py        the audio input's logic (audio_in() puts it in a Script CHOP)
effects/<name>/
  build_<name>.py             the builder (has a VERSION = 'x.y.z' line)
  src/                        what it is built from: *.glsl, *.py
  <name>.tox, <name>.json     built in TouchDesigner, committed together
bundles/<name>/               same shape; a bundle embeds effects (the showreel)
docs/effects/<name>.md        the effect's page, its preview beside it (_template.md to start)
tests/check_tox.py            the stale-file test
tests/test_guards.py          breaks each rule check_tox.py enforces, once, and checks it fails
dev/                          dev loop and self-test; never shipped
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
  from `app.samplesFolder` until something is wired in, and with `audio=True`, `in2_audio`
  (input 2, an optional CHOP).
- `finish_effect()` adds `out_top`, the Open Window / Fill Display / Display parameters and
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
the bitmap font (`glsl_font()` gives the shader `glyph(g, p)`; `ramp()` orders glyphs by ink).

## Save-time checks

`save_tox()` refuses to save, naming each offender, when:

- anything points outside the component: an external `.tox`, a clone, a global shortcut, an
  operator parameter or expression naming an absolute path, a script calling `op('/...')`,
  or a file parameter with an absolute path (sample media comes from `app.samplesFolder`).
  TouchDesigner's own `/sys` and `/ui` are allowed;
- a docked DAT is unused (the builder wired its own beside it);
- it isn't readable inside: no README, an operator without a comment, a parameter without
  help, the About page incomplete, no tags, another node color, a node smaller than 480 x 270;
- the inputs aren't a TOP then optionally a CHOP, or the output isn't one TOP;
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

## Flashing

Every effect follows [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html).
One that can flash is built with `new_effect(..., flashing=True)`, which adds the standard
Flashing parameter: Off never flashes; Calm, the default, allows at most one flash a second;
Up to 3 per second is the WCAG limit, which no setting exceeds. Every flash goes through
`flash_gate(comp, trigger, x, y)`: a Trigger CHOP whose Re-Trigger Delay follows the setting
(`FLASH_INTERVAL`) and a Math CHOP that passes nothing when it is Off. `dev/selftest.py` feeds
it 4 pulses a second for 6 s: Off lets 0 through, Calm 6, Up to 3 per second 16. The effect
shapes the flash after the gate, and the limits are measured again on its output before release
(TD_IDIOMS.md A2).

## The audio input

An effect built with `new_effect(..., audio=True)` reads input 2 through `audio_in(comp, _ROOT)`,
which turns whatever is wired there into four channels on the CHOP `audio`: `beat` (1 on the
frame a beat arrives), `beat_count` (watch it for logic: a one-frame pulse can be missed),
`level` (0 to 1) and `source` (0 nothing, 1 raw audio, 2 analysis channels). Input 2 may carry:

- raw audio (Audio File In, Audio Device In): the low band's loudness gives `level`, and a jump
  above its recent average gives a beat;
- analysis channels, by name: beats from `beat_count` (Fosfora), or the rising edge of `beat`,
  `kick` or `onset` (Fosfora, TouchDesigner's audioAnalysis and Essentia rhythm CHOPs); level from
  `energy`, `level`, `low`, `bass` or `rms`;
- nothing: no beats, level 0, and the effect still works.

`lib/audio_callbacks.py` holds the logic. `dev/selftest.py` feeds it each kind of input for 3 s:
nothing gives 0 beats; `beat_count` and `kick` at 2 a second give 6; TouchDesigner's sample MP3
gives 6 (about 120 BPM). Beats that make the picture flash still go through `flash_gate()`.

## Manifests and the stale-file test

`<name>.json` records the effect's version, the TouchDesigner build it was saved in, a hash
of its sources (every `lib/*.py`, the builder, everything in `src/`) and a hash of the
`.tox`. A bundle's also records the hash of every `.tox` it embeds.

`tests/check_tox.py` fails when a source changed since the last build, the `.tox` isn't the
file its manifest describes, the builder's `VERSION` isn't the built one, an effect has no docs
page (or it doesn't link `releases/latest/download/<name>.tox`, doesn't state the build the
`.tox` was saved in, or its preview is missing), an effect's idiom review is missing or out of
date (above), or a bundle embeds an older build. `tests/test_guards.py` breaks each of those on purpose. Both run
in CI and before every commit:

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

Nothing under `dev/` goes into a `.tox`.

## Performance notes

Each effect's page states its frame rate on the reference machine: MacBook Pro, Apple M2 Pro
(16 GB), macOS 15.6, TouchDesigner 2025.33230, at 1280 x 720 input.

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
  (2025.33230, `dev/probes/input_order.py`): hence `in1_top`, `in2_audio`.
- A Switch TOP whose index is `0 if parent().inputConnectors[0].connections else 1` follows
  wiring and unwiring on later frames without a forced cook (`dev/selftest.py`).
