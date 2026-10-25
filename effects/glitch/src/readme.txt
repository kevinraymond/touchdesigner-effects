Glitch {v}: digital corruption in short bursts. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/glitch.md

Glitch art imitates broken digital video: blocks of the picture jump to the wrong place or freeze,
rows slip sideways as if the signal lost sync, and the red, green and blue parts of the picture
drift apart.

This effect breaks the picture on the music. Every beat tears a few thin slivers of rows sideways,
glitches a few single blocks and kicks the RGB split. On the one of each bar a big burst comes: for
a moment blocks shift, freeze, smear or lose their colors and bands of rows tear; then the picture
is whole again. With nothing wired both come steadily. A burst holds still while it lasts.

USE
Drag glitch.tox into your network: it shows TouchDesigner's sample movie (grass in the wind)
breaking up every {steady:g} s straight away. Wire any TOP into input 1; the result is on output 1,
at the input's size. Optionally wire audio or beat channels into input 2 (below). Open Window shows
it full size; Esc closes the window.

THE PAGE
Bursts: when a big burst comes (On Bars, On Beats, Steady: every {steady:g} s, Off). Amount: how
much of the picture a burst breaks. Length: how long a burst lasts. Block Size. Blocks: blocks
shift, freeze, smear and lose their colors. Tears: rows slip sideways. RGB Split: always on, wider
during a burst, kicking on every beat. Song Moments: Fosfora's builds and drops.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it
into input 2. Beats bring the small glitches and bars the bursts; with Song Moments on, a build
breaks more of the picture as it rises and a drop breaks all of it once (Fosfora's drop detection is
experimental). Any input: small glitches on its beats, bursts on its bars or beats, and loudness
widens the RGB split. Raw audio (Audio File In, Audio Device In) gives beats from a kick detector
and a beat clock that locks to the kicks' tempo (experimental: it can still add or miss beats) and a
bar every 4 beats; TouchDesigner's
audioAnalysis gives beats from its kick or onset channels. Nothing wired: the glitches and bursts
come steadily instead.

FLASHING
Every burst is a flash: the picture changes at once and changes back. Bursts pass one gate that
follows the Flashing parameter (Off: no bursts at all, only the RGB split; Calm, the default: at
most one a second; Up to 3 per second, the WCAG 2.3.1 limit) and then a budget that keeps this
effect to about 2 a second even at Up to 3. A burst's damage holds still while it lasts. The small
glitches on every beat cover too little of the picture to count as flashes; Off turns them off too.

INSIDE
source -> hold (the picture from before the burst, a feedback loop) -> glitch (the burst's damage
and the RGB split, one pass). Input 2 goes through audio (lib audio_in); counts and steps turn its
counts into steps, steady counts the time for Steady; beat_pulse, beat_env and beat_n turn beats (or
steady ticks, steady_tick) into the small glitches; beat_on, bar_on, steady_on and drop_on pick the
bursts Bursts and Song Moments ask for, flash_limit and flash gate them, flash_budget spaces them,
burst holds each one for Length, burst_count numbers them (each burst's seed) and drop_kind marks a
drop's.

CREDITS
- The damage (slivers torn sideways, blocks that jump, freeze or lose their color, rows that slip)
  is the common vocabulary of digital glitch art, after broken video streams and files.
- Dice: Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
- Read during the survey, not used: td-glitch-effects, Glitch Machine.
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness;
  the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it
  is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic
  Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001).
  Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (the bursts, the flash budget) is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new glitch.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External
.tox at a downloaded copy). The version and the build it was saved in are on the About page.
