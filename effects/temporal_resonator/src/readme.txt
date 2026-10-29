Temporal Resonator {v}: every pixel a plucked string tuned to the beat, so whatever moves comes round again on the next beats, fainter and softer each time.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/temporal_resonator.md

A plucked string rings because its vibration runs back and forth along it and returns once every period, a little weaker and a little smoother each time, since the string loses its high harmonics first. In 1983 Kevin Karplus and Alex Strong found that a computer could do the same with a delay line one period long. Whatever goes in comes out again a period later, is averaged with its neighbor and is fed back in, and the result sounds like a plucked string. David Jaffe and Julius Smith extended it the same year, tuning the loop finely and controlling how fast it decays.

This effect gives every pixel such a string, one beat long. Whatever moves plucks the strings it moves across, and a beat later the movement comes round again, then again on the beat after, each echo fainter and softer than the last, so a dancer's gesture made on the beat repeats on the next beats like a ringing note. The echoes are added behind whatever stands out now, so the live picture stays in front of its own echoes. Someone who stays in one place for a while becomes part of the background, so a depth map or mask on input 3 keeps them in front anyway.

USE
Drag temporal_resonator.tox into your network. It shows TouchDesigner's sample movie of grass swaying in front of a building, plucked at 120 beats a minute (Tempo). Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the strings follow its tempo and are plucked on its beats. Wire a depth map or mask into input 3 (optional, brighter nearer or inside) and whatever stands in front in it stays in front of the echoes, even standing still. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Mode Same makes each echo like the moment it repeats. Alternating inverts the strings every trip round, as a pipe closed at one end reflects a wave, so a bright figure comes back as a shadow on the next beat and bright again on the one after. Length is how long the strings are, half a beat, a beat or two, which is how far apart the echoes come. Sustain is how many beats the echoes last until they fade to a tenth, Strength how bright they show, and Softness how much softer each one comes back, in time and across the picture. Threshold is how far a pixel must differ from the background to pluck its string and to stand in front of the echoes, so drifting smoke and noise stay out. Plucks On Beats plucks the strings on each beat, rising at once and falling to half by the next beat, so what moves on the beat rings loudest. Always plucks them evenly all the time. Tempo is the beat with nothing on input 2, and Loudness how much harder louder music plucks. Depth Type says what input 3 holds, and Max Distance how far a Kinect Azure's meters reach.

AUDIO (input 2)
The strings are as long as a beat of the music on input 2 and plucked on its beats. Beats slower than {lo:g} or faster than {hi:g} a minute count double or half. Raw audio (Audio File In, Audio Device In) gives the tempo from the beat clock the library's audio input locks to its kicks. Fosfora's signal gives it from its bpm. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too, the tempo timed from its beats. When the tempo changes the strings glide to their new length, so the echoes never jump in time.

FLASHING
Nothing here flashes on a beat, so there is no Flashing setting. The echoes replay the movement that plucked them, fainter and softer each time, and a pluck never falls below half between beats: falling to nothing, it made the echoes of a picture that moves all over pulse with the beat, and the whole picture flashed. An echo moving a red near WCAG's saturated-red line moves it across the line more often, so every pixel goes through the red guard, which keeps reds just short of it. The flashes a second were counted on the output (docs page, Accessibility).

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance). The strings are kept at half the picture's size in 16-bit float, one copy a frame: at 1280 x 720 and 60 frames a second, about {membeat} MB of GPU memory at Length 1 Beat, {memhalf} MB at 1/2 Beat and {memtwo} MB at 2 Beats.

INSIDE
string is the strings: each pixel's pluck (how far the picture differs from background, times pluck) plus what comes back round the delay line, averaged over three moments around a beat back and a little of the picture around it, times the loop's gain. Its buffer 0, the strings' state, goes through state and string_fb into states, the delay line, a Texture 3D TOP that keeps one slot a cook. Its buffer 1, the echo and what stands out now, goes through echo to show, which adds the echoes behind the live picture. background is the picture's running median, what isn't moving (background_fb its last frame). stamp marks every cook (which, when, and whether the strings start again: the first cook, after a pause, or at a cut found by the input's clock, lib optical_flow), and stamps keeps those beside states, so taps can find which slots lie a beat back. Input 3 goes through depth (lib depth_in, else no_depth, which finds nothing), near (its nearness at an eighth size, lib depth_near) and find (what stands in front of its surroundings, lib depth_find), which string counts as standing out now. Input 2 goes through audio (lib audio_in): beat is the beat's length, delay_to and delay the strings' length gliding to it, phase where in the beat it is, level_pick and level_smooth the loudness, and pluck how hard the strings are plucked now.

CREDITS
- K. Karplus and A. Strong, "Digital Synthesis of Plucked-String and Drum Timbres" (Computer Music Journal 7(2), 1983): the delay line one period long, averaged and fed back. Its patent, US 4,649,783, expired.
- D. A. Jaffe and J. O. Smith, "Extensions of the Karplus-Strong Plucked-String Algorithm" (Computer Music Journal 7(2), 1983): the loop's delay tuned between samples and its decay set apart from its length, as Length and Sustain are here.
- The approximate median background: N. J. B. McFarlane and C. P. Schofield, "Segmentation and tracking of piglets in images" (Machine Vision and Applications 8(3), 1995).
- A negative loop gain, which makes a closed pipe of the string, is a standard variation of Karplus-Strong (Jaffe and Smith; J. O. Smith, Physical Audio Signal Processing, https://ccrma.stanford.edu/~jos/pasp/).
- What stands in front in the depth (lib depth_near.glsl and depth_find.glsl) is shared with Particles, Fluid, Point Cloud, Reaction-Diffusion and Words.
- The red guard (lib red_guard.glsl) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan Processor and Voxel Space.
- Not used: Schroeder's allpass filters over the frame history, a phaser for the picture; a negative gain gives echoes that alternate in sign more simply.
Everything else is written for this library: the strings as the picture's difference from its background, plucked on the beat and tuned to the tempo, the echoes behind what stands out now, the delay line kept in a ring of stamped slots. MIT.

EXPERIMENTAL
The cut that starts the strings again is found from how much the picture changes at once, a guess that a very fast pan can fool.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new temporal_resonator.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
