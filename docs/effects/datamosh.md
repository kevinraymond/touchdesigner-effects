# Datamosh

![Datamosh on cuts between a field of red flowers and a woman's face against blue: on the beats the picture blooms, her face zooming and smearing into doubled outlines before it catches up, and at the cut back to the flowers her face stays printed over them until the picture settles](datamosh.webp)

**New to datamoshing?** It is a glitch-art technique that breaks video compression on purpose. To
save space, a compressed video stores a full picture (a keyframe) only now and then; the frames in
between store mostly how patches of the picture move. Delete the keyframe at a cut, and the new
shot's motion gets applied to the old shot's picture: the old shot smears and melts into the new
one until the next keyframe cleans it up. It has been a music-video staple since the late 2000s.

This effect imitates that look live, on any moving picture. It does not edit a real compressed video
and deletes no real keyframes. Instead it estimates the motion itself on the GPU, every frame, and
runs its own small "decoder" that it holds back from correcting. Use it for music visuals,
transitions between shots, or any moving picture you want to melt. TouchDesigner's own Optical Flow
TOP runs only on Windows with an NVIDIA RTX card. This effect does its own motion estimation in
GLSL, so it works on a Mac too. It reacts to music, with extra moments from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal.

**[Download datamosh.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/datamosh.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `datamosh.tox` into your network. With nothing wired in, it cuts between two of
   TouchDesigner's sample pictures every 6 seconds, so there is a cut to mosh straight away.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Moving pictures and
   hard cuts mosh best.
3. Optional: wire audio or beat channels into input 2 (see Audio input).

A clip slower than the project, such as 16 fps footage in a 60 fps project, works as it should:
the picture moves only when the input brings a new frame, so the smear doesn't pulse.

Open Window (on the effect's page) shows it full size; Esc closes the window.

To update, delete your copy and drag in the new `datamosh.tox`. Dragging a `.tox` in embeds a
copy, so a new release doesn't reach it on its own. You can also point the COMP's External .tox
at a downloaded file.

## Parameters

The Datamosh-style page, top to bottom:

| Parameter | Default | What it does |
|---|---|---|
| Mode | Smear | How the picture moves. Smear: optical flow per pixel, so the smears look liquid. Blocks: one motion vector per 16 px block, as a codec finds them, with a coarse residual and frozen blocks. Switching modes doesn't jump: both work on the same picture. |
| Mosh | 0.5 | How much of each new frame's correction the picture leaves out. At 0 every correction arrives, so it moshes only at cuts, skips, Hold, or with Motion away from 1. At 1 the motion alone moves the picture, and only Recovery brings it back. |
| Motion | 1.2 | How far each frame's motion pushes the picture. Above 1 it runs ahead of the movement and smears. Below 1 it lags behind. |
| Recovery | 3 | Seconds the picture takes to fade back to the input after a mosh. Longer keeps smears around. |
| Chroma | 0 | Lets color smear apart from brightness. At 1, brightness follows the input and only color moshes. |
| Frozen Blocks | 0.03 | Blocks only: the share of blocks that miss each update and stay where they were. More freeze during a skipped keyframe. Grayed out in Smear. |
| Hold | Off | Freezes the motion and keeps applying it, with no corrections. What was moving keeps flowing the same way (the "bloom" mosh), and what was still stays put. When Hold goes off, the picture recovers. |
| Mosh Cuts | On | At a cut in the input, drops the keyframe: the new shot's motion pushes the old picture around until it recovers. Off: cuts pass through. Cut detection is experimental (see below). |
| Keyframe | | Sends a keyframe: the picture fades back to the input over Fade. In Blocks it fades in a sweep of block columns, left to right. It counts as a flash, so Flashing limits it, and it does nothing when Flashing is Off. |
| Fade | 1 | Seconds a keyframe takes to fade the picture back to the input. |
| Skip Keyframe | | Skips a keyframe now. For about half a second the motion holds and no corrections arrive, so the picture smears along its last movement, then recovers. It counts as a flash, so Flashing limits it, and it does nothing when Flashing is Off. |
| Beat Surge | 0.5 | On each beat of input 2 the picture blooms: for a moment no corrections arrive, the whole picture zooms out from the middle and its motion runs further ahead, then it catches up with the input, so each beat pumps it out and back. It changes the whole picture, so it is a flash: Calm allows one a second (about every other beat at dance tempos), Up to 3 per second every beat up to 180 BPM, Off none. 0 turns it off. |
| Skip On | Every Bar | Which pulse on input 2 skips a keyframe, as Skip Keyframe does: Every Beat, Every Bar (Fosfora's downbeats, else every 4th beat), or Off. Flashing limits it too. Beats found in raw audio are experimental. |
| Level | 0.3 | How much loudness on input 2 adds to Mosh. Louder passages smear more. |
| Song Structure | On | With Fosfora's signal on input 2: builds, drops and sections (see Audio input). Other inputs carry no song structure, so this does nothing with them. |
| Flashing | Calm | Off never flashes. Calm allows at most one flash a second. Up to 3 per second is the WCAG 2.3.1 limit. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on; 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`,
drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire
it into input 2. With Song Structure on, you get:

- **Builds:** as a build rises, keyframes are withheld. Recovery slows to a stop and Mosh climbs
  toward 0.9, so the picture melts further and further.
- **Drops:** the drop brings a keyframe that fades the picture clean over Fade. Fosfora's drop
  detection is experimental.
- **Sections:** each new section brings a keyframe too.
- **Bars:** with Skip On at Every Bar, the skips land on Fosfora's real downbeats.

Its level comes from Fosfora's `bass`, which swells with each beat and between passages; Fosfora's
`energy` is loudness over three seconds, nearly constant on mastered music.

**Plain audio** works too. Wire an Audio File In or Audio Device In CHOP into input 2. The effect
takes the loudness of the low band (30 to 150 Hz) as the level, and a sudden jump in it as a kick.
Once the kicks keep to a tempo, a beat clock locks to them: beats then come on the beat even when a
kick is missed, a kick between beats is left out, and a bar is every 4 beats (which beat starts the
bar is a guess). It stops 8 beats after the kicks do, so a breakdown goes quiet, and while it isn't
locked every kick is a beat. It is experimental: it takes a few beats to lock, and music whose kicks
don't keep the beat (half-time, broken beats) gets every kick as a beat.

**TouchDesigner's audioAnalysis** (or any CHOP with these channels) works the same way. Beats come
from `beat_count`, or from the rising edge of `beat`, `kick` or `onset`. The level comes from
`energy`, `level`, `low`, `bass` or `rms`.

With any of these inputs:

- a beat blooms the picture, zooming and smearing it out from the middle and letting it catch up,
  as often as Flashing allows (Beat Surge);
- every beat or every bar skips a keyframe (Skip On), so the picture smears along its movement
  for a moment, the held motion blooming further;
- loudness adds to Mosh (Level).

**Nothing wired:** no blooms or skips, and Level adds nothing. The effect still moshes the input's cuts and
its own Mosh, and the Keyframe and Skip Keyframe pulses still work.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with default parameters (Smear) and a beat far busier than music on
input 2. Each frame took 3.5 ms on the GPU (95th percentile 5.1 ms) and 0.47 ms on the CPU (95th
percentile 0.56 ms), the median of three runs, and TouchDesigner held 60 fps. GPU times on this
machine vary by about a third from run to run.

The optical flow is most of it: Lucas-Kanade at 1/4 size (about 1.2 ms) and at 1/8 (about
0.6 ms), then the decoder (0.9 ms, which reads its last picture twice while a beat blooms). Blocks costs a little more: 3.44 ms on the GPU (95th percentile 4.99 ms)
and about 0.7 ms on the CPU. The costliest Blocks step picks the best offset per block
(about 1.4 ms). A larger input costs more everywhere; Mosh, Motion and the other settings cost
nothing extra.

With nothing downstream and the node out of view, nothing inside cooks, whether input 2 is
wired or not.

## Accessibility

- **Not by hue alone.** The effect draws nothing of its own: no overlay, no colors, no text. It
  moves the input's own pixels. Chroma lets color smear apart from brightness, but carries no
  meaning.
- **Palette:** none; the picture keeps the input's colors.
- **Flashing.** Keyframes, skipped keyframes and a beat's bloom change the whole picture, so they
  count as flashes. They pass through one gate that follows the Flashing parameter. Off lets none
  through: no blooms or skips on beats, no keyframes from Fosfora's drops and sections, and the
  Keyframe and Skip Keyframe pulses do nothing. Calm (the default) allows at most one keyframe, one
  skip and one bloom a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting
  exceeds. Even then, nothing cuts: a keyframe fades over Fade (at least 0.25 s), a skip smears the
  picture along its own motion, a bloom eases out and back, recovery fades, and a cut in the input
  is held rather than passed through.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far
busier than music: 8 beats, 2 bars and 1 drop a second, a section change every 2 s, and a build
rising and falling. The gate did pass them: in 3 s, Calm let through 3 skips and 3 keyframes,
Up to 3 per second 6 skips and 3 keyframes, and Off none. The table gives the flashes in the worst
second, by WCAG's area rule:

| Clip | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 0.5 | 1.0 | 2.0 | 1.0 |
| People crossing a plaza | 0.5 | 1.0 | 2.0 | 0.5 |
| Dancer, a beat at 140 BPM | 0.5 | 1.0 | 1.5 | 1.0 |

The last row is a dance tempo, a bar every 4 beats. It matters here because a bloom takes about a
third of a second to go out and come back: the busy beat restarts it before it returns, while at
140 BPM each one finishes. Before the bloom went through the gate it measured 3.0 at Calm on that
row, so Calm now lets one through a second. There were no red flashes.

## Experimental

- Cut detection is a heuristic. A cut is a change between frames several times larger than the
  usual one, and never less than a fixed floor. It can miss a soft cut, or take a sudden change of
  light in the input for a cut. Mosh Cuts turns it off.
- Drop keyframes depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It
  takes a few beats to lock and can still add or miss beats where the kicks don't keep the beat, and
  which beat starts a bar is a guess; Fosfora or audioAnalysis give steadier beats.

## Credits and license

MIT. The shaders and operators are written for this library.

- **The technique:** datamoshing is the glitch art of deleting a compressed video's keyframes, so
  one shot's motion drags the last shot's pixels. This effect is datamosh-style: it models what a
  decoder does with missing keyframes, with no codec.
- **Smear:** Lucas-Kanade optical flow, written from B. D. Lucas and T. Kanade, "An Iterative
  Image Registration Technique with an Application to Stereo Vision" (1981).
- **Blocks:** block matching as a video encoder does it, a full search refined to a quarter pixel
  as in H.264. olegchomp's tdx-datamosh ([tdx-rnd](https://github.com/olegchomp/tdx-rnd)), read
  during the survey, models macroblocks too; none of its code was used (it states no license).
- **Resampling:** a Catmull-Rom bicubic (Catmull and Rom, 1974), clamped so repeated moves neither
  blur nor ring.
- **Dice:** Chris Wellons' lowbias32 integer hash ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain, the Unlicense).
- **Read during the survey, not used:** VARIMOSH (paid), the Palette's opticalFlow (its license
  keeps it out of a shared `.tox`).
- With nothing wired in, it shows TouchDesigner's own sample media; none ships in the `.tox`.
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump
  in the low band's loudness, and the beat clock takes its tempo from the gaps between kicks, each
  gap voting for the beat lengths it is a whole multiple of: inter-onset-interval tempo induction,
  the idea behind S. Dixon's "Automatic Extraction of Tempo and Beat from Expressive Performances"
  (Journal of New Music Research, 2001). Followed, not copied: written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html), measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person.
