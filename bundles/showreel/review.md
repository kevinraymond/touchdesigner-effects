# showreel: idiom review

Reviewed version: 0.1.0

The review items of docs/TD_IDIOMS.md, checked by hand for this version: tick each box
(`- [x]`) and say in a few words how it holds.

- [x] P4 Pulse for actions, Toggle for states, Menu for discrete choices; labels in Title Case. Names of 10 characters or fewer are checked at save time (assert_idiomatic); TouchDesigner itself refuses names that aren't an uppercase letter followed by lowercase letters or digits. [Custom Parameters](https://docs.derivative.ca/Custom_Parameters), [Page Class](https://docs.derivative.ca/Page_Class)
  Menu for View (discrete choices) and Flashing; Toggle for Labels and Full Screen; Int for Every and Display; Pulses for Open Window and Open Docs. Labels in Title Case; names are 10 characters or fewer (save-time check passes). The effects inside keep their own reviewed pages.
- [x] P5 Inner operators follow the COMP's parameters through expressions (`parent().par.Amount`), not scripts copying values; values only the inside needs are kept off the pages (`ipar`). [Internal Parameters](https://docs.derivative.ca/Internal_Parameters)
  The page drives the inside through expressions: view's index (parent().par.View, Every through the cycle CHOP), grid's and label's uniforms (parent().par.Labels), and every embedded effect's Flashing (parent().par.Flashing). No script copies values. The tile layout, names, the 2 s bar and the 2 s minimum gap live in the builder and src/, off the page.
- [x] P6 Related parameters are grouped with `startSection`; parameters that don't apply in the current mode are grayed out with `enableExpr`.
  Sections: View, Every and Labels; then Flashing; then the window. Every is grayed out unless View is Cycle (enableExpr); Labels applies to every view.
- [x] I4 The audio input goes through `audio_in()`, which reads it by channel name with fallbacks and takes a pulse from its count channel when one exists, because a one-frame pulse is lost on any frame nothing pulls the CHOP; the effect reads the counts (`beat_count`, `bar_count`...) for logic, not `beat`. [Cook](https://docs.derivative.ca/Cook), [Logic CHOP](https://docs.derivative.ca/Logic_CHOP)
  Input 2 reaches each embedded effect unchanged (each goes through its own audio_in()); the showreel's own audio_in() feeds only cycle, which reads the bar_count and source channels, never the one-frame beat pulse.
- [x] E2 Only capitalized members are promoted; state lives on `self` and the extension can be reinitialized at any time; no module globals; `onInitTD`/`onDestroyTD`, the 2025 names. [Release Notes 2025](https://docs.derivative.ca/Release_Notes/2025.30000)
  No extension in the showreel; the effects inside have none either.
- [x] C4 Motion and timing follow seconds (`absTime.seconds`, `me.time.seconds`), not frame counts, so dropped frames don't change the speed. [AbsTime Class](https://docs.derivative.ca/AbsTime_Class)
  Cycle's timing is in seconds: src/cycle.py reads absTime.seconds for the 2 s bar without music and the 2 s minimum gap, and counts input 2's bars; dev/probes/showreel_cycle.py measured moves exactly 2.0 s apart with nothing wired and under a 2-bars-a-second beat at Every 1. Nothing counts frames.
- [x] C5 Nothing cooks while the output is unused: checked with `dev/idle.py` (nothing downstream, the node out of view; input 2 unwired and wired to a changing beat), or in the Performance Monitor. [Performance Monitor](https://docs.derivative.ca/Performance_Monitor_Dialog)
  dev/idle.py on the 0.1.0 build with ascii, blob_track, datamosh and glitch inside (node viewer off, nothing downstream): 0 of 323 operators cooked over 60 frames unused, with input 2 unwired and with the clip and a changing beat wired in; the control cooked 198 and 203. The cycle CHOP and its clock cook only while View is Cycle (the view reads them only then); the Switch TOP cooks only the view shown.
- [x] C6 Pixel formats are 8-bit unless precision is needed, and 32-bit float for data textures (a CHOP to TOP feeding a shader).
  grid and label are 8-bit (the pictures); the Null TOPs pass each effect's own format; no data textures of its own (the effects inside keep their reviewed formats).
- [x] C7 The performance note on the docs page was measured on the reference machine at 1280 x 720, not estimated.
  dev/perf.py on the 0.1.0 build with ascii, blob_track, datamosh and glitch inside (MacBook Pro M2 Pro 16 GB, macOS 15.6, TouchDesigner 2025.33230), 1280 x 720: Grid (default) GPU 9.18 ms (95th percentile 11.22), CPU 2.17 ms (2.41); Cycle GPU 2.94 ms (5.58), CPU 0.78 ms (1.20); 60 fps held in both. Remeasured whenever the effects inside change.
- [x] D5 The README DAT and docs page say how to update: dragging a `.tox` in embeds a copy, so updating means dragging in the new one (or pointing External .tox at it). [A word about external files](https://derivative.ca/community-post/word-about-external-files-202310k-builds/68166)
  The README DAT's UPDATING section and the docs page's Use it section say to delete the copy and drag in the new showreel.tox; both say a new effect in the library means a new showreel.
- [x] A2 The flash limits were measured, not assumed: the output recorded with a beat-heavy input at each Flashing setting, and the flashes in any one second counted.
  dev/flash.py + dev/flashcount.py on the 0.1.0 build with the four effects inside, stress beat of 8 beats, 2 bars and 1 drop a second. Worst second, area rule: Grid on the dancer Off 0.5, Calm 1.0, Up to 3 per second 2.0 (clip alone 1.0); Grid on the plaza 0.5, 1.0, 2.0 (clip 0.5; Grid remeasured after its cells were packed into one 16:9 block); Cycle at Every 1 on the dancer (a cut every 2 s, the fastest it allows) 1.0, 2.0, 3.0 (clip 1.0). Red flashes only in Cycle: Calm 0.5, Up to 3 per second 1.0 (Glitch's fringes). All within flashcount's bars.
- [x] A3 No meaning rests on hue alone (brightness, size or motion carries it too); the palette is colorblind-safe (orange and blue); text is legible at the size it is shown.
  The names are white (0.9) on a 60% dark plate, so they read by brightness on light and dark pictures, in the 5 x 7 font at 2 px per font pixel in the grid and 3 in single views (at 720 high); checked on saved frames of every view. No meaning rests on color; the effects inside keep their reviewed palettes.
- [x] A4 Anything unreliable is labeled experimental in its help and docs.
  Nothing of the showreel's own is unreliable; the experimental parts of the effects inside (Fosfora's drops, the raw-audio kick detector) are labeled in their own help and pages.
