Pixel Art {v}: the picture as pixel art, each art pixel a region shaped around the picture's features, in a small palette it picks itself and keeps following.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/pixel_art.md

Pixel art is a picture drawn one pixel at a time in a few colors, as on old game consoles. Shrinking a photo and cutting its colors down gives something else: blurred edges, speckles, and grays where the picture had a skin tone. A pixel artist instead picks a few colors that matter and places each pixel so the shapes read.

This effect does that the way Gerstner and his colleagues described in 2012. Each pixel of the art covers a small region of the picture, and the regions bend around the picture's features, so an eye or the line of a mouth lands on whole art pixels instead of being smeared between two. The palette starts as one color, the picture's average, and splits into more as it settles, until it has as many as you ask for, which takes about half a second. Meanwhile the art shows the regions' own colors, then fades into the palette. On video it never stops: each frame carries on from the last, so the palette follows the picture's colors as they change.

USE
Drag pixel_art.tox into your network. It shows TouchDesigner's sample movie of mist over a lake as pixel art. Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the beats kick the art into bigger blocks. You can also wire a depth map or mask into input 3. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Pixel Size is how many of the picture's pixels across one art pixel is. Colors is how many colors the palette has. Dither mixes two colors in a checkerboard where an art pixel sits between them. Saturation is how colorful the palette is drawn. Hold Palette keeps the palette as it is, and New Palette starts it again from one color. Mosaic Kick and Swell are for input 2, Subject Colors, Depth Type and Max Distance for input 3, and Flashing says how often the beat may kick the art.

AUDIO (input 2)
On each beat the art jumps to bigger blocks for a moment and back, as the Super Nintendo's mosaic did, as often as Flashing allows. Mosaic Kick sets how big the blocks are. Swell dithers the art more as the music gets louder than it has been, following the loudness over a second, so loud passages get the checkerboards old consoles drew their in-between shades with. Raw audio (Audio File In, Audio Device In) gives the beats and loudness from the sound itself. Fosfora's signal gives them too. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too.

DEPTH OR MASK (input 3, optional)
With a depth map on input 3, Subject Colors spends more of the palette on near things, so a person in front gets their own skin and clothing tones while the room behind makes do with fewer. With a mask (white inside), what lies inside it counts most. Depth Type reads depth cameras too. The RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3 every part of the picture counts the same.

FLASHING
The mosaic changes the whole picture at once, which counts as flashing, so a beat kicks it only through a gate that follows the Flashing parameter. Off never kicks. Calm (the default) kicks at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. The art's own changes are held steady so they don't flicker. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
lab turns the picture into L*a*b* colors, with each pixel's importance from input 3. assign puts each pixel into one of the 9 superpixels around it, by color and place, and gather finds each superpixel's new center and color. centers pulls each center toward its neighbors, so the superpixels stay in rows and columns, and colors smooths their colors and eases them over time. The palette lane runs one step of the annealing a frame: assoc weighs each superpixel toward each palette entry, totals adds them up for each entry, and palette refines the colors, cools and splits them, then follows the picture. index picks each art pixel's color, and the next nearest for Dither (index_next), and show draws the art at full size. centers_fb, colors_fb, index_fb and palette_fb are last frame's. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, flash_limit and flash let it through as often as Flashing allows, and kick holds the mosaic. level, level_now and level_usual are the loudness, over a second and its usual level over 4 seconds. Input 3 goes through depth and near (lib depth_near). New Palette resets palette_fb (reset).

CREDITS
- The method: T. Gerstner, D. DeCarlo, M. Alexa, A. Finkelstein, Y. Gingold and A. Nealen, "Pixelated Image Abstraction" (NPAR 2012), https://gfx.cs.princeton.edu/pubs/Gerstner_2012_PIA/: superpixels on the art's grid by a modified SLIC whose color distance is to the palette, Laplacian smoothing of their centers, a bilateral filter on their colors, the palette by mass-constrained deterministic annealing, the saturation step, and the importance map.
- SLIC superpixels: R. Achanta, A. Shaji, K. Smith, A. Lucchi, P. Fua and S. Suesstrunk, "SLIC Superpixels" (EPFL technical report 149300, 2010; TPAMI 34(11), 2012).
- Mass-constrained deterministic annealing: K. Rose, "Deterministic annealing for clustering, compression, classification, regression, and related optimization problems" (Proc. IEEE 86(11), 1998), after K. Rose, E. Gurewitz and G. Fox (Physical Review Letters 65, 1990).
- The bilateral filter: C. Tomasi and R. Manduchi, "Bilateral Filtering for Gray and Color Images" (ICCV 1998).
- CIE L*a*b* (CIE 1976) from sRGB (IEC 61966-2-1) with the D65 white.
- Dither: B. E. Bayer, "An optimum method for two-level rendition of continuous-tone pictures" (IEEE ICC 1973), its 4 x 4 matrix.
- The mosaic: the Super Nintendo's mosaic effect (Nintendo, 1990), each block showing its top-left pixel.
- Depth Type: the RealSense, Kinect and Kinect Azure TOPs' depth, as their help pages describe it; the depth reading (lib depth_near) is shared with Chladni Sand, Detail, Fluid, Motion Magnify, Paint, Particles, Pencil, Point Cloud and Video Vocoder.
- Not used: optimizing the small picture against a perceptual similarity to the input (A. C. Oeztireli and M. Gross, "Perceptually Based Downscaling of Images", SIGGRAPH 2015), which ETH Zurich patented (US 10,325,346, active).
Everything else is written for this library: running the paper's loop one iteration a frame on video, carried from frame to frame; the temperature also falling after a moment at one temperature; showing the superpixels' own colors until the palette is whole, then fading to it; each superpixel's color eased only where it changed a little; a pixel keeping its color until another is clearly nearer; an unused color taking half of the most spread-out one; Dither between the two nearest colors; the mosaic on the beat through the flash gate; the swell of dither with the loudness. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new pixel_art.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
