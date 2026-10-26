Showreel {v}: every touchdesigner-effects effect in one component. MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/showreel.md

Every effect in the library at the time this was built, each a full copy you can open and change:
{effects}

USE
Drag showreel.tox into your network: it shows a 5-second clip of a dancer and her depth map (inside this component, AI-generated footage, CC BY 4.0, no sound) through every effect straight away. Wire any TOP into input 1; every effect gets it. Optionally wire audio or beat channels into input 2 (Fosfora's signal is the best; see each effect's docs): every effect gets that too. Optionally wire a depth map or mask lined up with input 1 into input 3 (grayscale, brighter nearer or inside): the effects that use depth get it. Without it they get the dancer's depth while she is showing, else none, and work without. Open Window shows it full size; Esc closes the window.

VIEW
Cycle, the default: one effect at a time, full size, named in the bottom-left corner, fading to the next over 1 s every Every bars of input 2's music (a bar is 2 s while no bars arrive), never within 2 s of the last move. Only the effect showing runs, two during a fade. One effect by name: that one alone, full size. Only it runs. Labels turns the names off. Flashing applies to every effect inside (Off, Calm, the default, or Up to 3 per second, the WCAG 2.3.1 limit); each effect's own help says what it flashes. A fade changes the whole picture once, so while Cycle fades and for a second after, Up to 3 per second holds the effects to Calm.

INSIDE
source (input 1, or the sample movie) feeds each effect; depth (input 3, else depth_stand_in: the dancer's depth, sample_depth, while she shows, or no_depth, black) feeds the input 3 of each effect that has one; in2_audio feeds each effect's input 2 and audio (lib audio_in), whose bars, with a clock, drive cycle (a Script CHOP: when Cycle moves on). Each effect's output goes through a Null TOP (fx_<name>) to view, a Switch TOP that picks the effect Cycle has reached (blending from the last one while it fades) or the effect chosen; a Switch TOP cooks only the inputs it shows. The first effect is wired into view again last, so the fade from the last effect back to the first blends neighbors too. label names the effect showing. The effects inside are the released .tox files, unchanged except that their Flashing follows this component's (Calm around Cycle's fades) and their node viewers are off.

CREDITS
- The effects inside are this library's own; each one's README has its credits.
- The built-in clip: Kevin Raymond, touchdesigner-effects, CC BY 4.0. It is AI-generated (stills from Krea 2 brought to life with Wan 2.2, both run locally) and shows no real person. Her depth map: Depth Anything 3's Mono-Large model (Apache 2.0), one frame at a time, held steady from frame to frame by fitting each frame's scale to the one before (written for this library).
- Names: a 5x7 pixel font drawn for this library.
- Beats from raw audio (the library's audio input, which Cycle's bars come from): a kick is a jump in the low band's loudness; the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new showreel.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest. A new effect in the library means a new showreel. The version and the build it was saved in are on the About page.
