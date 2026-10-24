Depth Particles {v}: particles peel off the people. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/depth_particles.md

A depth map is a picture of how far away things are: brighter is nearer. Depth cameras (Kinect,
RealSense) make one live, and depth estimators (Depth Anything) make one from any video.

This effect finds the people in a depth map (or a mask) and sends particles off them like smoke,
each in the picture's color where it was born. The air carries them up and swirls them around, and
they fade over a few seconds. The music moves the whole cloud: loudness thickens the stream, each
beat fires a burst and kicks the cloud outward, each bar swings the wind; with Fosfora's signal, a
build stirs the air up and a drop sends a shockwave out from the people.

USE
Drag depth_particles.tox into your network: it shows TouchDesigner's sample movie (a birch among
dark leaves), with the trunk's brightness standing in for depth. Wire the picture into input 1 and
its depth map or a mask into input 3 (grayscale, brighter nearer or inside, lined up with input 1);
the result is on output 1, at the input's size. With nothing on input 3, input 1's brightness stands
in for depth: bright things standing out from what is beside them emit. Optionally wire audio or beat
channels into input 2 (below). Open Window shows it full size; Esc closes the window.

FINDING THE PEOPLE
Set Show to People to see what the effect takes for the people (orange) and the depth beside them
(blue). Find on Stand Out counts what is nearer than Far Limit and nearer, by Stand Out, than what
lies to its left and right in the same row. Floors and walls drop out that way, since a floor is about
as near all along a row and a wall gets steadily nearer or farther along one, while a person has the
background on both sides. Two limits: someone cut off by the left or right edge of the frame drops
out, and feet merge with the floor they stand on. Find on Nearer Than Far Limit counts everything
nearer, for a mask or a depth camera that sees no floor. Raise Far Limit to drop the background,
lower it if parts of people go missing. Polarity: Brighter Is Nearer for depth estimators, a Kinect
or a mask; Darker Is Nearer for the RealSense TOP, whose black (no reading) is then left out.

THE PAGE
Show. Find, Stand Out, Far Limit, Polarity (above). Emit From: the whole body or its outline. Rate:
particles born per second (at most {n:,} alive at once). Life: seconds each lives. Size, in pixels at
720 high. Speed: how fast they leave the body. Drift: how fast the air rises (below 0, falls).
Turbulence: how much it swirls. Color: the picture's (lifted, so dark clothes still glow), orange,
blue or white. Glow. Backdrop: how bright the picture behind is. Loudness: how much input 2's
loudness thickens and thins the stream. Beat Bursts: a burst and an outward kick on each beat. Bar
Gusts: the wind swings on each bar. Song Moments.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it
into input 2. Loudness thickens and thins the stream; each beat fires a burst of particles that leave
faster than the rest and kicks the whole cloud outward (Beat Bursts); each bar swings the wind (Bar
Gusts); with Song Moments on, a build makes the air swirl harder as it rises and a drop sends a ring
outward from the people that shoves the particles it passes (Fosfora's drop detection is
experimental). Raw audio (Audio File In, Audio Device In) gives beats from a simple kick detector
(experimental: it can add or miss beats) and a bar every 4 beats; TouchDesigner's audioAnalysis gives
beats from its kick or onset channels. Nothing wired: a steady stream, no bursts.

INSIDE
The people: depth (input 3, or input 1's brightness) -> near (small, brighter nearer) -> find (the
people) -> emit (where particles are born; emit_stats averages it) and people_blur (which way is out).
The particles: sim moves {n:,} of them, one per pixel of three float buffers (sim, sim_life,
sim_color), which it reads back through sim_fb, sim_life_fb and sim_color_fb; alive_stats counts the
living, so births come to Rate. Drawing: geo puts a dot (dot, dot_mat) at every particle by
instancing from the buffers, cam looks at them flat, render draws them, glow blurs them and look lays
both over the picture. Input 2 goes through audio (lib audio_in); counts and steps turn its counts into
steps, beat_env is a beat's burst and kick, drop_env a drop's shockwave, build_lag the build,
level_lag the loudness, gust and gust_lag the wind's angle for each bar.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new depth_particles.tox
from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's
External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
