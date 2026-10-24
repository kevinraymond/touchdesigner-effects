Particles {v}: particles peel off the subject. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/particles.md

Particles come off a subject in the picture, a person usually, like smoke or sparks, each in the
picture's color where it was born. The air carries them up and swirls them around, and they fade
over a few seconds. The music moves the whole cloud: loudness thickens the stream, each beat fires a
burst and kicks the cloud outward, each bar swings the wind; with Fosfora's signal, a build stirs the
air up and a drop sends a shockwave out from the subject.

USE
Drag particles.tox into your network: it shows TouchDesigner's sample movie (a birch among dark
leaves), particles peeling off the trunk. Wire your picture into input 1 (a webcam, a video); the
result is on output 1, at the input's size. Optionally wire audio or beat channels into input 2
(below). Open Window shows it full size; Esc closes the window.

WHAT YOU HAVE, WHAT YOU GET
Find on Auto picks for itself; set Show to Subject to see what the particles come from and a label
saying how it was found.
- A depth map on input 3 (Kinect, RealSense, Depth Anything), lined up with input 1, Depth Type set
  to match: the best result. What stands in front of what is beside it emits, still or moving, in any light.
- A mask on input 3 (MediaPipe, the NVIDIA Background TOP): what is inside it emits.
- Only a picture (a webcam, a video): what moves emits. Someone who holds still fades out within a
  couple of seconds; moving shadows count too.
- Only a picture from a fixed camera: set Find to Background and, with the frame empty, press Capture
  Background; then everything that isn't the empty room emits, still or moving.
- A lit performer on a dark stage: Find on Stand Out reads the picture's brightness as depth.
Auto goes by what input 3 carries: a depth input that goes black falls back to Movement on its own.

FIND
Stand Out: nearer than Far Limit and, by Stand Out, than what lies to its left and right in the same
row; floors and walls drop out, while someone cut off by the left or right edge of the frame drops
out too and feet merge with the floor. Nearer Than Far Limit: everything nearer, for a mask or a
camera that sees no floor (at a desk, close up: set Far Limit just behind you). Depth Type: Brighter
Is Nearer for depth estimators and masks; Distance 0-1 for the RealSense and Kinect TOPs and Distance
in Meters (Max Distance) for the Kinect Azure TOP, whose black (no reading) is then left out; don't
invert a camera's depth yourself. Movement: what differs from a background that follows the scene a
couple of seconds behind (Sensitivity); edges and patterns count more than flat colors, and the camera
must stay still. Background: what differs from the empty room kept by Capture Background
(Sensitivity), by hue and by brightness allowing for the camera's own exposure drift; until it is
pressed, what moves.

THE PAGE
Show. Find, Capture Background, Sensitivity, Stand Out, Far Limit, Depth Type, Max Distance (above). Emit From: the
whole subject or its outline. Rate: particles born per second (at most {n:,} alive at once). Life:
seconds each lives. Size, in pixels at 720 high. Speed: how fast they leave the subject. Drift: how
fast the air rises (below 0, falls). Turbulence: how much it swirls. Color: the picture's (lifted, so
dark clothes still glow), orange, blue or white. Glow. Backdrop: how bright the picture behind is.
Loudness: how much input 2's loudness thickens and thins the stream. Beat Bursts: a burst and an
outward kick on each beat. Bar Gusts: the wind swings on each bar. Song Moments.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it
into input 2. Loudness thickens and thins the stream; each beat fires a burst of particles that leave
faster than the rest and kicks the whole cloud outward (Beat Bursts); each bar swings the wind (Bar
Gusts); with Song Moments on, a build makes the air swirl harder as it rises and a drop sends a ring
outward from the subject that shoves the particles it passes (Fosfora's drop detection is
experimental). Raw audio (Audio File In, Audio Device In) gives beats from a simple kick detector
(experimental: it can add or miss beats) and a bar every 4 beats; TouchDesigner's audioAnalysis gives
beats from its kick or onset channels. Nothing wired: a steady stream, no bursts.

INSIDE
The subject: depth (input 3, or input 1's brightness) -> near (small, brighter nearer; depth_stats:
is there any?) -> find (Stand Out, Nearer Than); source -> small -> motion (what moves) and plate (the
empty room, at each Capture Background: capture_exec counts presses in captures); subject picks by
Find -> emit (where particles are born; emit_stats averages it) and subject_blur (which way is out).
The particles: sim moves {n:,} of them, one per pixel of three float buffers (sim, sim_life,
sim_color), which it reads back through sim_fb, sim_life_fb and sim_color_fb; alive_stats counts the
living, so births come to Rate. Drawing: geo puts a dot (dot, dot_mat) at every particle by
instancing from the buffers, cam looks at them flat, render draws them, glow blurs them and look lays
both over the picture, or shows the subject with its label. Input 2 goes through audio (lib
audio_in); counts and steps turn its counts into steps, beat_env is a beat's burst and kick, drop_env
a drop's shockwave, build_lag the build, level_lag the loudness, gust and gust_lag the wind's angle
for each bar.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new particles.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External
.tox at a downloaded copy). The version and the build it was saved in are on the About page.
