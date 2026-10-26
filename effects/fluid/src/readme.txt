Fluid {v}: the picture pours ink, smoke or fire into a fluid that its own movement stirs.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/fluid.md

A fluid simulation runs over the picture. Where the picture moves (or is bright, or stands out in a depth map, or is inside a mask), it pours ink, smoke or heat into the fluid, and its movement drags the fluid along: wave a hand and the smoke swirls after it, spin and the flames whip round. The fluid keeps going on its own, curling into eddies, rising (smoke and flames) and fading. Music makes it leap and churn on the beats.

USE
Drag fluid.tox into your network: it shows TouchDesigner's sample movie (grass swaying in front of a building) with a soft white ball circling over it, trailing flames. Wire your picture into input 1 (a webcam, a video); the result is on output 1, at the input's size. Optionally wire audio or beat channels into input 2, and a depth map or mask into input 3 (below). Open Window shows it full size; Esc closes the window. Reset clears the fluid.

LOOK
- Fire (the default): flames that rise and flicker, orange through yellow to white as they get hotter, added onto the picture.
- Smoke: soft, see-through smoke that rises and thins out, lit from above.
- Ink: the picture's colors swirl and linger like ink dropped in water, sharp and opaque; they don't rise. Best on a light background.
Linger sets how long it lasts: at 0.5 each look's own (half gone after about {half[0]:g} s for Ink, {half[1]:g} s for Smoke, {half[2]:g} s for Fire), at 0 a quarter of that, at 1 four times. Rise adds to each look's own rise (Ink none, Smoke some, Fire a lot); below 0 it sinks.

EMIT FROM
- Movement: what moves pours in, so someone who holds still stops. Moving shadows count too, and the camera must stay still (a moving camera pours everywhere).
- Brightness: what is bright pours in, moving or not: a lit performer on a dark stage, a light beam.
- Depth (Input 3): what stands in front of what lies left and right of it in the depth map, as in Particles: floors and walls drop out, someone cut off by the left or right edge drops out too, and feet merge with the floor. Depth Type: Brighter Is Nearer for depth estimators (Depth Anything), Distance 0-1 for the RealSense and Kinect TOPs, Distance in Meters (Max Distance) for the Kinect Azure TOP; don't invert a camera's depth yourself. With nothing on input 3, the picture's brightness stands in (only what is brighter than half counts).
- Mask (Input 3): what is inside the mask (white inside: MediaPipe, the NVIDIA Background TOP). With Fire, a whole silhouette burns.
Sensitivity lowers the bar in each: slower movement, dimmer brightness, farther depth or a grayer mask counts as well.

THE PAGE
Look, Reset. Emit From, Sensitivity, Depth Type, Max Distance (above). Amount: how much pours in. Linger (above). Push: how strongly the picture's movement drags the fluid. Swirl: how much it curls into eddies. Rise (above). Color (Ink, Smoke): the picture's or one of orange, blue and white. Backdrop: how bright the picture behind is. Loudness, Beat Puffs, Song Moments (below). Flashing.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. Loudness thickens and thins the pour. As often as Flashing allows, a beat puffs (Beat Puffs): the fluid leaps up where it is thick and churns into more swirls, the pour flares, and the flames burn hotter (the smoke catches more light) for a moment. With Song Moments on, a build stirs the fluid into more and more swirls, and a drop sends a puff three times as strong lasting a second (Fosfora's drop detection is experimental). Raw audio (Audio File In, Audio Device In) gives beats from a kick detector and a beat clock that locks to the kicks' tempo (experimental: it can still add or miss beats); TouchDesigner's audioAnalysis gives beats from its kick or onset channels. Nothing wired: a steady pour, no puffs.

FLASHING
A beat's puff throws bright flames (or thick smoke) up at once and makes them flare, so it counts as a flash, and so does a drop's: both pass through one gate that follows the Flashing parameter. Off never puffs, Calm (the default) at most once a second (every second or third beat at dance tempos), Up to 3 per second is the WCAG 2.3.1 limit (every beat up to 180 BPM). The flames are never pure red (they start at orange), so their flicker never counts as a red flash. The limits were measured on the output (docs page, Accessibility).

INSIDE
The motion: lib optical_flow() makes lum8 and lum4 (the picture's luma at 1/8 and 1/4) and the previous input frame's (lum8p, lum4p), tells new input frames and cuts apart (change, change_avg, clock) and measures the optical flow (lk8, then lk4); pace says when the last new frame came and the gap between frames, and motion turns the flow into a speed at the fluid's grid (a quarter of the picture), held between the input's frames. Where it emits: emit, from motion, the picture or subject (input 3: depth -> near -> find for Depth, near alone for Mask; none of that cooks for Movement and Brightness). The fluid: advect carries the velocity along itself and adds vorticity confinement, the rise and the motion's drag; divergence measures what each cell gains or loses; pressure cancels it ({passes} Jacobi iterations in one GLSL TOP, its Passes); velocity is the result, read back next frame through velocity_fb. dye carries the ink, smoke or heat along the velocity at the picture's size and pours in where emit says (dye_fb reads it back); look draws it over the picture. Every Feedback TOP starts from still (nothing, at rest), and Reset pulses them back to it. Unwired, demo puts ball (a Circle TOP on a figure of eight) over the sample movie. Input 2 goes through audio (lib audio_in); counts and steps turn its counts into steps, ask names them puff and drop, flash_limit and flash let them through as often as Flashing allows, and puff_env and drop_env shape them; build_lag is the build, level_lag the loudness.

CREDITS
- Stable fluids: J. Stam, "Stable Fluids" (SIGGRAPH 1999): semi-Lagrangian advection and the pressure projection; on the GPU as M. Harris laid it out in "Fast Fluid Dynamics Simulation on the GPU" (GPU Gems, ch. 38, 2004): Jacobi iteration of the pressure, one pass per step.
- Vorticity confinement and buoyancy: R. Fedkiw, J. Stam and H. W. Jensen, "Visual Simulation of Smoke" (SIGGRAPH 2001).
- Smoke that absorbs light as it thickens: the Beer-Lambert law.
- The motion: this library's Lucas-Kanade optical flow (B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to Stereo Vision", 1981), shared with Datamosh.
- Ink kept sharp: a Catmull-Rom bicubic (Catmull and Rom, 1974), clamped to its neighbors, shared with Datamosh. The same shared helpers (lib common.glsl) carry Chris Wellons' lowbias32 integer hash (hash-prospector, public domain), which Fluid doesn't use.
- Fire's flicker: TouchDesigner's built-in simplex noise.
- Depth Type: the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth reading (lib depth_near and depth_find) is shared with Particles and Point Cloud.
- Read during the survey, not used: touchFluid (kamindustries, MIT), the community "Fluid Simulation in TOPs" (none stated), NVIDIA Flow (Windows and NVIDIA only).
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness; the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (the motion held between the input's frames and its drag on the fluid, the looks, the beat's leap, churn and glow) is written for this library. MIT.

EXPERIMENTAL
  Cuts in the input are found by a heuristic shared with Datamosh (a change several times the usual
  one between frames); across a cut the motion is ignored for that frame, and a cut it misses gives
  one frame of meaningless push. Fosfora's drops and raw audio's beats are experimental (AUDIO).

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new fluid.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
