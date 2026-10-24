Showreel {v}: every touchdesigner-effects effect in one component. MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/showreel.md

Every effect in the library at the time this was built, each a full copy you can open and change:
{effects}

USE
Drag showreel.tox into your network: it shows a 5-second clip of a dancer (inside this component,
AI-generated footage, CC BY 4.0, no sound) through every effect straight away. Wire any TOP into
input 1; every effect gets it. Optionally wire audio or beat channels into input 2 (Fosfora's signal
is the best; see each effect's docs): every effect gets that too. Open Window shows it full size;
Esc closes the window.

VIEW
Grid: the input and every effect side by side, each named in its corner. Every effect runs.
Cycle: one effect at a time, moving on every Every bars of input 2's music (a bar is 2 s while no
bars arrive), never within 2 s of the last move, named in the bottom-left corner. Only the effect
showing runs.
One effect by name: that one alone, full size. Only it runs.
Labels turns the names off. Flashing applies to every effect inside (Off, Calm, the default, or Up
to 3 per second, the WCAG 2.3.1 limit); each effect's own help says what it flashes.

INSIDE
source (input 1, or the sample movie) feeds each effect; in2_audio feeds each effect's input 2 and
audio (lib audio_in), whose bars, with a clock, drive cycle (a Script CHOP: when Cycle moves on).
Each effect's output goes through a Null TOP (fx_<name>) to grid (a GLSL TOP tiling the input and
every effect with their names) and to view, a Switch TOP that picks Grid, the effect Cycle has
reached, or the effect chosen; a Switch TOP cooks only the input it shows. label names the effect
showing. The effects inside are the released .tox files, unchanged except that their Flashing
follows this component's and their node viewers are off.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new showreel.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest. A new effect in the library
means a new showreel. The version and the build it was saved in are on the About page.
