Video Vocoder {v}: a channel vocoder with the picture as the carrier, its octaves of detail gained by the music's bands.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/video_vocoder.md

A vocoder splits a sound into bands of pitch, from the lowest to the highest, and lets each band of a second sound through only as loud as the first sound's matching band. That is how a synthesizer is made to talk.

This effect does it to a picture. It splits the picture into seven octaves of detail, from its largest shapes and soft light down to its finest grain, and makes each octave stronger or weaker with the matching band of the music: the bass pumps the big shapes and the glow, the mids sharpen the edges, and the treble sparkles the fine detail. Each band of the music is judged against its usual level over the last few seconds, so the picture keeps its look and the music's changes show in it: a quiet moment softens it to a haze, a loud one makes it crisp and vivid. A band jumps up at once as often as Flashing allows, and follows the music smoothly in between. With nothing on input 2, the seven sliders are an equalizer for the picture's detail.

USE
Drag video_vocoder.tox into your network. It shows TouchDesigner's sample movie of a river running over rocks, a slow wave moving through its octaves of detail (Idle Sweep). Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the picture follows its bands. You can also wire a depth map or mask into input 3. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Brilliance, Presence, Upper Mid, Mid, Low Mid, Bass and Sub Bass are the picture's seven octaves, finest to largest, each named after the band of the music that drives it: 1 leaves an octave as it is, 0 takes it out (the picture goes soft, or flat), 3 makes it three times as strong. Above 1 the music swings an octave no further than at 1. Drive says how much the music moves them. Release is how long an octave takes to settle after the music makes it jump. Idle Sweep moves a slow wave through the octaves while nothing is on input 2. Depth Focus, Depth Type and Max Distance are for input 3, and Flashing says how often the music may make the octaves jump.

AUDIO (input 2)
Raw audio (Audio File In, Audio Device In) gives the bands directly, from the sound itself. Fosfora's signal gives them from its feature bus: run `fosfora --signal --feat-bus`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. Without the feature bus, Fosfora's bass, melody and drums stand in for the bands. TouchDesigner's audioAnalysis gives them from its low, mid and high levels. The bands are Fosfora's seven: sub bass (20 to 60 Hz), bass (to 250), low mid (to 500), mid (to 2000), upper mid (to 4000), presence (to 6000) and brilliance (above).

DEPTH OR MASK (input 3, optional)
With a depth map on input 3, Depth Focus keeps the music's changes to near things, so a person in front pumps with the music while the room behind keeps the sliders alone. With a mask (white inside), what lies outside it keeps the sliders alone. Depth Type reads depth cameras too. The RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3 the music moves the whole picture.

FLASHING
Pumping the octaves at every hit counts as flashing: on every eighth note at a dance tempo it flashed red flowers 4 times a second. So a band jumps up at once only through a gate that follows the Flashing parameter, all seven bands together, and settles back over Release. In between it follows the music smoothed over a second, too smoothly to flash: rising slowly but falling fast, it rippled at every hit, enough to flip reds near WCAG's red line. Off never jumps, so the music moves the octaves only smoothly. Calm (the default) jumps at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. Above 1, a slider doesn't widen the music's swing. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
Each level of the pyramid is a quarter of the size of the one above, so all seven together cost about a third of one full-size pass, and only the last pass runs at full size: about 0.9 ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance). Raw audio on input 2 costs a little CPU for measuring its bands.

INSIDE
g1 to g7 (lib pyramid) halve the picture again and again, smoothing it first each time: the picture at every octave of size. collapse6 to collapse0 run from the smallest octave to the largest: each takes its level minus the next smaller one, the octave's detail, gains it by its slider and the music's band, and adds back the octaves below, so collapse0 is the picture. Input 2 goes through audio (lib audio_in): bands picks its seven bands, rises and ask notice a band jumping, flash_limit and flash let a jump through as often as Flashing allows, and open stays open a tenth of a second for it. bands_jump lets each band jump up while open and fall over Release, bands_steady smooths it over a second, bands_now takes the higher of the two, and bands_usual is each band's usual level over the last 4 seconds. Input 3 goes through depth and near (lib depth_near).

CREDITS
- The channel vocoder: H. Dudley, "Remaking Speech" (J. Acoustical Society of America 11, 1939), and his vocoder (Bell Labs, 1939). Here the picture is the carrier and the music the modulator.
- The octaves of detail: P. J. Burt and E. H. Adelson, "The Laplacian Pyramid as a Compact Image Code" (IEEE Trans. Communications 31(4), 1983), the library's pyramid (lib pyramid_down.glsl and pyramid.glsl). Its expand reads the next level by the cubic B-spline in four bilinear reads, after C. Sigg and M. Hadwiger, "Fast Third-Order Texture Filtering" (GPU Gems 2, 2005).
- The same idea before this one: stoatworks-labs/vocoder (https://github.com/stoatworks-labs/vocoder, MIT, 2026), a channel vocoder with the picture as the carrier for Resolume. This effect was written from Dudley's and Burt and Adelson's descriptions, not from its code.
- The seven bands: Fosfora's split (its AUDIO-FEATURES.md), measured from raw audio by the library's audio input.
- Depth Type: the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth reading (lib depth_near) is shared with Fluid, Motion Magnify, Paint, Particles, Pencil and Point Cloud.
Everything else is written for this library: judging each band against its usual level, the jumps through the flash gate, Idle Sweep and the depth focus. MIT.

EXPERIMENTAL
The bands Fosfora's bass, melody and drums stand in for, without its feature bus, are a rough guess.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new video_vocoder.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
