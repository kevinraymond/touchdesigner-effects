Bent Cam {v}: a circuit-bent webcam filming a screen that shows its own picture.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/bent_cam.md

Circuit bending means opening up a cheap electronic device and soldering wires across its circuit board,
so it breaks in interesting ways. Done to an old webcam, wires across the pins of its sensor chip garble
the bytes the picture travels on, and the picture comes out in false colors, flat bands, torn lines and
broken blocks. Point that camera at a small screen showing its own picture and it films itself filming
itself, so the damage repeats into tunnels and spirals, and the screen's pixels beat against the
camera's in rainbow moire. VJs then mirror the result into a kaleidoscope.

This effect models that rig rather than drawing its look. The picture is on a screen, with the camera's
last picture over it. The camera films the screen through its lens and its sensor's red, green and blue
filters, then processes the picture as webcams do, once a camera frame, and that picture goes round the
loop. On its way out, the picture travels as bytes over the sensor's bus, where the shorts bend it. The
camera compresses each frame as a JPEG, the cable loses bits, and the computer decodes what arrives and
scales it up. On the music, a wire touches for a moment.

USE
Drag bent_cam.tox into your network. It shows TouchDesigner's sample movie (mist over a lake) through a
bent camera straight away, with a wire touching every {steady:g} s. Wire any TOP into input 1, and the
result is on output 1 at the input's size. You can also wire audio or beat channels into input 2 (see
below). Open Window shows it full size, and Esc closes the window.

THE PAGE
Camera picks a camera from the lot, each shorted differently, and Shorts says how many of its shorts are
connected. Byte Slip makes the bridge chip read the bytes one, two or three places late. Clock Slips makes
the pixel clock gain or lose a tick here and there, and Sync makes the lines longer than the bridge
counts. Sensor is the camera's resolution. Compression sets how hard the camera compresses each frame,
and Block Errors how often the cable loses bits. Feedback is how much of the camera's own picture the
screen shows. Zoom, Rotate and Focus place the camera and its lens before the screen, and Moire is how
much the screen's pixels show. Contrast and Saturation are what the camera adds on every pass, and Noise
is its sensor's grain. Mirror tiles the picture (Left-Right, Four Ways or Kaleidoscope, with Segments
wedges). Bursts says when a wire touches (On Bars, On Beats, Steady every {steady:g} s, or Off), Length
how long it touches, Beat Kick how hard each beat hits the rig, and Song Moments follows Fosfora's builds
and drops.

THE CAMERA
The screen has red, green and blue stripes for pixels, 1.25 of them for each of the sensor's pixels (a
7-inch panel before a 640 x 480 sensor). Each sensor pixel sees one color through its filter (red, green
or blue, in a Bayer mosaic), and the two grids beat into moire, which turns to color when the camera fills
in each pixel's other two colors from its neighbors. The lens blurs the screen and its stripes when Focus
is low, and darkens the corners. The sensor adds noise that grows with the light. The camera then applies
gamma, contrast and saturation (which eases off as colors grow vivid, so round the loop they don't all run
to one pure color) and blends each frame half and half with the last, the temporal noise reduction webcams
do. It does that 30 times a second and holds its picture in between, so the loop goes round at the
camera's rate whatever TouchDesigner's frame rate is. The loop takes the camera's picture
before the bus. A swap of brightness and color inside the loop would swap back on the next pass, so in a
real rig the whole picture strobes at the camera's frame rate.

THE BUS
The sensor sends each line as bytes in YUYV order: for each pair of pixels, the first one's brightness,
the pair's blue difference, the second one's brightness and the pair's red difference, in BT.601's 8-bit
ranges. The bridge chip reads them over eight data lines. A short to ground or to power sticks a line at 0
or 1, and two lines shorted together both read the lower, or the higher, of the two. Each camera has six
shorts on the four highest lines, and Shorts connects them in turn. The one being connected touches on
and off, in pieces of lines that come and go. Read one byte late, brightness bytes land where color
belongs, so dark parts turn green and light parts pink. A clock slip moves the bytes a place until the
clock gains or loses a tick back, so a stretch of the line turns to false color. A quarter of them never
recover and run to the end of the line, and the bridge starts each line afresh. Lines that run long start
each one later in the stream than the last, so the picture shears and slips a byte every few lines, in
bands. On every beat the loose wires crackle. For a moment one of D3 to D7 flips on a scattering of
bytes all over the picture, a new scattering every camera frame and fewer as the beat fades (Beat Kick),
and the clock slips and block errors jump to new places.

THE LOT
Each camera's six shorts, in the order Shorts connects them. Grounded lines read 0, lines tied to power
read 1, and bridged lines both read the lower (low wins) or the higher (high wins) of the two. D7 carries
128 of each byte's value and D4 carries 16. A neutral color byte is exactly 128, so a camera with D7
grounded turns every gray green.
{lot}

THE JPEG
The camera cuts each frame into blocks of 8 x 8 pixels for brightness and 16 x 8 for color, turns each
into its 64 cosine coefficients and rounds them to the steps of the JPEG standard's tables, scaled to a
quality from 100 down to 5. A lost bit makes the decoder misread the stream from a block on. Each block
stores its average as a change from the block before, so every block after the error is off by all the
errors so far, and its detail turns to stripes, up to the next restart marker (every 8 blocks), which puts
the decoder right. Errors come and go, each staying a moment.

AUDIO (input 2, optional)
Fosfora's signal is the best input. Run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into
input 2. Bars bring the bursts, when a wire touches for a moment: the bytes slip, every short connects at
once, or the JPEG stream breaks from a block to the end of the frame. With Song Moments on, a build
connects more shorts as it rises, and a drop throws the frame's start off, so the picture jumps down a
third for a moment (Fosfora's drop detection is experimental). With any input, bursts come on its bars or
beats, and every beat makes the wires crackle and moves the slips and block errors. Raw audio (Audio File In, Audio Device In) gives
beats from a kick detector and a beat clock that locks to the kicks' tempo (experimental: it can still
add or miss beats), and a bar every 4 beats. TouchDesigner's audioAnalysis gives beats from its kick or
onset channels. With nothing wired, a burst comes every {steady:g} s.

FLASHING
Every burst is a flash, and each goes through one gate that follows the Flashing parameter: Off lets
none through and turns off what beats do, Calm (the default) allows at most one a second, and Up
to 3 per second is the WCAG 2.3.1 limit. A budget after the gate keeps this effect to about 1.3 a second
even at Up to 3. A burst's damage holds still while it lasts and the jump is one jump and one jump back,
since damage that changed every frame would flash every frame. Clock slips, shorts touching on and off and
block errors each cover part of a line or a few blocks and stay a moment, too small and too slow to flash.
The beat's crackle comes on every beat without the gate because it is fine-grained, single bytes
scattered over the picture, so the light over any area hardly moves. A jolt of the camera on each beat and
a jump of its white balance were tried first, and both flashed at Calm under a fast beat, since the
shorts' hard-edged bands moved with them.
Saturation builds up round the loop, and WCAG counts a pixel as saturated red, all or nothing, once red is
80% of its light, so reds are kept a little short of that line, inside the loop and on every pixel shown.
With Zoom above 1, every movement echoes outward, and each echo that passes a point is another swing
between light and dark there, made sharp by the shorts' hard-edged bands. At Feedback 0.95 and Zoom 1.1
that measured 4.5 flashes a second with Flashing Off, so Feedback stops at 0.85, Zoom at 1.03 and Rotate
at 2 degrees either way, where the loop adds no flashes even with every fault at 1. A tunnel (Zoom below 1)
shrinks its echoes and stays calm.

INSIDE
The loop: source and feed_fb -> screen (the picture with the camera's last picture over it, at the
sensor's size) -> lens (Focus) -> camera (Zoom, Rotate, the screen's stripes through the Bayer mosaic,
the noise) -> isp (demosaicing, gamma, Contrast, Saturation, the red guard, once a camera frame), which
feed_fb takes back to screen. still is where feed_fb starts. Out: isp -> bus (the bytes, the shorts, the
slips and sync) -> dct (the JPEG's blocks, quantized, and the block errors) -> idct (the decoder) -> out
(scaled up, Mirror, the red guard). Input 2 goes through audio (lib audio_in). counts and steps turn its
counts into steps, and steady counts the time for Steady. beat_on, bar_on, steady_on and drop_on pick the
bursts Bursts and Song Moments ask for. flash_limit and flash gate them, flash_budget spaces them, burst
holds each one for Length, burst_count numbers them (each burst's seed) and drop_kind marks a drop's.
beat_pulse, beat_env and beat_n turn beats (or steady ticks, steady_tick) into the crackle, the sliver
and the new places of the slips and block errors.

CREDITS
- The idea: dusty_whale's post "Circuit bent feedback loop - The fractal microscope" on r/vjing
  (https://www.reddit.com/r/vjing/comments/1x9wez8/circuit_bent_feedback_loop_the_fractal_microscope/),
  a circuit-bent laptop webcam on a microscope mount filming a 7-inch screen showing its own picture,
  tiled into a kaleidoscope.
- Circuit bending: Reed Ghazala's name and practice for shorting the circuits of cheap electronics.
- Video feedback as a camera filming its own screen, with zoom, rotation and gain: J. P. Crutchfield,
  "Space-time dynamics in video feedback", Physica D 10 (1984).
- The bytes: YUYV (YUY2) 4:2:2 order as USB webcams send it; ITU-R BT.601's YCbCr matrix and 8-bit ranges.
- The Bayer color filter mosaic (B. E. Bayer, US patent 3,971,065, 1976) and bilinear demosaicing.
- The JPEG: ITU-T T.81 (1992), its DCT and its Annex K quantization tables, scaled by quality as the
  Independent JPEG Group's libjpeg does; restart markers; DC coded as the change from the block before.
- Dice: Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
- Seen during the survey, not used: elekktronaut's Circuit Bending tutorial, aaronmylespereira's
  circuitBending_MYLES.tox, the Palette's feedback component and TouchDesigner's Mirror TOP.
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness; the beat
  clock takes its tempo from the gaps between kicks, each voting for the beat lengths it is a whole
  multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of
  Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (the shaders, the faults' models, the moire from the screen's stripes, the bursts, the red
guard from VHS + CRT) is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new bent_cam.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox
at a downloaded copy). The version and the build it was saved in are on the About page.
