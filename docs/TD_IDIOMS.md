# TouchDesigner idioms every effect follows

What an experienced TouchDesigner developer expects of a component they download, adapted
from the checklist `fosfora_signal.tox` and its examples were polished against (2026-10-23;
Derivative's documentation first, Derivative's own TDAbleton and audioAnalysis as models).

Each item is one of:

- **auto**: a check refuses to save the `.tox` (or `tests/check_tox.py` fails) when it doesn't
  hold. The check is named; `dev/selftest.py` or `tests/test_guards.py` breaks each one on purpose.
- **review**: a script can't judge it. Every effect carries `effects/<name>/review.md` with each
  review item checked off for its current version, and `tests/check_tox.py` fails while a box is
  open, the review is for an older version, or this list has gained an item the review lacks.
  Start one with `uv run tests/check_tox.py --review-template <name>`.

## Parameters

- **P1** (auto: assert_idiomatic) The effect's own settings are on the first page; the About
  page comes last, with read-only Version and Built With and an Open Docs pulse.
  [Component Editor](https://docs.derivative.ca/Component_Editor),
  [audioAnalysis](https://docs.derivative.ca/Palette:audioAnalysis)
- **P2** (auto: assert_readable) Every parameter has help text (Alt+hover shows it).
  [Par Class](https://docs.derivative.ca/Par_Class)
- **P3** (auto: assert_idiomatic) Saved at its defaults: every parameter holds its default, so
  right-click Reset returns to the state that shipped. [Par Class](https://docs.derivative.ca/Par_Class)
- **P4** (review) Pulse for actions, Toggle for states, Menu for discrete choices; labels in Title
  Case; names of 10 characters or fewer (TouchDesigner itself refuses names that aren't an
  uppercase letter followed by lowercase letters or digits).
  [Custom Parameters](https://docs.derivative.ca/Custom_Parameters), [Page Class](https://docs.derivative.ca/Page_Class)
- **P5** (review) Inner operators follow the COMP's parameters through expressions
  (`parent().par.Amount`), not scripts copying values; values only the inside needs are kept off
  the pages (`ipar`). [Internal Parameters](https://docs.derivative.ca/Internal_Parameters)
- **P6** (review) Related parameters are grouped with `startSection`; parameters that don't apply
  in the current mode are grayed out with `enableExpr`.

## Inputs, outputs and the node

- **I1** (auto: assert_standard_io) Input 1 a TOP, optional input 2 a CHOP, output 1 a TOP. A COMP
  orders its inputs by the In operators' names, so the names carry the order (`in1_top`, `in2_audio`).
- **I2** (auto: assert_idiomatic) The node shows the output (viewer on, Node View pointing at
  `out_top`) at a size that reads. [Base COMP](https://docs.derivative.ca/Base_COMP)
- **I3** (auto: assert_loads_clean) It works with nothing wired, as a drag-in leaves it: no errors
  or warnings, the sample picture through the effect; a second copy beside the first works too.
- **I4** (review) The audio input is read by channel name, with a sensible fallback when a channel
  is missing; a pulse is taken from its count channel when one exists, because a one-frame pulse is
  lost on any frame nothing pulls the CHOP. [Cook](https://docs.derivative.ca/Cook),
  [Logic CHOP](https://docs.derivative.ca/Logic_CHOP)

## Extensions (when an effect has one)

- **E1** (auto: assert_idiomatic) Init Extensions on Start is on; otherwise extensions start lazily.
  [Extensions](https://docs.derivative.ca/Extensions)
- **E2** (review) Only capitalized members are promoted; state lives on `self` and the extension
  can be reinitialized at any time; no module globals; `onInitTD`/`onDestroyTD`, the 2025 names.
  [Release Notes 2025](https://docs.derivative.ca/Release_Notes/2025.30000)

## Cooking and performance

- **C1** (auto: assert_idiomatic) Script CHOPs return `CookLevel.WHEN_USED` from `onGetCookLevel`.
  [ScriptCHOP Class](https://docs.derivative.ca/ScriptCHOP_Class)
- **C2** (auto: assert_idiomatic) Nothing runs Python every frame or forces a cook: no Execute DAT
  with Frame Start or Frame End on, no `cook(force=True)` in a script. Operators do the work.
  [Optimize](https://docs.derivative.ca/Optimize)
- **C3** (auto: assert_nc_resolution) Nothing renders above 1280 x 1280, the Non-Commercial cap.
- **C4** (review) Motion and timing follow seconds (`absTime.seconds`, `me.time.seconds`), not frame
  counts, so dropped frames don't change the speed. [AbsTime Class](https://docs.derivative.ca/AbsTime_Class)
- **C5** (review) Nothing cooks while the output is unused: checked in the Performance Monitor
  with nothing wired downstream and the node out of view.
  [Performance Monitor](https://docs.derivative.ca/Performance_Monitor_Dialog)
- **C6** (review) Pixel formats are 8-bit unless precision is needed, and 32-bit float for data
  textures (a CHOP to TOP feeding a shader).
- **C7** (review) The performance note on the docs page was measured on the reference machine at
  1280 x 720, not estimated.

## Distribution

- **D1** (auto: assert_self_contained) Nothing points outside the component: no External .tox
  path, Clone master, Global OP Shortcut, absolute path or `op('/...')`, except TouchDesigner's
  own `/sys` and `/ui`. [Global OP Shortcut](https://docs.derivative.ca/Global_OP_Shortcut)
- **D2** (auto: assert_no_unused_docked) The DATs TouchDesigner docks to an operator are filled,
  not duplicated.
- **D3** (auto: assert_readable) A README DAT, a comment on every operator, tags, the library
  color, a node large enough to read. [OP Snippets](https://docs.derivative.ca/OP_Snippets)
- **D4** (auto: check_tox.py) The docs page states the build the `.tox` was saved in (newer builds
  open older files, not the reverse) and links `releases/latest/download/<name>.tox`.
  [Release Notes 2023](https://docs.derivative.ca/Release_Notes/2023.10000)
- **D5** (review) The README DAT and docs page say how to update: dragging a `.tox` in embeds a
  copy, so updating means dragging in the new one (or pointing External .tox at it).
  [A word about external files](https://derivative.ca/community-post/word-about-external-files-202310k-builds/68166)

## Accessibility and honesty

- **A1** (auto: assert_idiomatic) An effect that can flash is built with `flashing=True`, which tags
  it and adds the standard Flashing parameter: Off never flashes; Calm, the default, allows at most
  one flash per second; the most any setting allows is three per second
  ([WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)).
- **A2** (review) The flash limits were measured, not assumed: the output recorded with a
  beat-heavy input at each Flashing setting, and the flashes in any one second counted.
- **A3** (review) No meaning rests on hue alone (brightness, size or motion carries it too); the
  palette is colorblind-safe (orange and blue); text is legible at the size it is shown.
- **A4** (review) Anything unreliable is labeled experimental in its help and docs.
