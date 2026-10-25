# Bent Cam

![Bent Cam on a dancer in a hazy warehouse: the shadows are a deep purple full of colored grain, the fog behind her is a pale cloud ringed in black and gray contours, her figure glows yellow and pink, thin green lines and short stripes of false color cross the dark, and on the bars of the music the whole frame turns green and pink or breaks into streaks for a moment](bent_cam.webp)

**New to circuit bending?** Circuit bending means opening up a cheap electronic device and soldering
wires across its circuit board so it breaks in interesting ways. Done to an old webcam, wires across
the pins of its sensor chip garble the bytes the picture travels on. The picture comes out in false
colors, flat bands, torn lines and broken blocks. Point that camera at a small screen showing its own
picture and it films itself filming itself, so the damage repeats into trails, tunnels and spirals,
and the screen's pixels beat against the camera's in rainbow moiré. VJs then mirror the result into a
kaleidoscope. A Reddit post of exactly that rig, "Circuit bent feedback loop - The fractal
microscope", drew hundreds of upvotes and comments asking how it was done.

This effect builds that rig as a model rather than drawing its look. The picture is on a screen, with
the camera's last picture over it. The camera films the screen through its lens and the red, green
and blue filters on its sensor, then processes the picture as webcams do, 30 times a second, and that
picture goes round the loop. On its way out the picture travels as bytes over the sensor's bus, where
the shorts bend it. The camera compresses each frame as a JPEG, the cable loses bits, and the
computer decodes what arrives and scales it up. A lot of 50 cameras, each shorted differently, gives
50 different looks (see [The lot](#the-lot)). On the bars of the music a wire touches for a moment.
Circuit-bending components for TouchDesigner exist as tutorials and a tutorial-derived `.tox`, which
imitate the look with displacement and color shifts. None models the bytes, the compression or the
camera filming its screen, and none follows the music. This one is MIT and runs on any GPU.

![Bent Cam with Mirror set to Kaleidoscope, Camera 38, Feedback 0.8 and Rotate 2, on red flowers against the sky: a pink and violet six-way star with the flowers' centers at its heart, fine rainbow moiré from the screen's pixels across the petals, and a thin hexagon where the tilted camera sees the screen's edge](bent_cam_kaleido.webp)

*Mirror set to Kaleidoscope with Camera 38, Feedback 0.8 and Rotate 2, on the flowers.*

**[Download bent_cam.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/bent_cam.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `bent_cam.tox` into your network. It shows TouchDesigner's sample movie (mist over a lake)
   through a bent camera straight away, with a wire touching every 2 s.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. A webcam's picture is
   the obvious input, but any video stands in for what the camera sees.
3. Optional: wire audio or beat channels into input 2 (see Audio input). The bursts then follow its
   bars.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `bent_cam.tox`. Dragging a `.tox` in embeds a copy,
so a new release doesn't reach it on its own. You can also point the COMP's External .tox at a
downloaded file.

## Parameters

The Bent Cam page, top to bottom, in five groups: the shorts, the camera's resolution and its JPEG,
the camera filming its screen, the mirror, and the music.

| Parameter | Default | What it does |
|---|---|---|
| Camera | 8 | Which camera from the lot of 50 (see [The lot](#the-lot)). Each has six shorts on different pins. |
| Shorts | 0.35 | How many of the camera's shorts are connected, 0 to 1. Each sticks or bridges one of the data lines the picture travels on, so tones break into flat bands of odd colors. The one being connected touches on and off, in pieces of lines that come and go. At 0 the camera works. |
| Byte Slip | None | The bridge chip takes the bytes 1, 2 or 3 places late. At 1 or 3 it reads color as brightness and brightness as color, so dark parts turn green and light parts pink. At 2 the two colors swap and reds turn blue. |
| Clock Slips | 0.2 | How often the pixel clock gains or loses a tick, 0 to 1. The bytes then come a place early or late until the clock gains or loses one back, and that stretch of the line turns to false color. A quarter of the slips never recover and run to the end of the line. Each stays a moment. |
| Sync | 0 | How far the sensor's lines are from the length the bridge expects, 0 to 1. The picture shears, and breaks into bands of false color where the bytes slip a place. |
| Sensor | 640 x 480 | The camera's resolution, with the picture's aspect fitted into it (640 x 480 takes a 16:9 picture at 640 x 360). Old webcams gave 640 x 480 or less, so each of their pixels shows, and the JPEG's blocks with them. Also 320 x 240 and 1280 x 720. |
| Compression | 0.5 | How hard the camera compresses each frame as a JPEG, 0 to 1, from quality 100 down to 5. Blocks of 8 x 8 pixels and ringing around edges. |
| Block Errors | 0.2 | How often the cable loses bits, 0 to 1. From a block on, up to the stream's next restart marker (every 8 blocks), the brightness and color drift and the detail turns to stripes. Each error stays a moment. |
| Feedback | 0.5 | How much of the camera's own picture the screen shows over the input, 0 to 0.85. The camera films itself filming itself, which makes trails, and with Zoom and Rotate, tunnels and spirals. |
| Zoom | 1.02 | How close the camera is to the screen, 0.7 to 1.03. Above 1 it sees part of the screen, so the picture grows outward on each pass round the loop, 30 passes a second. Below 1 it sees the whole screen in its black bezel, a tunnel. |
| Rotate | 0 | How far the camera is tilted, -2 to 2 degrees. The picture turns that much on each pass, so trails become spirals. |
| Focus | 0.8 | How sharply the lens is focused on the screen, 0 to 1. Sharp, the camera sees the screen's pixels beat against its own (moiré). Soft, the picture blurs, more on each pass. |
| Moiré | 0.5 | How much the screen's red, green and blue stripes show to the camera, 0 to 1. Where they beat against the sensor's pixels they make bands of color. Focus softens them. |
| Contrast | 1.1 | The contrast the camera adds (0.5 to 1.5). In the loop it builds up on every pass, so above 1 the trails turn bold and flat. |
| Saturation | 1.2 | The color the camera adds (0 to 2). In the loop it builds up on every pass and eases off as colors grow strong, so the trails turn vivid and keep their hues. |
| Noise | 0.3 | The sensor's noise, 0 to 1, grain that grows with the light and is new on every frame. Where a camera's shorts bridge a high data line to a low one, the noise flips the high one too, as colored speckle. |
| Mirror | Off | Tile the picture, as VJ apps do with a bent camera. Left-Right mirrors the left half onto the right, Four Ways puts the top-left quarter in all four corners, and Kaleidoscope folds wedges around the middle. |
| Segments | 6 | How many wedges the Kaleidoscope makes (2 to 16). Grayed out unless Mirror is Kaleidoscope. |
| Bursts | On Bars | When a wire touches for a moment. Each burst does one of three things: the bytes slip a place (the frame turns green and pink), every one of the camera's shorts connects at once, or the JPEG stream breaks from a block in the top half to the end of the frame. On Bars (the one of each bar) and On Beats follow input 2, and with nothing wired a burst comes every 2 s. Steady is every 2 s, Off never. |
| Length | 0.3 | How long a burst lasts, in seconds (0.1 to 1). |
| Song Moments | On | With Fosfora's signal on input 2, a build connects more of the shorts as it rises, and a drop throws the frame's start off for a moment, so the picture jumps down a third. |
| Flashing | Calm | How often a burst may come. Off never, Calm at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. Off also stops the beat's slivers. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The lot

![Every camera in the lot on the same frame of the dancer, numbered 1 to 50 in five columns. Some turn the whole picture green, some magenta, some cream, purple or gray, with the fog cut into contoured bands. Under each picture are its eight data lines, D7 to D0, and its six shorts, one row each: a downward triangle for a line grounded, an upward one for a line tied to power, and a bar between two lines ending in downward triangles (the lower of the two wins) or upward ones (the higher wins). Shorts that pull toward 0 are blue and those that pull toward 1 orange. The first two rows are bright, connected at the default Shorts, and the rest faint](bent_cam_lot.webp)

Each camera in the lot has six shorts, on data lines D4 to D7 (the ones whose faults show), and Shorts
connects them in order. The sheet above shows every camera at the default Shorts, 0.35, which
connects the first two, with Clock Slips, Block Errors and Bursts off so only the shorts show. Under
each picture, its pins from D7 to D0 and its shorts, a row each. A downward triangle is a line wired
to ground, which then always reads 0, and an upward one a line tied to power, which always reads 1. A
bar joins two lines bridged together. Both then read the lower of the two (downward triangles at its
ends) or the higher (upward ones). Blue marks a short that pulls toward 0 and orange one that pulls
toward 1, and the shapes say the same without the color. Bright rows are connected at the default
Shorts, faint ones as Shorts rises.

D7 carries 128 of each byte's value. A byte of color is 128 where there is no color, exactly D7 alone,
so a camera with D7 grounded (or bridged to a line that reads 0, low winning) turns every gray a strong
green, and one with D7 tied to power turns the darks bright and the colors pink. A short on D4 only
moves values by 16 and draws fine contours. The README inside the `.tox` lists every camera's shorts
in words. The table lives in `effects/bent_cam/src/lot.py`, drawn with a hash, the same on every
build, so a camera stays the same camera.

## How it works

The network inside, left to right, works at the camera's resolution until the last step.

**The camera filming its screen.** `screen` shows the picture with the camera's last picture over
it, as much as Feedback says. `lens` blurs it by how far Focus is from sharp. `camera` looks at it the
way the camera does: each sensor pixel sees the point of the screen Zoom and Rotate put it on, through
one color filter of a Bayer mosaic (red, green or blue in an RGGB pattern). The screen has its own
pixels, each a red, a green and a blue stripe with a dark gap between rows, 1.25 of them to each of
the sensor's pixels (a 7-inch panel before a 640 x 480 sensor). The shader works out what each
sensor pixel sees of those stripes from their Fourier series, softened by the lens and by the width
of the sensor pixel, so the two grids beat into moiré where they would. A cheap lens darkens the
corners, and the sensor adds shot noise, which grows with the light, and read noise. `isp` is the
camera's processing. It fills in each pixel's two missing colors from its neighbors (bilinear
demosaicing, where moiré turns to color), then applies gamma, contrast and saturation (eased toward a
ceiling, so the loop doesn't run every hue to one pure color), the red guard, and temporal noise
reduction that blends each frame half and half with the last, as webcams do. It runs 30 times a
second and holds its picture in between, so the loop turns at the camera's rate whatever
TouchDesigner's frame rate is. `feed_fb` takes that picture back to `screen`.

The loop takes the camera's picture before the bus. A byte slip that swaps brightness and color,
inside the loop, swaps it back on the next pass, so a real rig's whole picture strobes at the
camera's frame rate. Here the shorts bend the picture once, on its way out.

**The bus.** `bus` turns the camera's picture into the bytes its sensor sends: each line as YUYV, for
each pair of pixels the first one's brightness, the pair's blue difference, the second one's
brightness and the pair's red difference, in BT.601's 8-bit ranges. It reads them back as the bridge
chip does, one byte per tick of the pixel clock over eight data lines, and puts the faults where the
wires are. A short changes a data line in every byte that passes. A byte slip moves the bridge's
count. A clock slip moves the bytes a place for a stretch of a line, and Sync starts each line a
little later in the stream than the last. On the beat, a sliver of six lines slips somewhere new.

**The JPEG.** `dct` cuts the frame into blocks of 8 x 8 pixels for brightness and 16 x 8 for color
(the stream's color already covers pairs of pixels), turns each block into its 64 cosine coefficients
and rounds them to the steps of the JPEG standard's tables, scaled to the quality Compression gives,
as libjpeg scales them. A lost bit makes the decoder misread the stream from some block on. Each
block's average is stored as a change from the block before, so every block after the error is off
by all the errors so far, and its detail turns to stripes, up to the stream's next restart marker
(every 8 blocks), which puts the decoder right. `idct` decodes each pixel from its blocks'
coefficients and turns brightness and color back into red, green and blue.

**Out.** `out` scales the camera's picture up to the input's size, as the app showing it does,
applies Mirror, and runs the red guard on every pixel.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it
into input 2. Bursts follow its bars (or its beats, with Bursts set to On Beats), and with Song
Moments on, two more things happen:

- **Builds** connect more of the camera's shorts as they rise, up to half of them again at the peak.
- **Drops** throw the frame's start off, so the picture jumps down a third with its bytes out of
  step, and it snaps back after Length, through the same Flashing gate as every burst. Fosfora's drop
  detection is experimental.

**Any input** brings bursts on its bars (On Bars) or beats (On Beats), and a sliver of slipped lines
on every beat. Raw audio (an Audio File In or Audio Device In CHOP) gives beats from a kick detector
and a beat clock. Once the kicks keep to a tempo, the clock locks to them, beats then come on the
beat even when a kick is missed, a kick between beats is left out, and a bar is every 4 beats (which
beat starts the bar is a guess). It stops 8 beats after the kicks do, and while it isn't locked every
kick is a beat. TouchDesigner's audioAnalysis gives beats from its kick or onset channels.

On the library's test song (`dev/reaction.py`), the bars are what shows. In the half second after a
bar the picture is 4.4 times as far from the clip as in the half second before it, the strongest
response to bars in the library. The beat's sliver is small on purpose (a few lines, too little to
count as a flash) and gets lost in the camera's own noise, which changes every frame: the picture
changes no more in the 0.5 s after a beat than before it (0.98 times as much). Loudness doesn't drive
anything.

**Nothing wired:** a burst every 2 s, so the effect shows itself.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6,
TouchDesigner 2025.33230), with default parameters. Each frame took 1.44 ms on the GPU (95th
percentile 2.2 ms) and 0.33 ms on the CPU, the median of three runs. The JPEG costs the most: the
decoder 0.8 ms and the encoder 0.3 ms, each reading 128 values for every pixel. Everything before the
last step works at the Sensor's resolution, so 1280 x 720 costs about four times as much as the
default 640 x 480, and the input's size matters only for the last step. Nothing inside cooks while
the output is unused.

## Accessibility

- **Flashing.** A burst is a flash. Each passes one gate that follows the Flashing parameter: Off
  never bursts, Calm (the default) allows at most one a second, and Up to 3 per second is the WCAG
  2.3.1 limit, which no setting exceeds. After the gate, a budget keeps this effect to about 1.3
  bursts a second even at Up to 3, since each kind of burst changes the whole frame differently. Off
  also stops the beat's slivers.
- **No flicker of its own.** A burst's damage holds still while it lasts, and a drop's jump is one
  jump and one jump back. Clock slips, shorts touching on and off, and block errors each cover part of
  a line or a few blocks and stay a moment, too small and too slow to count. Clock slips are mostly
  stretches spread over the frame, since slips that all ran to the right edge piled up there and
  flashed. The sensor's noise is fine-grained and evens out over any area WCAG counts.
- **The feedback loop.** With Zoom above 1, every movement echoes outward, and each echo that passes
  a point is another swing between light and dark there, made sharp by the shorts' hard-edged bands.
  At Feedback 0.95 and Zoom 1.1 that measured 4.5 flashes a second with Flashing Off on the flowers, so
  Feedback stops at 0.85, Zoom at 1.03 and Rotate at 2 degrees either way. At those limits the loop
  adds no flashes even with every fault at 1 (the last row below). A tunnel (Zoom below 1) shrinks its
  echoes and stays calm.
- **Red.** Saturation builds up round the loop, and WCAG counts a pixel as saturated red once red is
  80% of its light, all or nothing. Very saturated reds and oranges are kept a little short of that
  line, inside the loop and on every pixel shown, so an orange comes out a little lighter. The effect
  made no red flashes at all in the tests below.
- **No meaning in color.** Nothing is signaled by hue. On the lot's sheet, the shapes of the marks
  say what the colors do.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far
busier than music: 8 beats, 2 bars and 1 drop a second. The table gives the flashes in the worst
second, by WCAG's area rule:

| Clip | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse (worse of two runs) | 1.5 | 2.0 | 2.0 | 1.0 |
| Dancer, a dance-tempo beat (140 BPM) | 1.0 | 1.5 | 1.5 | 1.0 |
| Dancer, no beat (steady bursts) | 1.0 | 1.5 | 1.5 | 1.0 |
| People crossing a plaza | 0.5 | 1.5 | 1.5 | 0.5 |
| Red flowers against the sky | 1.0 | 1.5 | 1.5 | 1.0 |
| Koi in a black pond | 1.0 | 2.0 | 2.0 | 0.5 |
| Red flowers, every fault at 1, Feedback 0.85, Zoom 1.03, Rotate 2 | 1.0 | 1.5 | 1.5 | 1.0 |

Each is within its setting's rule: Off adds nothing to what the clip does by itself beyond the
measurement's half-flash margin, and Calm at most one a second. On the koi, Off measures 1.0 where the
clip's brightness measures 0.5, under the clip's own red flashing (1.5 a second), which is what the
rule holds it to. Red flashes, which WCAG counts separately, measured none at any setting on any clip.
Four earlier versions failed these tests and changed: beat slips on every line measured 4 flashes a
second at Calm, the loop at Feedback 0.95 and Zoom 1.1 measured 4.5 with Flashing Off, Feedback 0.8 at
Zoom 1.05 still added one, and bursts 0.55 s apart measured 4 at Up to 3 on the dancer.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It
  takes a few beats to lock and can still add or miss beats where the kicks don't keep the beat, and
  which beat starts a bar is a guess. Fosfora or audioAnalysis give steadier beats.

## Credits and license

MIT. The shaders and operators are written for this library, including the faults' models, the lot,
the moiré from the screen's stripes, the bursts and the red guard (shared with VHS + CRT).

- **The idea:** the Reddit post "Circuit bent feedback loop - The fractal microscope" (2026), a
  circuit-bent laptop webcam on a microscope mount filming a 7-inch screen showing its own picture,
  tiled into a kaleidoscope. Its look and its rig, not its code, which isn't published.
- **Circuit bending:** Reed Ghazala's name and practice for shorting the circuits of cheap electronics.
- **Video feedback** as a camera filming its own screen, with zoom, rotation and gain: J. P.
  Crutchfield, "Space-time dynamics in video feedback" (Physica D 10, 1984).
- **The bytes:** YUYV (YUY2) 4:2:2 order as USB webcams send it, and ITU-R BT.601's YCbCr matrix and
  8-bit ranges.
- **The sensor:** the Bayer color filter mosaic (B. E. Bayer, US patent 3,971,065, 1976) and bilinear
  demosaicing. Temporal noise reduction as webcams' image processors do it.
- **The JPEG:** ITU-T T.81 (1992), its DCT and its Annex K quantization tables, scaled by quality as
  the [Independent JPEG Group's libjpeg](https://ijg.org/) does, its restart markers, and its DC
  coefficients stored as the change from the block before.
- **Dice:** Chris Wellons' lowbias32 integer hash ([hash-prospector](https://github.com/skeeto/hash-prospector), public domain), which also draws the lot.
- **Seen during the survey, not used:** elekktronaut's
  [Circuit Bending tutorial](https://youtu.be/mAp_wxuuw_U), aaronmylespereira's
  `circuitBending_MYLES.tox` ([TD-Toxes](https://github.com/aaronmylespereira/TD-Toxes), MIT,
  after that tutorial), the Palette's feedback component and TouchDesigner's Mirror TOP.
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
[repository README](../../README.md#demo-footage)) and shows no real person. The second preview is
the flowers from the same footage, and the lot's sheet holds one frame of the dancer.
