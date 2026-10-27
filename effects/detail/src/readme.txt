Detail {v}: the picture's fine detail made stronger or smoothed away, its edges kept clean, by a local Laplacian filter.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/detail.md

Turning up a picture's local contrast gives a photo the crisp, hyperreal "HDR look", where every texture, wrinkle and wisp of smoke stands out. The usual way, sharpening or a high-pass, boosts the edges too, and leaves a bright or dark halo along every one of them. A local Laplacian filter tells detail from edges by how large a step in brightness is. Small steps are detail and change, and large ones are edges and stay put, so it boosts or smooths texture without halos.

This effect runs the fast form of the filter live. Detail makes the fine detail stronger, or below 0 smooths it away while the edges stay sharp, which turns a picture into something like clay or a painting. Tone flattens the picture's large changes of light (the shadows open, the highlights come down) or deepens them, while the detail stays. Edge Contrast says how large a step in brightness counts as an edge. The music on input 2 makes the detail jump on its beats and swell when it gets loud.

USE
Drag detail.tox into your network. It shows TouchDesigner's sample movie of a tree against the light, its detail made twice as strong. Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the detail follows it. You can also wire a depth map or mask into input 3. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Detail is how much stronger the fine detail gets. At 0 it stays as it is, 1 doubles it and 3 makes it four times as strong, while -1 smooths it away entirely and keeps the edges. Tone is how large the picture's big changes of light stay. At 1 they stay as they are, lower flattens them and higher deepens them. Edge Contrast is the step in brightness, from black (0) to white (1), past which a change counts as an edge and is kept. Higher lets Detail reach larger features, and lower keeps it to fine texture. Noise Floor leaves detail fainter than it nearly as it is while Detail boosts, so the video's noise and compression blocks don't grow with the detail. Beat Kick and Loudness are for input 2, Depth Focus, Depth Type and Max Distance for input 3, and Flashing says how often the beats may make the detail jump.

AUDIO (input 2)
Each beat makes the detail jump up and settle back over a third of a second, as often as Flashing allows. At Beat Kick 1, Detail is 2 higher for a moment. The detail also swells as the music gets louder than it has been over the last few seconds and eases back as it quietens (Loudness), smoothed over a second. Any of these works on input 2: Fosfora's signal (fosfora_signal.tox, from Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora), raw audio (Audio File In, Audio Device In), or TouchDesigner's audioAnalysis.

DEPTH OR MASK (input 3, optional)
With a depth map on input 3, Depth Focus keeps the change to near things, so a person in front turns crisp while the room behind stays as it was. With a mask (white inside), what lies outside it stays as it was. The two are blended octave by octave, so there is no seam. Depth Type reads depth cameras too. The RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3 the whole picture changes.

FLASHING
Making the detail jump on every beat counts as flashing, so a beat reaches it only through a gate that follows the Flashing parameter. Off never jumps, Calm (the default) jumps at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. Loudness changes the detail only smoothly. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
The filter works on eight copies of the picture's brightness, four to a texture, and on the octaves of each. Each octave is a quarter of the size of the one above, so a pyramid's seven octaves together are about a third the size of the picture. It costs about {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
luma is the picture's brightness, and l1 to l7 (lib pyramid) halve it again and again, smoothing it first each time. copies_a and copies_b remap the brightness around eight levels from black to white, four each, and a1 to a7 and b1 to b7 halve those. collapse6 to collapse0 run from the smallest octave to the largest: each takes its octave's detail from the two copies whose levels lie on either side of the brightness there, leaves it nearly as it was where it is fainter than Noise Floor, and adds back the octaves below; collapse0 adds the change in brightness to the picture's colors. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, flash_limit and flash let it through as often as Flashing allows, and kick_env is its jump; level_now is the loudness over a second and level_usual over the last 4 seconds; detail_now is Detail with the beat's jump and the swell added, which the copies and the collapse passes read. Input 3 goes through depth and near (lib depth_near).

CREDITS
- The filter: S. Paris, S. W. Hasinoff and J. Kautz, "Local Laplacian Filters: Edge-aware Image Processing with a Laplacian Pyramid" (ACM SIGGRAPH 2011, ACM Trans. Graphics 30(4)), with its curves for detail and tone, its brightness-only color handling, and its smooth step that keeps the smallest differences from being boosted, which Noise Floor carries over.
- Its fast form: M. Aubry, S. Paris, S. W. Hasinoff, J. Kautz and F. Durand, "Fast Local Laplacian Filters: Theory and Applications" (ACM Trans. Graphics 33(5), 2014): a few remapped copies, interpolated, and the smooth (Gaussian) remapping it samples closely.
- Noise Floor as coring: J. P. Rossi, "Digital Techniques for Reducing Television Noise" (SMPTE Journal 87(3), 1978), whose coring leaves a small coefficient, more likely noise than detail, nearly as it was.
- The octaves: P. J. Burt and E. H. Adelson, "The Laplacian Pyramid as a Compact Image Code" (IEEE Trans. Communications 31(4), 1983), the library's pyramid (lib pyramid_down.glsl and pyramid.glsl), and their multiresolution spline ("A Multiresolution Spline With Application to Image Mosaics", ACM Trans. Graphics 2(4), 1983) for Depth Focus's blend. The expand reads the next level by the cubic B-spline in four bilinear reads, after C. Sigg and M. Hadwiger, "Fast Third-Order Texture Filtering" (GPU Gems 2, 2005).
- Depth Type: the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth reading (lib depth_near) is shared with Fluid, Motion Magnify, Paint, Particles, Pencil, Point Cloud and Video Vocoder.
Everything else is written for this library: the eight copies packed four to a texture, Noise Floor as coring in the collapse, the beat's jump through the flash gate and the loudness against its usual level. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new detail.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
