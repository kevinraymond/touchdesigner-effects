VHS + CRT {v}: a VHS tape played into a CRT television. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/vhs_crt.md

VHS stored video on magnetic tape, and an old CRT television drew it line by line with an electron
beam on a glass tube coated with red, green and blue phosphors. Each step left its mark: the tape
kept little detail and even less color, so colors bleed to the right of where they belong; it added
grain, white specks and, when the heads drifted off the tracks, a band of torn lines and streaks;
the cable that carried brightness and color on one wire left dots and rainbows; the tube showed its
lines, its phosphor mask, a glow around bright parts and a curved face.

This effect models that signal rather than laying noise over the picture. Each line is read where
the deck's unsteady time base puts it, filtered the way the deck's luma (brightness, to about 3
MHz) and chroma (color, to about half a megahertz) channels filter it, with filters that smear to
the right as analog ones do, then encoded and decoded as NTSC composite, and drawn by beams that
widen as they brighten, through the mask. On the music the heads lose tracking for a moment.

USE
Drag vhs_crt.tox into your network: it shows TouchDesigner's sample movie (mist over a lake) as a
worn tape on an old TV, the tracking slipping every {steady:g} s, straight away. Wire any TOP into
input 1; the result is on output 1, at the input's size. Optionally wire audio or beat channels into
input 2 (below). Open Window shows it full size; Esc closes the window.

THE PAGE
Tape: play the picture off a tape (off: straight into the TV). Tape Speed: SP, LP or EP, each
slower one softer with colors bleeding further. Wear: grain, color noise, specks, dropouts, a
wandering hue, wobbling lines. Tracking: a band of torn lines and streaks crawling up the picture.
Head Switching: the last lines at the bottom pushed sideways. Signal: Composite (dots and rainbows),
S-Video or RGB. Lines: how many lines the picture has (240, as one field of NTSC). Screen: show it on
a CRT (off: flat). Mask: Aperture Grille, Slot Mask, Shadow Mask or None. Mask Size: one triad's
width in pixels at 720 high. Scanlines: how far the lines stand apart. Curvature. Glow. Bursts: when
the heads lose tracking (On Bars, On Beats, Steady: every {steady:g} s, Off). Length: how long.
Song Moments: Fosfora's builds and drops.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it
into input 2. Bars bring the bursts (the heads lose tracking: a big band of torn lines and streaks);
with Song Moments on, a build throws the tracking off further as it rises, and a drop slips the
picture down a third of a frame for a moment, as a TV losing vertical hold (Fosfora's drop detection
is experimental). Any input: bursts on its bars or beats, every beat kicks the lines sideways a
little, and loudness raises the noise. Raw audio (Audio File In, Audio Device In) gives beats from a
kick detector and a beat clock that locks to the kicks' tempo (experimental: it can still add or miss
beats) and a bar every 4 beats; TouchDesigner's audioAnalysis gives beats from its kick or onset
channels. Nothing wired: a burst every {steady:g} s.

FLASHING
Every burst is a flash, and so is a drop's slip: each goes through one gate that follows the
Flashing parameter (Off: none, and no beat kicks; Calm, the default: at most one a second; Up to 3
per second, the WCAG 2.3.1 limit) and then a budget that keeps this effect to about 2 a second even
at Up to 3. A burst's damage holds still while it lasts, and the slip is one jump and one jump back,
since a picture rolling past every point would flash several times. The steady tracking band changes
every field, so it stays under a twelfth of the picture's height, below the area WCAG counts. NTSC
turns its color subcarrier's phase every field, which makes composite rainbows flicker 30 times a
second; here it holds still. And WCAG counts a pixel as saturated red, all or nothing, once red is
80% of its light, so tape noise would make reds near that line flash: very saturated reds are kept a
little short of it (an orange comes out a little lighter), on the picture and on every pixel of the
mask.

INSIDE
source -> line_in (each line read where the deck's time base puts it, as YIQ) -> tape (the deck's
luma and chroma filters, noise, specks, dropouts, mistracking) -> deck (its steep 3 MHz output
filter) -> signal (composite, S-Video or RGB, back to RGB, the red guard) -> screen (the beams, the
mask, the glow from glow_src and glow, the curved face). line_in, tape, deck and signal work on a
raster 1280 samples wide and Lines tall, one row a line. Input 2 goes through audio (lib audio_in);
counts and steps turn its counts into steps, steady counts the time for Steady; beat_on, bar_on,
steady_on and drop_on pick the bursts Bursts and Song Moments ask for, flash_limit and flash gate
them, flash_budget spaces them, burst holds each one for Length, burst_count numbers them (each
burst's seed) and drop_kind marks a drop's; beat_pulse and beat_env turn beats (or steady ticks,
steady_tick) into the kick.

CREDITS
- The signal: NTSC (the FCC's 1953 color standard, SMPTE 170M): the YIQ matrix, the 3.579545 MHz
  subcarrier turning half a cycle each line, the 52.6 us active line. VHS's published figures: luma
  to about 3 MHz (some 240 lines across a picture height), chroma recorded below it (color-under, 629
  kHz) with about 500 kHz each side, about 40 lines; FM luma on a 3.4 to 4.4 MHz carrier.
- The order of a tape's passes and the use of causal (left-to-right) lowpass filters follow ntsc-rs
  by valadaptive (https://github.com/valadaptive/ntsc-rs, MIT OR ISC OR Apache-2.0), a port of ntscqt
  and ntsc (Apache-2.0), themselves after J. Campbell's composite-video-simulator (GPL-2.0). Read,
  not copied: no code taken, and the bandwidths here are VHS's figures rather than its cutoffs.
- Composite decoding: a notch filter for the brightness and synchronous demodulation for the color,
  the textbook NTSC receiver.
- The tube: Gaussian scanlines whose width grows with brightness, and phosphor masks, as CRT shaders
  have drawn them since cgwg's CRT-Geom (GPL) and Timothy Lottes' scanline shader (public domain);
  followed, not copied. The glow (halation) is the widely used blurred-light mix.
- Dice: Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
- Seen during the survey, not used: tdx-crt, ntsc-td, BrokenVHS, TD-VHShader, CRT TV Filter.
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness;
  the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it
  is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic
  Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001).
  Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (the shaders, the bursts, the slip, the red guard) is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new vhs_crt.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External
.tox at a downloaded copy). The version and the build it was saved in are on the About page.
