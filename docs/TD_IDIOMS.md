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
  Case. Names of 10 characters or fewer are checked at save time (assert_idiomatic);
  TouchDesigner itself refuses names that aren't an uppercase letter followed by lowercase
  letters or digits.
  [Custom Parameters](https://docs.derivative.ca/Custom_Parameters), [Page Class](https://docs.derivative.ca/Page_Class)
- **P5** (review) Inner operators follow the COMP's parameters through expressions
  (`parent().par.Amount`), not scripts copying values; values only the inside needs are kept off
  the pages (`ipar`). [Internal Parameters](https://docs.derivative.ca/Internal_Parameters)
- **P6** (review) Related parameters are grouped with `startSection`; parameters that don't apply
  in the current mode are grayed out with `enableExpr`.

## Inputs, outputs and the node

- **I1** (auto: assert_standard_io) Input 1 a TOP, optional input 2 a CHOP, optional input 3 a TOP
  (depth or a mask, after the audio, so input 2 is always the audio), output 1 a TOP, and no sound.
  A COMP orders its inputs by the In operators' names, so the names carry the order (`in1_top`,
  `in2_audio`, `in3_top`).
- **I2** (auto: assert_idiomatic) The node shows the output (viewer on, Node View pointing at
  `out_top`) at a size that reads. [Base COMP](https://docs.derivative.ca/Base_COMP)
- **I3** (auto: assert_loads_clean) It works with nothing wired, as a drag-in leaves it: no errors
  or warnings, the sample picture through the effect; a second copy beside the first works too.
- **I4** (review) The audio input goes through `audio_in()`, which reads it by channel name with
  fallbacks and takes a pulse from its count channel when one exists, because a one-frame pulse is
  lost on any frame nothing pulls the CHOP; the effect reads the counts (`beat_count`, `bar_count`...) for logic, not `beat`. [Cook](https://docs.derivative.ca/Cook),
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
  A parameter expression that follows the clock (`absTime.seconds` driving a uniform or a
  transform) is the idiomatic way to animate and doesn't count.
  [Optimize](https://docs.derivative.ca/Optimize)
- **C3** (auto: assert_nc_resolution) Nothing renders above 1280 x 1280, the Non-Commercial cap.
- **C4** (review) Motion and timing follow seconds (`absTime.seconds`, `me.time.seconds`), not frame
  counts, so dropped frames don't change the speed. [AbsTime Class](https://docs.derivative.ca/AbsTime_Class)
- **C5** (review) Nothing cooks while the output is unused: checked with `dev/idle.py` (nothing
  downstream, the node out of view; input 2 unwired and wired to a changing beat), or in the
  Performance Monitor. [Performance Monitor](https://docs.derivative.ca/Performance_Monitor_Dialog)
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
- **D3** (auto: assert_readable) A README DAT with a CREDITS section and one line per paragraph, a
  comment on every operator, tags, the library color, a node large enough to read.
  [OP Snippets](https://docs.derivative.ca/OP_Snippets)
- **D4** (auto: check_tox.py) The docs page states the build the `.tox` was saved in (newer builds
  open older files, not the reverse) and links `releases/latest/download/<name>.tox`.
  [Release Notes 2023](https://docs.derivative.ca/Release_Notes/2023.10000)
- **D5** (review) The README DAT and docs page say how to update: dragging a `.tox` in embeds a
  copy, so updating means dragging in the new one (or pointing External .tox at it).
  [A word about external files](https://derivative.ca/community-post/word-about-external-files-202310k-builds/68166)
- **D6** (review) Provenance: the README DAT's CREDITS and the docs page's Credits and license name
  every paper, technique, project, code, font, model and media the effect uses, follows or was
  built after, with links and licenses, and call original only what was designed here and has no
  earlier source after a search. Code recalled from elsewhere that can't be traced is replaced,
  never called original; code taken from elsewhere is also credited where it sits (a comment in
  the shader or script). D3 and check_tox.py only see that the sections exist.
- **D7** (auto: assert_laid_out) The network reads left to right in Network Boxes titled with what
  each part does: every operator in one box, nothing overlapping, each docked DAT under its
  operator, every wire running left to right (docs/BUILDING.md, Laying out the network).
  [Network Box](https://docs.derivative.ca/Annotate_COMP)

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
