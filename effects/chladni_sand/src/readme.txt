Chladni Sand {v}: the picture's light moved like sand on a vibrating plate, piling on the lines of a figure the music sets and settling back between beats.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/chladni_sand.md

In 1787 Ernst Chladni strewed sand on a metal plate and drew a violin bow along its edge. The plate sang, and the sand jumped away from the parts that shook and gathered on the lines that kept still, drawing a figure of curves, stars and rings. Each note drew another figure. They are called Chladni figures.

This effect makes the picture the sand. Each of the music's seven bands sets one of the plate's figures, the lowest the simplest, and the bands rising most shape it. Each beat strikes the plate, and the picture's light slides toward the figure's lines and piles up there in the picture's own colors, while the parts between empty out. Then it settles back to the picture until the next beat.

USE
Drag chladni_sand.tox into your network. It shows TouchDesigner's sample movie of mist over a lake, struck every 2 seconds in turn by each of the plate's seven figures (Idle Strike). Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the beats strike the plate. You can also wire a depth map or mask into input 3. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Speed is how fast the sand travels toward the lines. Settle is how long the picture takes to come back after the sand moves, so short lets the figure form on each strike and clear between, and long keeps it hanging. Strike is how hard each beat strikes the plate, and Swell how much the bands rising above their usual level shake it between beats. Idle Strike strikes the plate every 2 seconds while nothing is on input 2. Depth Focus, Depth Type and Max Distance are for input 3, and Flashing says how often the plate may be struck.

AUDIO (input 2)
The plate's figure comes from the music's seven bands, Fosfora's split, from the sub bass (20 to 60 Hz) through bass, low mid, mid, upper mid and presence to the brilliance (above 6000 Hz). Each band is judged against its usual level over the last 4 seconds, so the bands rising most shape the figure, and it turns as the music does. Each beat strikes the plate as often as Flashing allows. Raw audio (Audio File In, Audio Device In) gives the bands and beats from the sound itself. Fosfora's signal gives them from its feature bus. Run `fosfora --signal --feat-bus`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too. Without Fosfora's feature bus, its bass, melody and drums stand in for the bands.

DEPTH OR MASK (input 3, optional)
With a depth map on input 3, Depth Focus keeps the sand moving on near things, so a person in front turns to sand while the room behind stays still. With a mask (white inside), only what lies inside it moves. Depth Type reads depth cameras too. The RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3 the whole picture is sand.

FLASHING
Each strike moves the picture's light into the figure and out again, which counts as flashing, so a beat strikes the plate only through a gate that follows the Flashing parameter. Off never strikes, so only Swell moves the sand, smoothly. Calm (the default) strikes at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
The plate is worked out at a quarter of the picture's size, and the sand at full size: about {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
plate works out the plate's figure from figure's seven weights, at a quarter size: the flow that carries sand toward the lines and where it gathers. sand carries the picture's light along that flow, its colors and its mass, and lets both settle back to the live picture; sand_fb is its last frame. show lights the sand by its mass, brighter where it piled up. Input 2 goes through audio (lib audio_in): bands, bands_now and bands_usual are the seven bands, smoothed over a second and their usual level over 4 seconds; counts and steps notice a beat, idle_count and idle_steps make Idle Strike's strikes, strike_ask takes either, flash_limit and flash let a strike through as often as Flashing allows, and strike_env rings it down. figure holds each mode's weight and how hard the plate shakes. Input 3 goes through depth and near (lib depth_near).

CREDITS
- The figures: E. F. F. Chladni, Entdeckungen ueber die Theorie des Klanges (Leipzig, 1787), the sand on a bowed plate.
- The figures as simple modes summed: C. Wheatstone, "On the Figures Obtained by Strewing Sand on Vibrating Surfaces, Commonly Called Acoustic Figures" (Phil. Trans. R. Soc. 123, 1833), whose two perpendicular modes in opposite phase give the square plate's figures, cos(n pi x) cos(m pi y) - cos(m pi x) cos(n pi y).
- Carrying the light along the flow: J. Stam, "Stable Fluids" (SIGGRAPH 1999), the semi-Lagrangian step Fluid uses too.
- The seven bands: Fosfora's split (its AUDIO-FEATURES.md), measured from raw audio by the library's audio input.
- The same figures before this one: Derivative's community tutorial "Audioreactive particles with Chladni Cymatics" (https://derivative.ca/community-post/tutorial/audioreactive-particles-chladni-cymatics/67877), which draws particles into the figures; this effect moves the picture instead and was written from Chladni's and Wheatstone's descriptions.
- Depth Type: the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth reading (lib depth_near) is shared with Detail, Fluid, Motion Magnify, Paint, Particles, Pencil, Point Cloud and Video Vocoder.
Everything else is written for this library: the sand as the picture's light with its mass kept, the bands judged against their usual level as the plate's modes, the strikes through the flash gate and Idle Strike. MIT.

EXPERIMENTAL
The bands Fosfora's bass, melody and drums stand in for, without its feature bus, are a rough guess.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new chladni_sand.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
