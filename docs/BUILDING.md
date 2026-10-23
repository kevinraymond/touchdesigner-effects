# Building the library

Every `.tox` here is generated, never edited by hand. A builder script assembles each one
inside TouchDesigner from plain source files (shaders, callbacks), checks it, and saves it
with a manifest beside it. Review the sources; ship the `.tox`.

## Layout

```
lib/tox_build.py              shared by every builder: the standard effect shell, save-time checks, manifests
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
__file__ = '/path/to/tdlib/effects/glow/build_glow.py'; exec(open(__file__).read())
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
CHOP's callbacks) instead of adding a second one.

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
- an operator renders larger than the Non-Commercial license's 1280 x 1280.

`dev/selftest.py` breaks each of these once inside TouchDesigner and checks it refuses, and
checks that the intact effect loads elsewhere without errors, as a drag-in would.

## Manifests and the stale-file test

`<name>.json` records the effect's version, the TouchDesigner build it was saved in, a hash
of its sources (`lib/tox_build.py`, the builder, everything in `src/`) and a hash of the
`.tox`. A bundle's also records the hash of every `.tox` it embeds.

`tests/check_tox.py` fails when a source changed since the last build, the `.tox` isn't the
file its manifest describes, the builder's `VERSION` isn't the built one, an effect has no docs
page (or it doesn't link `releases/latest/download/<name>.tox`, or its preview is missing), or
a bundle embeds an older build. `tests/test_guards.py` breaks each of those on purpose. Both run
in CI and before every commit:

```sh
git config core.hooksPath .githooks      # once per clone
uv run tests/test_guards.py
uv run tests/check_tox.py
```

Because the source hash covers `lib/tox_build.py`, changing it means rebuilding every effect.

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
`https://github.com/kevinraymond/tdlib/releases/latest/download/<name>.tox` always serves the
newest.

## TouchDesigner behaviors found here

Beyond those in [BRIEF.md](BRIEF.md#touchdesigner-behaviors-that-silently-broke-things):

- A COMP orders its inputs by the In operators' names, not their positions on the network
  (2025.33230, `dev/probes/input_order.py`): hence `in1_top`, `in2_audio`.
- A Switch TOP whose index is `0 if parent().inputConnectors[0].connections else 1` follows
  wiring and unwiring on later frames without a forced cook (`dev/selftest.py`).
