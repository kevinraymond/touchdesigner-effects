# Blob Track

![Blob Track on people crossing a plaza seen from above, a crop of the middle at full size: thin white boxes follow walkers, each with an orange number or word above and its position in gray below, lines join neighboring boxes, and on the beat some boxes fill and orange links reach across](blob_track.webp)

**New to blob tracking?** It is one of the basic tricks of computer vision: software finds the
patches of a picture that stand out from the rest, usually whatever moves, calls each one a blob,
and follows it from frame to frame. Drawn on screen as numbered boxes, it gives the look of
surveillance software or a targeting display in a film.

This effect draws that overlay on any picture or video. It finds what moves, puts a thin box around
each thing, writes a number above the box and its position below, and joins each box to its nearest
neighbors with thin lines. Boxes glide instead of jumping, show once a thing has lasted a moment,
and fade out when it is gone. Each box stays with one thing: when the detector loses it for a
moment, splits it or merges it, the box coasts on and picks it up again.
It is good for music visuals, dance, crowds and anything that should look watched. TouchDesigner's
Blob Track TOP can draw plain rectangles on its own; this adds the labels, the links, treatments
inside the boxes and behavior that follows the music, with extra moments from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal. The overlay is GLSL and TouchDesigner
operators, and the text is a pixel font drawn in the shader, so no font ships.

**[Download blob_track.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/blob_track.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license (more than 2 blobs needs TouchDesigner 2025.32820 or later)

## Use it

1. Drag `blob_track.tox` into your network. It shows TouchDesigner's sample movie (grass in the
   wind) straight away.
2. Wire any TOP into input 1. The result is on output 1, at the input's size.
3. Optional: wire audio or beat channels into input 2 (see Audio input).

Open Window (on the effect's page) shows it full size; Esc closes the window.

Movement, the default, works best with a still camera. When the camera moves, everything moves.

**Requirements.** The default detector is TouchDesigner's Blob Track TOP. On the free
Non-Commercial license, builds before 2025.32820 track at most 2 blobs; 2025.32820 and later track
as many as you like. The GPU Grid detector has no such limit.

To update, delete your copy and drag in the new `blob_track.tox`. Dragging a `.tox` in embeds a
copy, so a new release doesn't reach it on its own. You can also point the COMP's External .tox at
a downloaded file.

## Parameters

The Blob Track page, top to bottom:

| Parameter | Default | What it does |
|---|---|---|
| Detector | Blob Track TOP | What finds the blobs. Blob Track TOP: TouchDesigner's tracker; boxes fit closely. GPU Grid (cheaper): runs on the GPU only and reads nothing back to the CPU; its boxes snap to a grid of 40 x 22 cells. |
| Track | Movement | What gets a box. Movement: what moves, light or dark, against a background that follows the picture a second or two behind (and catches up quickly where the picture has gone still, so the place a thing just left doesn't get a box). Stand Out: brighter or darker than its surroundings, moving or not; use it for still pictures. Bright Areas and Dark Areas: one of the two. |
| Threshold | 0.25 | How strongly something must move or stand out to get a box. Raise it when everything gets one. |
| Merge | 0.25 | How far apart parts may be and still count as one blob. It blurs the mask the tracker sees. Grayed out for GPU Grid. |
| Min Size | 0.03 | Smallest box: its longer side as a fraction of the picture's height. |
| Max Size | 0.7 | Largest box, the same way. |
| Max Count | 10 | Most boxes showing at once, up to 64. Boxes stay with what they follow; once the limit is reached, new things wait for room, the longest-lasting first. |
| Smoothing | 0.3 | How calmly boxes follow. 0 jumps with every frame; 1 glides a quarter second behind. |
| Picture | Gray | The picture under the overlay: Gray, Original, or Dimmed so the overlay stands out. |
| Inside | None | What each box does to the picture inside it: None, Invert, Threshold (two tones, the bright parts in the accent color) or Zoom (2x). |
| Labels | ID and Position | Off; ID (the box's number above it); ID and Position (also the center, in percent across and up, below boxes tall enough to carry it); Words (a word instead of the number). Numbers count the boxes in the order they appear. |
| Links | Two Nearest | Lines from each box to its nearest neighbor (Nearest) or two nearest (Two Nearest), or none (Off). |
| Line Width | 1 | Width of the boxes and links in pixels at 720 pixels high; it scales with the picture. |
| Label Size | 2 | Pixels per font pixel at 720 pixels high; it scales with the picture. Grayed out while Labels is Off. |
| Accent | Orange | Color of the numbers, the links a beat spawns and the Threshold inside: Orange, Blue or White. |
| Scramble Labels | On | On each beat, a quarter of the labels scramble and settle again. Grayed out while Labels is Off. |
| Spawn Links | On | On each beat, a quarter of the boxes reach for a random partner with a line in the accent color that fades over half a second. |
| Fill Boxes | On | On a beat, the inside of every box inverts for a moment. It is a flash, so Flashing limits how often it comes. |
| Song Moments | On | Bars, builds, drops and sections (see Audio input). Bars come from any beat input; the rest need Fosfora's signal. |
| Flashing | Calm | Off never flashes. Calm allows at most one flash a second. Up to 3 per second is the WCAG 2.3.1 limit; this effect stays near 2 a second there. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on; 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

Footage with texture everywhere, such as leaves or water, gets boxes everywhere: raise Threshold
or Min Size. A crowd seen from above wants a higher Max Count. Movement boxes the parts of a large,
evenly colored thing that change as it moves, such as a fish's fins and tail; Bright Areas or Stand
Out box the whole thing.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`,
drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire
it into input 2. With Song Moments on, you get:

- **Downbeats:** on each of Fosfora's downbeats the labels switch between numbers and words, so
  every other bar reads as words. The characters scramble for a moment and settle.
- **Builds:** as a build rises, each box also links to its 3rd and 4th nearest neighbors, and all
  links get brighter.
- **Drops:** a drop turns the whole picture over (inverts it) once and shows the four nearest
  links of every box, fading over 1.5 s. The turn-over is a flash: it shares the flash budget with
  Fill Boxes, so Flashing still limits it. Fosfora's drop detection is experimental.
- **Sections:** at each new section every box locks on again: it widens and closes back in, and
  its labels scramble and settle.

**Plain audio** works too. Wire an Audio File In or Audio Device In CHOP into input 2. The effect
takes the loudness of the low band (30 to 150 Hz) as the level, and a sudden jump in it as a beat.
That beat detector is simple and experimental: it can add or miss beats in busy music. A bar is
every 4 beats, counted from when it starts.

**TouchDesigner's audioAnalysis** (or any CHOP with these channels) works the same way. Beats come
from `beat_count`, or from the rising edge of `beat`, `kick` or `onset`. The level comes from
`energy`, `level`, `low`, `bass` or `rms`.

With any of these inputs:

- each beat scrambles a quarter of the labels (Scramble Labels) and sends a quarter of the boxes
  reaching for a random partner (Spawn Links);
- a beat inverts the inside of every box for a moment, as often as Flashing allows (Fill Boxes);
- each bar switches the labels between numbers and words (Song Moments);
- loudness brightens the links.

**Nothing wired:** no beat behaviors. The overlay still tracks, labels and links.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with default parameters. Each frame took 2.28 ms on the GPU (95th
percentile 3.64 ms) and 0.98 ms on the CPU (95th percentile 1.18 ms), and TouchDesigner held
60 fps.

Detection runs on a 320 x 180 copy of the picture. The Blob Track TOP (about 0.8 ms in this run;
its time varies from run to run) and the overlay pass (0.7 ms) are most of the cost; following the
boxes costs about 0.1 ms. The GPU Grid detector costs 1.37 ms on the GPU (95th percentile 1.93 ms)
and 0.38 ms on the CPU, measured the same way. The overlay
only visits the boxes near each part of the picture, so more boxes cost little; a larger input
costs more in the overlay pass. Nothing inside cooks while the output is unused.

## Accessibility

- **Not by hue alone.** Boxes and links are light lines. The number sits above each box and the
  position below it, and the two differ in brightness as well as color (orange against gray). The
  links a beat spawns are in the accent color, and they also come with the beat and fade. Accent
  offers orange, blue or white.
- **Colorblind-safe palette:** orange and blue, on a gray picture by default.
- **Legible text.** The 5 x 7 font is drawn at 2 screen pixels per font pixel at 720 pixels high
  and scales with the picture. On darker pictures the text gets a thin dark outline. Label Size
  goes up to 4.
- **Flashing.** Fill Boxes and the drop's turn-over are flashes. They pass through one gate that
  follows the Flashing parameter: Off never flashes, Calm (the default) allows at most one flash a
  second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. After the gate,
  a budget keeps this effect to about 2 flashes a second even at Up to 3, leaving room for what
  the footage does by itself.
- **No flicker of its own.** A blob gets a box only once it has lasted 0.4 s, a box whose blob is
  lost coasts on for 0.5 s before it fades (so a box doesn't blink out and back), boxes fade in and
  out, and the labels are drawn light enough that boxes and labels coming, going and moving don't
  count as flashes.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far
busier than music: 8 beats, 2 bars and 1 drop a second, a section change every 2 s, and a build
rising and falling. The table gives the flashes in the worst second, by WCAG's area rule:

| Clip | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 2.0 | 3.0 | 1.0 |
| People crossing a plaza | 0.5 | 1.5 | 2.0 | 0.5 |
| Dancer in a hazy warehouse, no beat | 1.5 | 1.5 | 1.5 | 1.0 |

There were no red flashes. Under the beat, Off adds nothing to what the clips do by themselves,
and Calm adds at most one flash a second, as promised. Up to 3 per second reaches WCAG's limit of
3 on the dancer, whose clip already flashes once a second by itself, and stays at 2 on the plaza.
With no beat at all, boxes coming and going over the bright haze added half a flash a second on
the dancer at every setting: one more change of brightness, the smallest step the count has.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a simple kick detector. It can add or miss beats; Fosfora or
  audioAnalysis give steadier beats.

## Credits and license

MIT. The shaders and operators are written for this library: the GPU Grid, the tracking and the
flash budget among them.

- **The look** follows the blob-tracking overlays that spread on social video from 2024: boxes,
  numbers and lines over whatever moves. No project's files or code were used.
- **Detection:** TouchDesigner's own Blob Track TOP (Derivative), or this library's GPU Grid.
- **Dice:** Chris Wellons' lowbias32 integer hash ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain), which picks scrambled
  characters, words and partners.
- **Font:** the 5 x 7 bitmap font was drawn for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person. The preview is a
crop of the middle of the picture, so the labels stay readable at 640 pixels wide.
