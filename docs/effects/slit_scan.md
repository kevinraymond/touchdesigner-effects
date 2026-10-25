# Slit-Scan

![Slit-Scan's Slit map on a dancer in a hazy warehouse. Left of the middle is the live picture, with the spotlight and its haze. Right of the middle is the strip, where the vertical line down the middle is laid on film running right, so her arms and loose clothing crossing that line stream out to the right as smooth pale ribbons and her body becomes a tall smeared shape. Now and then a few thin slivers of rows land on the film from a moment earlier](slit_scan.webp)

*The Slit map on the dancer: the line down the middle, laid on film running right.*

**New to slit-scan?** Picture a video as a stack of its frames, one behind the other, so the stack is
a block of time. A normal picture is a slice straight across that block, every part of it from the
same moment. Slit-scan cuts the slice at a tilt or along a curve instead, so the top of the picture
might show now and the bottom a second ago. Anything that stands still looks the same, and anything
that moves bends, stretches or smears, since each part of it is seen at a different moment. The
older form is strip photography, which films one line of a scene through a narrow slit onto film
moving past it, the way photo-finish cameras at a race do.

This effect keeps the last two seconds of its input on the GPU and builds each pixel from its own
moment. The time map can sweep across the picture, spread in rings from a center, follow a depth map
or a mask, or follow a drifting noise, and a fifth map is a slit with film running past it. Between
the input's frames it fills in along the movement, so a 24 fps video or a 16 fps clip bends and
streams smoothly instead of breaking into steps. Free slit-scan setups for TouchDesigner exist as
tutorials, a tutorial's project file and an unlicensed component, built on the Time Machine TOP.
They step from frame to frame, don't follow music, and don't say how much memory their history
takes, which at 1280 x 1280 can run past a gigabyte. This one is MIT, fills in between frames,
states and measures its memory, and plays along with the music.

**[Download slit_scan.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/slit_scan.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `slit_scan.tox` into your network. It shows TouchDesigner's sample movie, a slow pan through
   a forest, with the trees leaning through time straight away. The history fills over the first two
   seconds, so the effect grows in.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Slit-scan only shows
   where something moves, so a camera on people, a dancer or traffic shows it best.
3. Optional: wire audio or beat channels into input 2 (see Audio input). The map then flips on its
   bars and tears on its beats.
4. Optional: wire a depth map or mask into input 3, grayscale and brighter nearer (or inside), for the
   Depth map. Without it, input 1's brightness stands in.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `slit_scan.tox`. Dragging a `.tox` in embeds a copy,
so a new release doesn't reach it on its own. You can also point the COMP's External .tox at a
downloaded file.

## Parameters

The Slit-Scan page, top to bottom, in three groups: the time map, the history, and the music.

| Parameter | Default | What it does |
|---|---|---|
| Map | Sweep | Which moment each part of the picture comes from. Sweep, Rings, Depth, Liquid and Slit are described under [The maps](#the-maps). |
| Delay | 1.5 | How far back the most delayed part of the picture lies, in seconds, up to History. While the history fills, after a pause or after History changes, it reaches only as far back as the history does. It glides to a new value at up to 1 s a second, whether set here or by the music (see [Accessibility](#accessibility)). Grayed out for Slit. |
| Angle | 270 | Where Sweep's past lies, in degrees counterclockwise from the right. At 270 the top of the picture is now and each row down is a moment older. At 0 the left is now and the right lags, and at 90 the bottom is now. |
| Spin | 0 | How fast Sweep's Angle turns, in degrees a second (-90 to 90), like turning a slice through the block of time. At delays over 1.5 s it turns more slowly, in proportion (see [Accessibility](#accessibility)). |
| Center X, Center Y | 0.5, 0.5 | Where the rings' center is, from 0 to 1 across and up the picture. The center is now and time recedes outward. |
| Scale | 2 | How many of Liquid's swirls fit the picture's height (0.5 to 8). |
| Drift | 0.2 | How fast Liquid's noise changes (0 to 1). At delays over 1.5 s it changes more slowly, in proportion (see [Accessibility](#accessibility)). |
| Film | Right | Which way Slit's film runs. With Right or Left the slit is a vertical line and with Down or Up a horizontal one, and the strip lies on the side the film runs to. |
| Position | 0.5 | Where the slit is, from 0 to 1 across the picture in Film's direction. The live picture lies on one side of it and the strip on the other, and at 0 the whole picture is strip. |
| Speed | 80 | How fast Slit's film runs, in pixels a second at 720 high (10 to 120, scaling with the picture). Slower squeezes more time into the strip, so things crossing the slit come out narrower. It stops at 120, louder music included (see [Accessibility](#accessibility)). |
| Bands | 0 | Cuts the map into this many steps of time (up to 32), each its own moment, with hard edges between them. At 0 the map is smooth. Grayed out for Slit. |
| Reverse | Off | Turns the map end over end, so what lagged most is now and what was now lags most. Slit runs its film the other way. |
| History | 2 | How many seconds of the input are kept on the GPU (0.5 to 8). [Memory](#memory) says what each second costs. Changing it starts the history again. |
| History Size | Full | The resolution the history is kept at. Half takes a quarter of the memory and Quarter a sixteenth, and the past looks softer. The newest moment always comes from the input itself, at its full size. Changing it starts the history again. |
| Between Frames | Flow | How the moments between the input's frames are filled in. Flow moves the frames either side along the movement between them, Blend mixes them, and Steps shows whichever frame was showing (see [How it works](#how-it-works)). |
| Flips | On Bars | When the map flips end over end, sliding over a quarter second (longer at delays over 1.5 s). On Bars flips on the one of each bar and On Beats on every beat, both from input 2, and with nothing wired every 2 s. Steady flips every 2 s and Off never. A flip changes the whole picture, so it counts as a flash, and Flashing limits how often they come. Slit doesn't flip, since its film would lose the strip. Grayed out for Slit. |
| Beat Kick | 0.5 | How hard each beat tears the picture, 0 to 1. For 0.15 s three thin slivers of rows, one in each third of the picture, open onto a moment further back, up to 0.8 s at 1 (0.4 s at the default). In Slit they land on the film and ride away with it. Flashing Off stops them. |
| Loudness | 0.5 | How much the music's loudness on input 2 sets how far back the picture reaches, 0 to 1. Louder reaches further and quieter less: at 1, from about half of Delay in quiet passages to one and a half times it in loud ones. In Slit it runs the film faster. Loudness is eased over half a second, so the delay swells and fades without jitter. |
| Song Moments | On | With Fosfora's signal on input 2, a build reaches further back as it rises, up to twice Delay at its peak, and a drop freezes time for Length seconds. |
| Length | 0.5 | How long a drop freezes time, in seconds (0.1 to 1.5). Grayed out with Song Moments off. |
| Flashing | Calm | How often a flip or a freeze may come. Off never, Calm at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. Off also stops the beat's tears. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The maps

![Six views of the dancer, each named in the library's pixel font. INPUT is the clip as it is. SWEEP, the default, shows her with the top of the picture now and each row down a moment older, so her limbs twist away from her body as she turns. RINGS has the middle now and the edges older, so her legs and outstretched hands lag behind her body. DEPTH has her, the nearest thing, now and the room behind her earlier. LIQUID pools earlier moments in soft drifting patches, so parts of her come apart. SLIT shows the live picture left of the middle and the strip to its right, her arms streaming out as ribbons. Where the clip loops back to its start, the cut sweeps across the delayed parts as a wipe](slit_scan_maps.webp)

*Every map on the dancer at its defaults, with the clip as it is in the corner. The clip loops with a
cut, which sweeps through each map as a wipe.*

**Sweep** grows the delay straight across the picture, a slice through the block of time at a tilt, as
Fels and Mase cut their video cube with a plane. At the default Angle the top is now and the bottom
1.5 s ago, so a figure turning on the spot twists like a corkscrew and anything moving sideways leans.
Spin turns the slice, so the lean goes round.

**Rings** grows the delay with the distance from a center, a cut along a sphere. The middle is now and
the corners lag most, so whatever crosses the middle stretches out behind itself. Reverse puts the past
in the middle.

**Depth** takes the delay from input 3. Nearer is now and farther lags, so with a depth map of a
dancer she is now and the room behind her is a moment ago, and wherever she has just been the room
still holds her. With a mask, inside is now. Reverse makes the near (or inside) parts lag, so a person
moves through the room as their own past. With nothing on input 3 the brightness stands in, and the
bright parts are now.

**Liquid** takes the delay from a smooth noise that drifts, so time pools and flows across the picture
like oil on water, and moving things melt where they cross it.

**Slit** is strip photography. A slit across the picture sees one line of it, and film runs past the
slit, so each moment of that line is laid down beside the slit and carried away. Things standing still
on the slit smear into streaks, and moving things are drawn by how they cross it, so a dancer's arm
sweeping through the slit becomes a ribbon. The other side of the slit shows the live picture. The film
is a picture of its own, built up over time, so the strip can show far more time than History holds.

## Memory

The history lives on the GPU, as every frame the project made over the last History seconds: 60 a
second at 60 fps, whatever the input's own frame rate. A 30 fps camera's frames are each kept twice, and
a 16 fps clip's nearly four times. That costs memory but keeps the history steady however the input
arrives (see [How it works](#how-it-works)). The table gives what the whole effect takes on the GPU,
measured with `TOP.gpuMemory` on the reference machine, in MB (millions of bytes):

| Input | History | Full | Half | Quarter |
|---|---|---|---|---|
| 1280 x 720 | 1 s | 283 | 81 | 29 |
| 1280 x 720 | 2 s (the default) | 546 | 149 | 47 |
| 1280 x 720 | 8 s | 2,125 | 558 | 152 |
| 1280 x 1280 | 1 s | 471 | 134 | 49 |
| 1280 x 1280 | 2 s | 910 | 247 | 79 |
| 1280 x 1280 | 8 s | 3,542 | 922 | 259 |

Each second of History adds about 263 MB at 1280 x 720 at Full, 68 at Half and 18 at Quarter, and at
1280 x 1280, the free license's largest picture, 439, 112 and 30. Almost all of it is the picture
itself, 8 bits for each of red, green, blue and alpha; the flow that comes with each frame adds about
6%. A 720-high picture measures 7% over width x height x 4 bytes a frame, as if its rows were padded
to 768. History Size Half keeps a quarter of the pixels, so the past looks softer, but the newest
moment always comes from the input at its full size. Changing History or History Size makes the
rings anew, and the history grows back in over the next seconds.

## How it works

**The history.** Three Texture 3D TOPs each hold a ring of slots that TouchDesigner fills one slot a
frame. `pics` keeps the picture (8-bit, at History Size), `flows` the optical flow that came with it
(the library's Lucas-Kanade flow, at a quarter of that size, as two 16-bit floats), and `stamps` a
stamp for each slot. A Texture 3D TOP doesn't say which slot it wrote last, so the stamp records which
frame wrote the slot (a count kept on the GPU), which input frame it holds (a count of the input's new
frames), when that input frame came, and when the slot was written. `frames` finds the newest slot by
its stamp, walks back while each stamp follows on from the next, and lists the input's frames newest
first with how long ago each one came. A clip slower than the project fills several slots with one
frame, and the list keeps that frame once, at the slot where it first appeared, which is where its
flow is the movement since the frame before. Slots the rings never wrote, slots from before History
changed, and slots left from before a pause (an effect nobody watches stops cooking) all fail the walk,
so they never show, and the history grows back in from the live picture.

**Each pixel's moment.** `scan` works out the map at each pixel (0 is now and 1 is Delay ago), applies
Bands and Reverse, and looks that moment up in the list with a binary search, which finds the input
frame that was showing then and the one after it.

**Between frames.** Flow takes the movement between those two frames, which the flow ring stored with
the newer one, and moves each frame toward the moment in between before mixing them. What is at a
point at that moment was a fraction of the way back along the movement in the older frame, and the
rest of the way forward in the newer one. Blend mixes the two frames as they are, so moving edges
double, and Steps shows the older one, so a slow input breaks into bands of whole frames. Every moment
is looked up one input frame later than asked. A moment between the newest frame and now has no next
frame to fill in toward, so without that the picture near now would hold each frame, and the slit
would lay steps. The cost is a lag of one of the input's frames, as any frame interpolation has.

**The slit.** `slit` keeps its film in a Feedback TOP (`slit_fb`). Each frame the film moves on as far
as it ran, resampled with the library's Catmull-Rom filter so it stays sharp, and the newest stretch
beside the slit is filled from the history at the moments between this frame and the last. The film
is continuous however slow the input is. Every pixel Slit shows passes the library's red guard, which
keeps very saturated reds a little short of WCAG's saturated-red line (see [Accessibility](#accessibility)).

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it
into input 2. The map flips on its bars (or on its beats, with Flips at On Beats), its beats tear the
picture, and louder music reaches further back. With Song Moments on, two more things happen.

- **Builds** reach further back as they rise, up to twice Delay at the peak.
- **Drops** freeze time for Length seconds. Every pixel holds the moment it was showing while the
  input goes on, then time starts again at once. A freeze passes the same Flashing gate as the flips.
  Fosfora's drop detection is experimental.

**Any input** brings flips on its bars (On Bars) or beats (On Beats), tears on every beat, and the
delay swelling with loudness. Raw audio (an Audio File In or Audio Device In CHOP) gives beats from a
kick detector and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then
come on the beat even when a kick is missed, a kick between beats is left out, and a bar is every 4
beats (which beat starts the bar is a guess). It stops 8 beats after the kicks do, and while it isn't
locked every kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset channels.

On the library's test song (`dev/reaction.py`), in the 0.2 s after a beat the picture changes 1.74
times as much as in the 0.2 s before it (1.01 with nothing on input 2, the clip's own moves), from the
tears, close to Glitch's (1.8). A bar adds 1.46 times more than the other beats, from the flip.
Loudness moves the picture a little (a correlation of 0.17 with how much it changes), since it only
deepens the delay.

**Nothing wired:** a flip every 2 s, with the tears, so the effect shows itself.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with default parameters. Each frame took 3.7 ms on the GPU (95th
percentile 4.2 ms) and 0.56 ms on the CPU (95th percentile 0.76 ms), the median of three runs. The
optical flow costs the most, 2.3 ms of it (the library's Lucas-Kanade flow at an eighth and a quarter
of the size), then the scan (0.6 ms) and the frame list (0.3 ms). Writing each frame into the history
costs little. The flow runs whatever Between Frames is set to, so Blend and Steps cost about the same.
Nothing inside cooks while the output is unused. The history grows with History, not the time per
frame (see [Memory](#memory)).

## Accessibility

- **Flashing.** A flip changes the whole picture at once, and so does time starting again after a
  drop's freeze, so both count as flashes. They pass one gate that follows the Flashing parameter:
  Off never lets one through, Calm (the default) at most one a second, and Up to 3 per second is the
  WCAG 2.3.1 limit, which no setting exceeds. After the gate a budget keeps them at least 0.75 s apart
  even at Up to 3.
- **Beats.** Each beat tears three thin slivers of rows, 2 to 6 rows tall and one in each third of the
  picture, open onto an earlier moment for 0.15 s. That is too little of the picture to count as a
  flash, as Glitch's slivers are, so they don't need the gate, and Flashing Off stops them anyway. A
  band of extra delay running through the map on every beat was tried first. It moved whole areas back
  and forth in time, which is a jolt wherever the picture moves, and measured 3 to 4 flashes a second at
  Calm on red flowers and koi, mostly red ones. Slit's film surging on the beat measured 3.
- **Time never sweeps past too fast.** Slit-scan only re-times the picture, so a still input stays
  still and a flashing one flashes no more than it did, as long as the map holds still. A map that
  moves sweeps time past each point, and faster than the picture's own movement it shows the picture's
  changes, and its flashes, faster too, with Flashing Off as much as on. The speed is the delay times
  how fast the map moves, so the limits scale with the delay. The delay glides to new values at up to
  1 s a second, whether set from the page or by loudness or a build. Spin and Drift slow down at delays
  over 1.5 s, in proportion, so time sweeps past no faster than at Spin 90 or Drift 1 at a 1.5 s delay.
  A flip's slide lasts longer at long delays. Before these limits, Drift 2 at the default delay added a
  flash a second with Flashing Off on the dancer, and Drift 1 or Spin 90 at an 8 s delay added one or
  more on the plaza and the flowers, red ones too.
- **Slit.** The film spreads whatever flickers on the slit line across the strip, and the faster it
  runs the wider each flicker lands, until it fills whole areas. With Flashing Off, red flowers
  measured 1.0 flash a second at 80 pixels a second (the clip alone measures 1.0), 1.5 at 120, 2.0 at
  160 and 4.0 at 1000. So Speed stops at 120, louder music included, and defaults to 80. Every pixel
  Slit shows passes the library's red guard, which keeps very saturated reds a little short of WCAG's
  saturated-red line, so an orange there comes out a little lighter. Guarding only the film as it was
  laid still measured 2 red flashes a second on the flowers, since moving the film resamples it and
  can mix one pixel's red with its neighbor's green and blue.
- **No meaning in color.** The effect draws nothing of its own and signals nothing by hue.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far
busier than music (8 beats, 2 bars and 1 drop a second) and counted the flashes in the worst second,
by WCAG's area rule:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 1.5 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.0 | 1.5 | 1.0 |
| Dancer, no beat (steady flips) | 1.0 | 1.0 | 1.0 | 1.0 |
| People crossing a plaza | 0.5 | 1.0 | 1.0 | 0.5 |
| Red flowers against the sky | 1.0 | 1.0 | 1.5 | 1.0 |
| Koi in a black pond | 0.5 | 1.5 | 1.5 | 0.5 |
| Dancer, Beat Kick 1 | 1.0 | 1.5 | 1.5 | 1.0 |
| Flowers, Beat Kick 1 | 1.0 | 1.0 | 1.0 | 1.0 |
| Koi, Beat Kick 1 | 0.5 | 1.5 | 1.5 | 0.5 |
| Dancer, Slit, Beat Kick 1 | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, Slit at Speed 120, Beat Kick 1 | 1.5 | 1.0 | 1.0 | 1.0 |
| Koi, Slit at Speed 120, Beat Kick 1 | 1.0 | 0.5 | 0.5 | 0.5 |
| Flowers, Liquid at Drift 1, Delay and History 8, Beat Kick 1 | 1.0 | 2.0 | 1.5 | 1.0 |
| Flowers, Spin 90, Delay and History 8, Beat Kick 1 | 0.5 | 1.0 | 1.5 | 1.0 |
| Dancer, 32 Bands, Steps, Beat Kick 1 | 1.0 | 1.5 | 1.5 | 1.0 |
| Plaza, Rings, 8 Bands, Delay and History 8, Beat Kick 1 | 0.5 | 0.5 | 0.5 | 0.5 |

Each is within its setting's rule. Off adds nothing to what the clip does by itself beyond the
measurement's half-flash margin, Calm adds at most one a second, and nothing passes WCAG's 3. Red
flashes, which WCAG counts separately, followed the clips' own (1.0 a second on the flowers and 1.5 on
the koi, which both clips make by themselves): at most 1.0 a second at Off, 2.5 at Calm (the flowers
at Drift 1 and an 8 s delay) and 2.0 at Up to 3, none on the dancer or the plaza, and none in Slit,
whose reds are guarded.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It
  takes a few beats to lock and can still add or miss beats where the kicks don't keep the beat, and
  which beat starts a bar is a guess. Fosfora or audioAnalysis give steadier beats.
- Filling in along the movement (Between Frames, Flow) follows the library's optical flow, which
  can't see what was hidden behind something that moved. Where a moving edge uncovers the background,
  the moments in between show a little of both frames.

## Credits and license

MIT. The shaders and operators are written for this library, including the history's stamps and
frame list, the maps, the slit's film, the tears and the music.

- **Slit-scan as an art form:** Golan Levin's
  ["An Informal Catalogue of Slit-Scan Video Artworks and Research"](https://www.flong.com/archive/texts/lists/slit_scan/index.html)
  (flong.com, 2005 to 2015).
- **The block of time cut by a plane or a sphere** (Sweep, Spin, Rings): S. Fels and K. Mase,
  "Interactive Video Cubism" (Workshop on New Paradigms for Interactive Visualization and Manipulation,
  1999), and S. Fels, E. Lee and K. Mase,
  ["Techniques for Interactive Video Cubism"](https://hci.rwth-aachen.de/publications/fels2000a.pdf)
  (ACM Multimedia 2000). Followed, not copied.
- **Strip photography** as photo-finish cameras take it (Slit), and Martin Reinhart's tx-transform
  (1998), which swaps time and one direction of the picture.
- **Filling in between frames along the motion**, the two frames warped toward the moment between
  them and mixed, is a widely known technique. The motion is the library's Lucas-Kanade optical flow
  (B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to Stereo
  Vision", 1981), and the film is resampled with the library's Catmull-Rom filter.
- **Dice:** Chris Wellons' lowbias32 integer hash
  ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain), for Liquid's value
  noise and the tears.
- **Seen during the survey, not used:** FollowTheDarkside's
  [td-slitscan](https://github.com/FollowTheDarkside/td-slitscan) (no license stated), instant
  infinite's ["Slit scan with Texture3D & TimeMachine"](https://instantinfinitework.gumroad.com/l/yuzkh)
  project file (no license stated), elekktronaut's [Slitscan tutorial](https://youtu.be/jOcMCGtclBs),
  and TouchDesigner's [Time Machine TOP](https://docs.derivative.ca/Time_Machine_TOP) and its OP
  Snippet.
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
Depth map's preview was estimated from it with Depth Anything 3's Mono-Large model (Apache 2.0).
