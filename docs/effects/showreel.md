# Showreel

![Every effect in the Showreel on the same clip of a dancer in a hazy warehouse, each named in the library's pixel font. First the clip and its depth map (optional), the inputs, on a row of their own, then every effect: ASCII draws her in glyphs, Bent Cam turns her through a circuit-bent webcam into purple shadows, contoured light and torn green lines, Blob Track boxes her moving limbs, Chladni Sand pulls the haze's light into glowing curves and rings on each beat and lets it settle back, Datamosh smears her pose into the next, Detail sculpts the haze into textured smoke and brings out the grain of the floor, Fluid pours flames off her as she moves, Glitch tears her on the beat, Motion Magnify makes her every swing and step larger, Paint turns her and the haze into soft strokes of paint, Particles shed glowing specks off her, Pencil draws her in quick graphite lines on white paper, the dark warehouse around her shaded in pencil strokes, Pixel Sort sorts the haze and her clothes down each column into a pale curtain of light, Point Cloud turns her and the lit wall behind her in 3D, Reaction-Diffusion draws her and the haze in black and white stripes that curve along their edges like a fingerprint, Slit-Scan shows each row of her from a moment earlier than the one above, so her limbs twist as she turns, VHS + CRT plays her off a worn tape on an old TV as a band of torn lines crosses her, and Video Vocoder brings out the grain of the haze and the edges of her clothes, crisper still when the music swells. Each was recorded on its own and tiled for this page; the Showreel shows one at a time](showreel.webp)

**What is it?** Every effect in this library in one component, to try them all at once: drop it
in, and the same picture runs through each effect in turn, fading from one to the next in time with
the music.

The Showreel embeds the released `.tox` of every effect, unchanged, behind one View menu. Cycle, the
default, shows one effect at a time, full size and named in its corner, fading to the next every few
bars of the music on input 2. Or pick one effect by name. Only the effect showing runs, so the
Showreel costs about what one effect does, however many the library holds. (The preview above shows
them side by side under the clip and its depth map: each was recorded on its own and tiled for
this page. Video Vocoder's take has its four fine octaves at 2, Drive at 1 and Flashing at Up to 3 per
second, Detail's has Detail at 2.5 and Edge Contrast at 0.35, and Chladni Sand's has Flashing at Up to 3 per second,
so they show at this size.)
Each effect inside is a full copy you can open and change, with its own page of parameters. It is
generated from the effects themselves, so a new effect in the library comes with a new Showreel.

**[Download showreel.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/showreel.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `showreel.tox` into your network. It shows a 5-second clip of a dancer through every effect
   straight away. The clip and her depth map are inside the `.tox` (2.2 MB, no sound):
   TouchDesigner's own sample movies barely move (Blob Track and Datamosh need motion), and none
   has a depth map.
2. Wire any TOP into input 1. Every effect gets it; the result is on output 1.
3. Optional: wire audio or beat channels into input 2. Every effect gets them too, and Cycle moves
   on with their bars. [Fosfora](https://github.com/kevinraymond/fosfora)'s signal gives the most;
   each effect's page says what it does with it.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside), lined up
   with input 1. The effects that use depth (Particles, Point Cloud, and Fluid with Emit From on
   Depth or Mask) get it. Without it they get the dancer's depth while the dancer clip shows, and
   none once you wire input 1: then they work without depth (Particles follows what moves, Point
   Cloud reads the picture's brightness as depth, Fluid's Depth reads it too).

Open Window (on the Showreel page) shows it full size; Esc closes the window.

To update, delete your copy and drag in the new `showreel.tox`. Dragging a `.tox` in embeds a
copy, so a new release doesn't reach it on its own.

## What's inside

Every effect in the [README's Effects table](../../README.md#effects) at the time of the release,
each linked to its page. The README DAT inside lists the effects that copy holds.

## Parameters

The Showreel page, top to bottom:

| Parameter | Default | What it does |
|---|---|---|
| View | Cycle | What to show. Cycle: one effect at a time, fading to the next over 1 s. Or one effect by name. Only the effects showing run: one, or two during a fade. |
| Every | 4 | Cycle's pace: how many bars of input 2's music each effect shows for. While no bars arrive (nothing wired, or the music stopped), a bar is 2 s. Cycle never moves on within 2 s of its last move, whatever the bars do. Grayed out unless View is Cycle. |
| Labels | On | Names each effect on the picture, in the library's pixel font, white on a dark plate. |
| Flashing | Calm | Applies to every effect inside: Off never flashes, Calm (the default) allows at most one flash a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on; 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.
Each effect's own parameters are on that effect, inside the Showreel.

## Audio input

Input 2 goes to every effect's input 2 unchanged, so each reacts as its page describes, and to
Cycle, which counts its bars: Fosfora's downbeats, or one every 4 beats from plain audio or
TouchDesigner's audio analysis. With nothing wired, or once the bars stop, every effect still runs
and Cycle moves on every 8 seconds (Every 4, 2 s a bar).

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with the eighteen effects of this release inside, the dancer clip's depth on
input 3, a beat far busier than music on input 2, and the Mac otherwise idle. Cycle, the default,
runs one effect at a time: 4.2 ms on the GPU per frame and 1.5 ms on the CPU on average (the median
of three runs, 59 fps held), depending on the effect showing; during a fade two effects run, so the
95th percentile was 7.7 ms on the GPU and 1.5 ms on the CPU. A single view costs what that effect costs (see its page). The cost doesn't
grow as the library adds effects. Nothing inside cooks while the output is unused. GPU memory is the
exception: Slit-Scan keeps a few seconds of the picture for its history, about 546 MB at 1280 x 720,
and once it has shown, that memory stays reserved while the other effects show (its page has the
figures).

## Accessibility

- **Flashing.** One Flashing parameter sets every effect's: each keeps to its own limits (see its
  page). Cycle fades from one effect to the next over a second, never within 2 s of its last move,
  so even fast bars can't turn its moves into flashing. It used to cut: with six effects inside, a
  cut on top of an effect's own flashes reached 3.5 a second at Up to 3 per second under the test
  below, past WCAG's 3; the fade brought that down to 2.5. A fade still changes the whole picture
  once, and with ten effects inside, a fade into Blob Track flashing as fast as Up to 3 per second
  allows reached 3.5 again. So while Cycle fades and for a second after, Up to 3 per second holds the
  effects at Calm.
- **Measured.** The test recorded the output while it fed a beat far busier than music (8 beats,
  2 bars and 1 drop a second) and counted the flashes in the worst second, by WCAG's area rule.
  Under that beat Cycle moves on every 2 s, its fastest, whatever Every says:

  | Clip | Off | Calm | Up to 3 per second | The clip alone |
  |---|---|---|---|---|
  | Dancer in a hazy warehouse | 1.0 | 2.0 | 2.0 | 1.0 |
  | People crossing a plaza | 0.5 | 1.0 | 1.0 | 0.5 |
  | Dancer, Every 1 | 1.0 | 1.5 | 1.5 | 1.0 |

  Off adds nothing to what the clips do by themselves (beyond the half flash a second the count
  allows for measuring noise: the dancer at Off has measured 1.0 and 1.5 in different builds, by
  which effects showed), Calm adds at most one flash a second, and no
  setting goes past WCAG's 3 (Up to 3 per second reaches it with the effects flashing as often as
  that allows). The two dancer runs differ by which effects happened to show in the 10 seconds
  measured. Red flashes: none in these runs (Glitch's color split, the only effect that makes red
  flashes on the dancer, has measured up to 1.0 a second in earlier runs that caught it). On the plaza, Off
  measured 1.0 against the clip's 0.5, within the half flash a second the count allows for measuring noise (0.5 in
  some builds, by which effects showed).
- **Labels.** The names are white on a dark plate, in the library's 5 x 7 pixel font at 3 pixels
  per font pixel (at 720 pixels high; they scale with the picture), so they read on light and dark
  pictures alike.

## Credits and license

MIT. The effects inside are this library's own (their pages list what they use and follow); the
5 x 7 bitmap font was drawn for this library.

- **The built-in clip and the preview footage:** see below. Her depth map, inside the `.tox`, was
  estimated with [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3)'s Mono-Large
  model (Apache 2.0), one frame at a time, and held steady from frame to frame by fitting each frame's
  scale to the one before (written for this library).
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`, which Cycle's bars come
  from): a kick is a jump in the low band's loudness, and the beat clock takes its tempo from the gaps
  between kicks, each gap voting for the beat lengths it is a whole multiple of: inter-onset-interval
  tempo induction, the idea behind S. Dixon's "Automatic Extraction of Tempo and Beat from Expressive
  Performances" (Journal of New Music Research, 2001). Followed, not copied: written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

The built-in clip and the preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person.
