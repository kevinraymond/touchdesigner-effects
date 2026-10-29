# Temporal Resonator

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. SAME shows her with faint copies of her arms fanned out behind her, each from a beat earlier, fainter and softer the older it is, the live dancer clean in front of them. ALTERNATING shows the same echoes, every other one dark, a shadow of her arm against the haze. PLUCKS ALWAYS shows echoes from all through the beat, so they follow her moves more continuously](temporal_resonator.webp)

*The three looks on the dancer, the clip top left, with its depth map on input 3 and a song on input 2. Same is the default, Alternating inverts every trip round, and Plucks Always rings everything that moves, not only what moves on the beat.*

**New to plucked strings in a computer?** A guitar string rings because its vibration runs to the end of the string,
reflects and comes back, once every period, a little weaker each time and a little smoother, since the string loses its
high harmonics first. In 1983 Kevin Karplus and Alex Strong found that a computer could do the same with a delay line
one period long. Whatever goes in comes out again a period later, is averaged with its neighbor and is fed back in, and
the result sounds like a plucked string. David Jaffe and Julius Smith extended it the same year, tuning the loop finely
and setting how fast it dies away. It is one of the simplest ways there is to synthesize a sound, and it became the
plucked strings of many synthesizers.

This effect gives every pixel of the picture such a string, one beat of the music long. Whatever moves plucks the
strings it crosses, and a beat later the movement comes round again, then again on the beat after, each echo fainter
and softer than the last. A dancer's gesture made on the beat repeats on the next beats like a ringing note, and people
crossing a square leave chains of footsteps a beat apart. The echoes go behind whatever stands out in the picture now,
so the live subject stays in front of its own echoes. Alternating inverts the string every trip round, so a bright
figure comes back as a shadow on the next beat and bright again on the one after. In TouchDesigner, echoes of a picture
are usually built from a Cache TOP and Cache Select TOPs a fixed number of frames apart, or from a Feedback TOP's
trails, and a beat-length delay is worked out by hand from the tempo. I found nothing that follows the music's tempo
by itself, and nothing that rings the way a string does.

**[Download temporal_resonator.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/temporal_resonator.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `temporal_resonator.tox` into your network. It shows TouchDesigner's sample movie of grass swaying in front of a
   building, plucked at 120 beats a minute (Tempo).
2. Wire any TOP into input 1. The result is on output 1, at the input's size. A subject that moves against a still
   background, such as a dancer, hands or people walking, shows the echoes best.
3. Wire music into input 2 (see Audio input). The strings then follow the music's tempo and are plucked on its beats.
4. Optional: wire a depth map or mask into input 3, grayscale, brighter nearer (or inside). Whatever stands in front of
   its surroundings there stays in front of the echoes, even when it stands still. Without it, only what differs from
   the background stands in front.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `temporal_resonator.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Temporal Resonator page holds, top to bottom, the strings, when they are plucked, input 3, then the window.

| Parameter | Default | What it does |
|---|---|---|
| Mode | Same | Same makes each echo like the moment it repeats, fainter each beat. Alternating inverts the strings every trip round, as a pipe closed at one end reflects a wave, so the echoes alternate between a shadow and a light. A bright figure comes back dark on the next beat, then bright on the one after. |
| Length | 1 Beat | How long the strings are, half a beat, a beat or two beats of the music on input 2 (with nothing wired, of Tempo). It is how far apart the echoes come. Beats slower than 60 or faster than 200 a minute count double or half. Changing it starts the strings again. |
| Sustain | 10 | How many beats the echoes last until they have faded to a tenth, 1 to 30. At 2 it is a short pluck, at 30 a long ring. |
| Strength | 1.5 | How bright the echoes show, 0 to 3. |
| Softness | 0.5 | How much softer each echo comes back than the last, 0 to 1, in time and across the picture, as a string loses its high harmonics first. At 0 every echo is as sharp as the moment it repeats, and at 1 they soon blur into a haze. |
| Threshold | 0.06 | How far a pixel must differ from the background (what has stood still for a while) to pluck its string and to stand in front of the echoes, 0 to 0.5. Raise it to leave drifting smoke and the picture's noise out. |
| Plucks | On Beats | On Beats plucks the strings on each beat of input 2 (with nothing wired, of Tempo), rising at once and falling to half by the next beat, so what moves on the beat rings loudest. Always plucks them evenly all the time. |
| Tempo | 120 | The beat with nothing on input 2, in beats a minute, 40 to 240. It sets how long the strings are and, On Beats, when they are plucked. |
| Loudness | 0.5 | How much harder louder music on input 2 plucks the strings, 0 to 1. |
| Depth Type | Brighter Is Nearer | What input 3 holds, a depth map or a mask. Brighter Is Nearer is for depth estimators (Depth Anything) and masks. Distance 0-1 is for the RealSense and Kinect TOPs, 0 near to 1 far, black where the camera got no reading (left out). Distance in Meters is for the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters, how far away in meters counts as the far end of the depth, 0.5 to 15. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The strings

![Four views from above of people crossing a sunlit plaza, each named in the library's pixel font. INPUT is the clip. DEFAULTS shows each walker trailing a short chain of gray copies of themselves and their shadow, a beat apart, softening as they fade. SOFTNESS 0 makes the chains crisp, a dotted line of walkers like footprints. SUSTAIN 30 makes them longer, the older copies fading into a soft haze](temporal_resonator_looks.webp)

*People crossing a plaza with a song on input 2, at the defaults, with Softness 0 (each echo as sharp as the moment it repeats) and with Sustain 30 (the echoes last 30 beats). Nothing stays put here, so the background is the floor, and no depth map is needed.*

Each pixel's string is a delay line one beat long. Every frame, the string takes in its pluck, how far the picture there
differs from the background, and adds what comes back round the loop from a beat ago, times the loop's gain. What comes
back is averaged over three moments around a beat back, weighted 1, 2, 1, and over a few pixels around it, so each trip
round blurs it a little more, in time and across the picture. That is Karplus and Strong's averaging, which takes a
string's high harmonics away first. The gain is set so the echoes fade to a tenth after Sustain beats, and Alternating
makes it negative, so every trip round inverts the echo.

The background is what has stood still for a while. Every frame each of its pixels steps toward the picture by at most a
small amount, so it settles on the value the pixel holds most of the time (an approximate median, after McFarlane and
Schofield), and someone walking through leaves no trace. A running average kept a faint copy of whoever stood still a
moment, and the echoes then brought it back as a dark figure where they had been. Differences smaller than Threshold
don't pluck, so drifting smoke and the picture's noise stay out.

The echoes are added to the picture wherever it doesn't differ from the background now. Wherever it does, the live
subject stands in front of them, with a margin of a few pixels, so no echo shows inside its edge. Someone who stays in
one place for a while, such as a dancer dancing on the spot, becomes part of the background, and the echoes of their
own moves then showed on their clothes as dark smudges. With a depth map or mask on input 3, whatever stands in front
of its surroundings there (found as [Particles](particles.md) and [Words](words.md) find their subject, by a row having
something farther on both sides) stays in front of the echoes too.

The strings are kept at half the picture's size in 16-bit float, since every echo is soft anyway, and the live picture
stays at full size.

On Beats, a pluck rises over a tenth of a beat after each beat and falls to half by the next, so what moves right on
the beat rings loudest. With the strings one beat long, a move made on the beat comes back on the beats after it. A
pluck that fell all the way to nothing between beats made the echoes of a picture that moves all over, such as flowers
in the wind, pulse with the beat, and the whole picture flashed (see Accessibility).

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends its tempo (`bpm`) and where in the beat it is, so the
strings are a beat long and plucked on its beats. Drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`)
into your project and wire it into input 2. **Raw audio** (an Audio File In or Audio Device In CHOP) gives the tempo
from the beat clock the library's audio input locks to its kicks, and the beats from that clock. **TouchDesigner's
audioAnalysis** gives beats from its kick or onset channels, and the tempo is timed from them.

The strings are a beat long, doubled or halved into 60 to 200 beats a minute. When the tempo changes they glide to
their new length at a quarter of a second a second, so the echoes never jump in time. Louder music plucks harder
(Loudness), from the loudness smoothed over half a second.

**Nothing wired:** the strings are as long as a beat of Tempo (120 a minute) and plucked on its beats.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters and the dancer's depth on input 3. Each frame took 1.6 ms on the GPU (95th
percentile 1.75 ms) and 0.44 ms on the CPU, the median of three runs with the Mac otherwise idle. The strings themselves
(their pass, reading three moments a beat back, and the echo it hands on) take about 0.6 ms, finding the subject in the
depth about 0.35 ms and finding which slots lie a beat back 0.13 ms. Without input 3 it took 1.25 ms. GPU times on this
Mac wander from run to run as its GPU changes speed. Nothing inside cooks while the output is unused.

**GPU memory.** The strings are kept at half the picture's size in 16-bit float, one copy a frame, for a beat (Length)
and a little more. At 1280 x 720 and 60 frames a second, everything inside takes 161 MB at Length 1 Beat, 100 MB at
1/2 Beat and 285 MB at 2 Beats. The ring is sized for the slowest beat it plays (60 a minute), so the memory doesn't
change with the tempo, and a project running at 30 frames a second needs about half. Changing Length starts the
strings again.

## Accessibility

- **No Flashing setting.** Nothing here flashes on a beat. The echoes replay the movement that plucked them, fainter
  and softer each time, and a pluck rises over a tenth of a beat. Each echo is still another pass of the movement over
  the same spots, though, so three things keep them from adding flashes. Each echo comes back softer than the last, a
  pluck falls only to half between beats, and Plucks Always plucks at about On Beats' average. A pluck that fell to
  nothing between beats made the echoes of a picture that moves all over, such as flowers in the wind, pulse with the
  beat, 2 flashes a second against the clip's 1 at 140 BPM.
- **The red guard.** An echo moves a red near WCAG's saturated-red line back and forth across it, so every pixel goes
  through the red guard, which keeps reds just short of the line. Guarding only where an echo showed switched the guard
  on and off as echoes came and went, and the red flowers measured 2 red flashes a second against the clip's 1.
- **No meaning in color.** The effect signals nothing by hue. The echoes keep the picture's own colors.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully 8 times a second), a dance beat at 140 BPM, a song as raw audio,
or no music (Tempo's own plucks), and counted the flashes in the worst second by WCAG's area rule, and WCAG's red
flashes separately. The clips with a depth map had it on input 3:

| Clip and settings | Temporal Resonator | The clip alone |
|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.0 |
| Dancer, a song | 1.0 | 1.0 |
| Dancer, no music | 1.0 | 1.0 |
| Dancer, 140 BPM, Alternating | 1.0 | 1.0 |
| Dancer, 140 BPM, Plucks Always | 1.0 | 1.0 |
| Dancer, 140 BPM, Length 1/2 Beat | 1.0 | 1.0 |
| Dancer, 140 BPM, Length 2 Beats | 1.0 | 1.0 |
| A pair of hands | 1.5 | 1.5 |
| Hands, 140 BPM | 1.5 | 1.5 |
| A walker, 140 BPM | 1.0 | 1.0 |
| People crossing a plaza | 0.5 | 0.5 |
| Plaza, 140 BPM | 0.5 | 0.5 |
| Red flowers against the sky | 1.0, red 0 | 1.0, red 1.0 |
| Flowers, 140 BPM | 1.0, red 0 | 1.0, red 1.0 |
| Flowers, a song | 1.0, red 0 | 1.0, red 1.0 |
| Flowers, 140 BPM, Alternating | 1.0, red 0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 0 | 0.5, red 1.5 |
| Koi, 140 BPM | 1.0, red 0 | 0.5, red 1.5 |
| Walkers with lanterns at night, 140 BPM | 0 | 0 |
| Dancer, 140 BPM, Strength 3, Sustain 30 | 2.0 | 1.0 |
| Dancer, 140 BPM, Strength 3, Softness 0 | 2.5 | 1.0 |
| Flowers, 140 BPM, Strength 3, Sustain 30 | 1.0, red 0 | 1.0, red 1.0 |

Every row at the defaults and the common settings adds nothing to the clip's own flashes beyond the measurement's
half-flash margin, which the koi's reach, and the red guard took every red flash out, the clips' own included. The last
three rows are far corners of the ranges, the brightest and longest-ringing echoes or the brightest and sharpest, and
they stay within WCAG's 3. Strong, sharp echoes of a large moving subject do add flashes, so turn Strength down or
Softness up for an audience that needs it.

## Experimental

- The cut that starts the strings again, so echoes of one shot don't play over the next, is found from how much the
  picture changes at once. A very fast pan can look like a cut.

## Credits and license

MIT. The shaders and operators are written for this library, including the strings as the picture's difference from
its background, plucked on the beat and tuned to the tempo, the echoes behind what stands out now, and the delay line
kept in a ring of stamped slots.

- **The plucked string:** K. Karplus and A. Strong, "Digital Synthesis of Plucked-String and Drum Timbres" (Computer
  Music Journal 7(2), 1983), a delay line one period long, averaged and fed back. Its patent, US 4,649,783, has
  expired.
- **Its extensions:** D. A. Jaffe and J. O. Smith, "Extensions of the Karplus-Strong Plucked-String Algorithm" (Computer
  Music Journal 7(2), 1983), the loop's delay tuned between samples and its decay set apart from its length, as Length
  and Sustain are here. The negative loop gain that makes a closed pipe of the string is a standard variation (J. O.
  Smith, [Physical Audio Signal Processing](https://ccrma.stanford.edu/~jos/pasp/)).
- **The background:** N. J. B. McFarlane and C. P. Schofield, "Segmentation and tracking of piglets in images" (Machine
  Vision and Applications 8(3), 1995), the approximate median.
- **The tempo:** the library's audio input (`lib/audio_callbacks.py`), which gives the beat's length from Fosfora's
  `bpm`, from raw audio's beat clock, or from the gaps between beats.
- **What stands in front in the depth** (`lib/glsl/depth_near.glsl`, `lib/glsl/depth_find.glsl`) is shared with
  Particles, Fluid, Point Cloud, Reaction-Diffusion and Words.
- **The red guard** (`lib/glsl/red_guard.glsl`) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan
  Processor and Voxel Space.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Echoes before this one:** video mixers have long had echoes timed in beats (Pioneer's SVM-1000 of about 2007 had a
  video echo of 1/4 to 8 beats with an afterimage), and in TouchDesigner a Cache TOP with Cache Select TOPs gives
  frame delays (Derivative's [Trails and Frame Delays](https://derivative.ca/community-post/tutorial/trails-frame-delays-touchdesigner-tutorial/64075)
  tutorial). This effect follows neither. Its echoes come from a string per pixel.

**Patents.** A search of US patents (October 2026) found none on a feedback delay per pixel tuned to the music's tempo.
Karplus and Strong's patent expired around 2004. GoPro's active US 11,190,726 and 11,689,692 claim looping a highlight
of a video to music, played back in reverse, back and forth, shuffled or stuttered on the beat, none of which this
effect does. Apple's US 8,320,743, on changing a video's playback by its soundtrack, expired in 2024.

**Not used:** Schroeder's allpass filters over the frame history, a phaser for the picture. Tried offline on the
picture's difference from its background, it barely changed the picture, and a negative loop gain gives echoes that
alternate in sign more simply. The textbook string over the whole picture, shown as it is, dims whatever moves to a
translucent multi-exposure, so the effect strings only the difference from the background and keeps the live picture
whole.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
