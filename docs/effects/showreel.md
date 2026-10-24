# Showreel

![The Showreel's Grid view on a dancer in a hazy warehouse: a cell for the input and one for each effect, each named in its corner on a dark plate: ASCII drawing her in blue and orange glyphs, Blob Track boxing her moving limbs, Datamosh-style smearing her pose into the next, Depth Particles shedding glowing specks off her (her depth map on input 3), and Glitch tearing her on the beat](showreel.webp)

**What is it?** Every effect in this library in one component, to try them all at once: drop it
in, and the same picture runs through each effect side by side, or one after another in time with
the music.

The Showreel embeds the released `.tox` of every effect, unchanged, behind one View menu. Grid shows
your input and every effect next to each other, each named in its corner. Cycle shows one effect at
a time, full size, moving on every few bars of the music on input 2. Or pick one effect by name.
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
   with input 1. The effects that use depth (Depth Particles) get it. Without it they get the
   dancer's depth while the dancer clip shows, and your picture's brightness once you wire input 1.

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
| View | Grid | What to show. Grid: the input and every effect side by side, each named (every effect runs). Cycle: one effect at a time. Or one effect by name. Only the effects showing run. |
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
TouchDesigner 2025.33230), with the five effects of this release inside and the dancer clip's depth
on input 3. Grid, the default, runs every effect at once: 6.59 ms on the GPU per frame (95th
percentile 7.34 ms) and 2.79 ms on the CPU (95th percentile 2.96 ms). Cycle and the single views
run one effect at a time: Cycle took 1.74 ms on the GPU (95th percentile 3.41 ms; it depends on the
effect showing) and 0.82 ms on the CPU. Grid's cost grows with every effect the
library adds; Cycle's doesn't. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** One Flashing parameter sets every effect's: each keeps to its own limits (see its
  page). Cycle's change from one effect to the next is a cut, never within 2 s of the last, so
  even fast bars can't turn it into flashing.
- **Measured.** The test recorded the output while it fed a beat far busier than music (8 beats,
  2 bars and 1 drop a second) and counted the flashes in the worst second, by WCAG's area rule.
  Cycle was measured at its fastest, Every 1, so it moved on every 2 s:

  | View and clip | Off | Calm | Up to 3 per second | The clip alone |
  |---|---|---|---|---|
  | Grid, dancer in a hazy warehouse | 0.5 | 1.5 | 2.0 | 1.0 |
  | Grid, people crossing a plaza | 0.5 | 1.5 | 2.0 | 0.5 |
  | Cycle at Every 1, dancer | 0.5 | 1.5 | 2.0 | 0.5 |

  Off adds nothing to what the clips do by themselves, Calm adds at most one flash a second, and no
  setting goes past WCAG's 3, Cycle at its fastest under that beat included. No red flashes this
  time; earlier builds measured half a flash a second in Cycle, from Glitch's colored fringes.
- **Labels.** The names are white on a dark plate, in the library's 5 x 7 pixel font at 2 pixels
  per font pixel in the grid and 3 in the single views (at 720 pixels high; they scale with the
  picture), so they read on light and dark pictures alike.

## Credits and license

MIT. The effects inside are this library's own (their pages list what they derive from); the
5 x 7 bitmap font was drawn for this library.

The built-in clip and the preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person.
