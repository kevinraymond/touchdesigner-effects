# Pixel Sort

![Pixel Sort on a dancer in a hazy warehouse. The spotlight's haze between her and the lamp has been sorted down each column, so it hangs like a pale curtain whose light gathers at the bottom, cut off where the haze turns dark. Her white clothes are sorted too, into short vertical streaks, while the dark room around her stays as it was. Now and then the curtain turns end over end, its light gathering at the top, and on the beats thin stripes of whole columns sort the other way](pixel_sort.webp)

*The defaults on the dancer: the haze and her clothes sorted down each column, the sort turning over on the bars.*

**New to pixel sorting?** It rearranges the pixels of a picture in order, from darkest to brightest
for example, along its rows or columns. Sorting whole rows smears any picture into the same
gradients, so the art form sorts only runs of pixels, called spans: say, the pixels whose brightness
lies between two thresholds. Those melt into streaks while the rest of the picture stays as it was,
so a sky seems to pour, a face to drip, a lamp to rain light. Kim Asendorf's ASDFPixelSort made it
popular around 2010, and it has been a staple of glitch art since.

This effect really sorts: every span of every line of every frame, in full, on the GPU. The lines can
run at any angle, as steps of whole pixels, so nothing is resampled and the picture stays sharp.
Spans can be the pixels between two brightness thresholds, the stretches between the picture's
edges, whatever lies inside a depth map or mask on input 3, or whole lines, all of which can be cut
at random into streaks of many lengths. A span sorts by brightness, hue or saturation. The free
pixel sorters for TouchDesigner sort whole rows or columns, or fake the look with a feedback loop
that sorts a little each frame; a real span sort exists as a paid plugin that runs only on NVIDIA
cards. This one is MIT, runs on any GPU TouchDesigner does, Macs included, costs about 2.7 ms a frame,
and plays along with the music.

**[Download pixel_sort.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/pixel_sort.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `pixel_sort.tox` into your network. It shows TouchDesigner's sample movie, a tree against
   bright foliage, with the light between the branches pouring down.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Strong light and dark,
   a lit sky, haze or bright clothes against a dark room, sort best.
3. Optional: wire audio or beat channels into input 2 (see Audio input). The sort then turns over on
   its bars and tears on its beats.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside), and set
   Spans to Depth or Mask. Without it, input 1's brightness stands in.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `pixel_sort.tox`. Dragging a `.tox` in embeds a copy,
so a new release doesn't reach it on its own. You can also point the COMP's External .tox at a
downloaded file.

## Parameters

The Pixel Sort page, top to bottom, in three groups: the spans, the sort, and the music.

| Parameter | Default | What it does |
|---|---|---|
| Spans | Brightness | Which runs of pixels sort. Brightness, Edges, Depth or Mask and Whole Lines are described under [The spans](#the-spans). |
| Low | 0.25 | The darkest a pixel may be and still sort, 0 to 1 (input 3's value for Depth or Mask). Louder music lowers it. Grayed out for Edges and Whole Lines. |
| High | 0.8 | The brightest a pixel may be and still sort, 0 to 1 (input 3's value for Depth or Mask). Louder music raises it. With a mask, Low 0.5 and High 1 sort what lies inside it. Grayed out for Edges and Whole Lines. |
| Edge | 0.08 | How strong an edge must be to end a span, 0 to 0.5, where 1 would be a step from black to white. Higher, only the strongest edges end spans and the streaks run longer. Grayed out unless Spans is Edges. |
| Cut Every | 0 | Cuts the spans at random points about this many pixels apart (at 720 high, scaling with the picture), so streaks of many lengths sort side by side. The points are fixed to the picture's pixels, so they stay put from frame to frame and at any angle. At 0 the spans run whole. |
| Sort By | Brightness | What each span is sorted by. Brightness runs from dark to bright, Hue around the color wheel from red through yellow, green and blue to magenta, and Saturation from gray to the strongest colors. Hue jumps between neighbors in gray parts of the picture, so it shimmers more on video. |
| Angle | 270 | Which way the sort runs, in degrees counterclockwise from the right: each span's values rise that way. At 270 the brightest end of each span is at the bottom, so light seems to pour down. At 0 the brightest is at the right and at 90 at the top. Any angle works (see [How it works](#how-it-works)). |
| Spin | 0 | How fast Angle turns, in degrees a second, at most 10 either way (see [Accessibility](#accessibility)). |
| Flips | On Bars | When the sort turns end over end, so each span's bright end swaps with its dark end. On Bars flips on the one of each bar and On Beats on every beat, both from input 2, and with nothing wired every 2 s. Steady flips every 2 s and Off never. A flip changes every span at once, so it counts as a flash, and Flashing limits how often they come. |
| Beat Kick | 0.5 | How wide each beat tears the picture, 0 to 1. For 0.15 s three thin slivers of lines, one in each third of the picture, sort whole from end to end and against the grain, 6 to 18 lines each at 1 (at 720 high; 3 to 9 at the default). Flashing Off stops them. |
| Loudness | 0.5 | How much the music's loudness on input 2 widens the spans, 0 to 1, so more of the picture sorts in loud passages and less in quiet ones. Wider moves Low toward black and High toward white (at most 60% of the way), Edge up and Cut Every's cuts further apart. Narrower moves Low and High toward each other. Loudness is eased over half a second, and the spans widen or narrow by at most half of the way a second. |
| Song Moments | On | With Fosfora's signal on input 2, a build widens the spans as it rises, and a drop sorts every line whole for Length seconds. |
| Length | 0.5 | How long a drop sorts every line whole, in seconds (0.1 to 1.5). Grayed out with Song Moments off. |
| Flashing | Calm | How often a flip or a drop may come. Off never, Calm at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. Off also stops the beat's tears. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The spans

![Six views of the dancer, each named in the library's pixel font. INPUT is the clip as it is. BRIGHTNESS, the default, sorts the haze and her clothes down each column into a pale curtain. EDGES sorts the stretches between the picture's edges, so the dark room falls in long columns and the haze fills a tall bright band beside her. DEPTH OR MASK sorts only what the depth map puts near, her body and the floor, so she smears down into herself while the haze is untouched. WHOLE LINES with Cut Every 120 sorts everything into short streaks of every length, so the whole scene comes down like rain. ANGLE 30 sorts toward the upper right, so the haze streaks diagonally away from the lamp](pixel_sort_spans.webp)

*Each span kind on the dancer at the defaults otherwise, with the clip as it is in the corner. Depth
or Mask has Low 0.3 and High 1, Whole Lines Cut Every 120, and the last Angle 30.*

**Brightness** sorts the pixels whose brightness lies between Low and High, the threshold spans of
ASDFPixelSort. Black and white stay where they are and cut the spans, so a dark figure in front of a
bright sky keeps its outline while the sky melts around it.

**Edges** sorts the stretches between the edges in the picture, found with the Sobel operator. Flat
areas, light or dark, sort into long streaks, and outlines hold.

**Depth or Mask** sorts where input 3 lies between Low and High: with a depth map, what is near, and
with a mask, what is inside it at Low 0.5 and High 1. So a person can melt while the room stays put,
or the other way round with Low 0 and High 0.5. With nothing on input 3, input 1's brightness stands
in, and it works like Brightness.

**Whole Lines** sorts every line from one edge of the picture to the other, into one gradient each.
With Cut Every the lines break into streaks of many lengths, which is the look of rain or of a torn
signal.

Cut Every works with every kind, and Sort By with every kind: by Hue, a span becomes a band of the
color wheel, and by Saturation, it runs from gray into its strongest color.

## How it works

**Which pixels sort.** `key` works out three things for each pixel: the value it sorts by, whether it
lies in a span, and whether its line is cut there. A pixel already in a span stays in until it is 0.04
past Low or High, and one outside joins only once it is 0.04 inside them (hysteresis, against `key`'s
own last frame), with the brightness smoothed over 3 x 3. Without that, noise in the picture moved the
ends of spans back and forth from frame to frame, and a span that changes length sorts anew from end
to end.

**The lines.** `sort` is a compute shader with one workgroup for each line across the picture. A line
toward Angle is a digital line: within 45 degrees of horizontal it has one pixel in each column
(row y - round(x tan Angle)), and otherwise one in each row. So every pixel lies in exactly one line,
nothing is resampled, and the untouched parts of the picture stay exactly as they were. A picture up
to 1280 x 1280 has at most 2,559 lines, at 45 degrees.

**The sort.** Each workgroup reads its line into shared memory, marks where spans break (at a pixel
outside every span, at a span's first pixel, and at a cut), and works out where each pixel's span
starts with a parallel max-scan. Then it sorts the whole line once, by a key of the span's start, the
value and the pixel's place in the line. The span's start comes first, so the spans keep their places
and each one comes out sorted within itself, and a pixel outside every span is a span of one and stays
put (a segmented sort). The sort is a bitonic sorting network over up to 2,048 places: 66 rounds of
compare-and-swap, the 1,024 pairs of each round shared among the workgroup's 512 threads. Last, each place takes the pixel whose key
landed there and writes it back. A line with no span longer than one pixel is copied as it is.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it
into input 2. The sort turns over on its bars (or on its beats, with Flips at On Beats), its beats
tear thin slivers, and louder music widens the spans. With Song Moments on, two more things happen.

- **Builds** widen the spans as they rise, up to 40% of the way to black and white at the peak.
- **Drops** sort every line whole for Length seconds, then the spans come back at once. A drop passes
  the same Flashing gate as the flips. Fosfora's drop detection is experimental.

**Any input** brings flips on its bars (On Bars) or beats (On Beats), tears on every beat, and the
spans swelling with loudness. Raw audio (an Audio File In or Audio Device In CHOP) gives beats from a
kick detector and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then
come on the beat even when a kick is missed, a kick between beats is left out, and a bar is every 4
beats (which beat starts the bar is a guess). It stops 8 beats after the kicks do, and while it isn't
locked every kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset channels.

On the library's test song (`dev/reaction.py`), a bar's flip shows most: the picture changes 1.67
times as much around a bar as around the other beats. The beats themselves show less, since the tears
are thin: in the 0.2 s after a beat the picture changes 1.17 times as much as in the 0.2 s before it
(1.27 at Beat Kick 1), where Glitch's slivers reach 1.8. Loudness widens and narrows the spans slowly,
so it moves the picture little from moment to moment.

**Nothing wired:** a flip every 2 s, with the tears, so the effect shows itself.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with default parameters. Each frame took 2.7 ms on the GPU (95th
percentile 3.0 ms) and 0.27 ms on the CPU (95th percentile 0.32 ms), the median of three runs. The sort
costs nearly all of it (2.4 ms), and `key` 0.1 ms. The sort's cost follows the number and length of the lines more than how much of the
picture sorts: Whole Lines at Angle 30, the most work tried, took 3.4 ms on the GPU, and Angle 0 (rows,
720 lines of 1280 pixels) 2.4 ms. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** A flip changes every span at once, and so does a drop's whole sort, so both count as
  flashes. They pass one gate that follows the Flashing parameter: Off never lets one through, Calm
  (the default) at most one a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting
  exceeds. After the gate a budget keeps them at least 0.75 s apart even at Up to 3.
- **Beats.** Each beat sorts three thin slivers of lines whole, one in each third of the picture, for
  0.15 s. That is too little of the picture to count as a flash, as Glitch's slivers are, so they
  don't need the gate, and Flashing Off stops them anyway.
- **Steady spans.** A span that changes length sorts anew from end to end, so its whole streak can
  jump. Hysteresis keeps the ends of spans from following the picture's noise, and loudness and builds
  widen the spans gradually.
- **Spin.** Turning the angle moves the steps in the lines, so pixels move from one line to the next,
  and every span they leave or join sorts anew. With Flashing Off, the plaza measured 2.0 flashes a
  second at Spin 45 and 1.5 at Spin 20, where the clip alone measures 0.5, and nothing added at 10. So
  Spin stops at 10 degrees a second.
- **No meaning in color.** The effect draws nothing of its own and signals nothing by hue. It only
  moves the picture's own pixels, so it adds no color the picture didn't have.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far
busier than music (8 beats, 2 bars and 1 drop a second) and counted the flashes in the worst second,
by WCAG's area rule:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 1.5 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.0 | 1.0 | 1.0 |
| Dancer, no beat (steady flips) | 1.0 | 1.0 | 1.5 | 1.0 |
| People crossing a plaza | 0.5 | 1.0 | 1.0 | 0.5 |
| Red flowers against the sky | 1.0 | 2.0 | 2.0 | 1.0 |
| Koi in a black pond | 1.0 | 1.5 | 1.5 | 0.5 |
| Dancer, Beat Kick 1, Loudness 1 | 1.0 | 1.5 | 1.5 | 1.0 |
| Flowers, Beat Kick 1, Loudness 1 | 1.0 | 2.0 | 2.0 | 1.0 |
| Koi, Beat Kick 1, Loudness 1 | 1.0 | 1.5 | 2.0 | 0.5 |
| Flowers, Sort By Hue | 1.5 | | | 1.0 |
| Dancer, Sort By Hue | 1.5 | | | 1.0 |
| Koi, Edges | 1.0 | | | 0.5 |
| Flowers, Whole Lines, Cut Every 120 | 0.5 | | | 1.0 |
| Plaza, Spin 10 | 1.0 | | | 0.5 |
| Dancer, Depth or Mask (Low 0.3, High 1) | 1.0 | | | 1.0 |

Each is within its setting's rule. Off adds nothing to what the clip does by itself beyond the
measurement's half-flash margin, Calm adds at most one a second, and nothing passes WCAG's 3. The
settings measured at Off only change what sorts or how, not the flips or drops, which the rows above
measure at every setting. Red flashes, which WCAG counts separately, followed the clips' own (1.0 a
second on the flowers and 1.5 on the koi, which both clips make by themselves): at most 2.0 a second
at Off (Edges on the koi; 1.5 at the defaults), 2.5 at Calm and at Up to 3 (the koi), and none on the
dancer or the plaza.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It
  takes a few beats to lock and can still add or miss beats where the kicks don't keep the beat, and
  which beat starts a bar is a guess. Fosfora or audioAnalysis give steadier beats.

## Credits and license

MIT. The shaders and operators are written for this library, including the digital lines at any
angle, the compute shader, the hysteresis, the tears and the music.

- **Pixel sorting with threshold spans** as an art form: Kim Asendorf's
  [ASDFPixelSort](https://github.com/kimasendorf/ASDFPixelSort) (Processing, 2010, no license
  stated). Followed, not copied.
- **The span kinds** (between two brightness thresholds, between edges, whole lines with random
  lengths) and the defaults Low 0.25 and High 0.8: satyarth's
  [pixelsort](https://github.com/satyarth/pixelsort) (Python, MIT). Followed, not copied.
- **The sort:** the bitonic sorting network of K. E. Batcher, "Sorting networks and their
  applications" (AFIPS Spring Joint Computer Conference, 1968). Sorting each span inside one sort of
  the whole line, by a key that starts with where the span starts, is a widely known technique (a
  segmented sort). Where each span starts comes from a parallel max-scan, after W. D. Hillis and
  G. L. Steele, "Data parallel algorithms" (Communications of the ACM, 1986).
- **Edges** by the Sobel operator, and **hue and saturation** by the usual HSV formulas: widely known
  techniques.
- **Dice:** Chris Wellons' lowbias32 integer hash
  ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain), for the cuts and the
  tears.
- **Seen during the survey, not used:** MaxMainio's Sort in [TD_](https://github.com/MaxMainio/TD_)
  (MIT, whole rows or columns, needs 2025's POPs), aaronmylespereira's [TD-Toxes](https://github.com/aaronmylespereira/TD-Toxes) pixelSorting (a
  feedback look from a tutorial), Lou Evoy's [Pixel Sort TOP](https://louevoy.gumroad.com/l/pixelsort-top)
  (paid, NVIDIA only), the forum's [Pixel Sorter](https://forum.derivative.ca/t/pixel-sorter/9792)
  (2017, a Shadertoy port), and elekktronaut's [Pixel Sorting tutorial](https://youtu.be/xasLIEw23zY).
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): a kick is a jump in
  the low band's loudness, and the beat clock takes its tempo from the gaps between kicks, each gap
  voting for the beat lengths it is a whole multiple of. That is inter-onset-interval tempo
  induction, the idea behind S. Dixon's "Automatic Extraction of Tempo and Beat from Expressive
  Performances" (Journal of New Music Research, 2001). Followed, not copied, and written for this
  library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person. The depth map behind the
Depth or Mask view was estimated from it with Depth Anything 3's Mono-Large model (Apache 2.0).
