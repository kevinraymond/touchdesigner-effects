Lens Flare {v}: the picture's bright lights throw the ghosts a real lens would, worked out from the lens's design.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/lens_flare.md

A lens flare is light that went where it shouldn't inside a camera lens. Each glass surface reflects a little of the light, so some of it bounces off one surface, back off another, and reaches the sensor as a ghost: a faint copy of the iris's shape, on the line from the light through the middle of the picture, tinted by the lens's coating. Bright lights also draw a starburst, spikes that come from light bending around the iris's blades.

Most flare effects paint made-up ghosts along that line. This one works them out from real lenses, the way Lee and Eisemann described in 2013. Every ghost of a lens is a pair of surfaces the light bounced between, and simple optics gives where it lands, how big it is, where the lens's front element cuts it off and what color the coatings leave it. The effect finds the brightest lights in the picture and draws every ghost of every light, so they move as the lights move, grow as the lights grow and swing across the middle as a light crosses it.

USE
Drag lens_flare.tox into your network. It shows TouchDesigner's sample movie of a tree with the sun behind its branches, and the sun's flare. Wire a TOP with bright lights in it (stage lights, headlights, the sun, lanterns) into input 1. The result is on output 1 at the input's size. A picture with no light near white gets no flare: lower Threshold for one whose highlights aren't clipped. Wire music into input 2 (below) and the flare flares up on the beats. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Lens picks the lens the flare comes from. Coating picks how its glass was coated, which colors the ghosts. Aperture is the f-number: stopped down the ghosts are small and crisp, wide open they spread into veils. Blades, Roundness and Blade Angle shape the iris, which the ghosts and the starburst take after. Amount and Starburst set how strong the ghosts and the starbursts are, and Starburst Size how big. Threshold is how bright a part of the picture must be to count as a light, and Lights how many of the brightest may flare at once. Show gives the picture with its flare, or the flare alone. Beat Kick and Swell are for input 2, and Flashing says how often the beat may flare it up.

AUDIO (input 2)
On each beat the flare flares up and settles, as often as Flashing allows. Beat Kick sets how much. Swell strengthens the flare as the music gets louder than it has been, following the loudness over a second. Raw audio (Audio File In, Audio Device In) gives the beats and loudness from the sound itself. Fosfora's signal gives them too. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too.

FLASHING
The flare flaring up on a beat changes large parts of the picture at once, which counts as flashing, so a beat does it only through a gate that follows the Flashing parameter. Off never flares it up. Calm (the default) does at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. A flare puts big ghosts far from their light, so a light that flickers or bobs (a lantern carried by someone walking) would sweep them back and forth over large areas. The lights are eased over a fifth of a second and the flare over a tenth, so the ghosts follow smoothly, trailing a little behind a light that moves fast. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
bright finds each pixel's light past Threshold at a quarter size, and tiles sums it in tiles of 32 x 32 pixels (tiles_fb is last frame's). lights, a compute shader, gathers the brightest tiles into lights. The lens lane holds each lens's ghosts in a table (lens_heliar and the rest), worked out when the effect was built; ghost_table picks one and ghost_chop and ghost_tex turn it into a texture. The starburst lane draws the iris (aperture), takes its Fourier transform (dft_rows, dft) and sums it over the spectrum (burst). ghost_geo has a square for every ghost of every light, and ghost_mat's shaders place, size and color each one; burst_geo and burst_mat do the same for the starbursts. render adds them all up, and look adds that to the picture. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, flash_limit and flash let it through as often as Flashing allows, and kick holds the flare up. level, level_now and level_usual are the loudness, over a second and its usual level over 4 seconds.

CREDITS
- The method: S. Lee and E. Eisemann, "Practical Real-Time Lens-Flare Rendering" (EGSR 2013, Computer Graphics Forum 32(4)), https://cg.skku.edu/pub/papers/2013-lee-egsr-matrixflare-cam.pdf: paraxial ray transfer matrices for each two-reflection ghost, split at the iris, the ghost as the iris's shape cut by the entrance pupil, a color channel each (650, 510 and 475 nm), brightness from the area ratio.
- Anti-reflection coatings as thin films and the starburst as the iris's far-field diffraction summed over wavelengths, with dust on the iris: M. Hullin, E. Eisemann, H.-P. Seidel and S. Lee, "Physically-Based Real-Time Lens Flare Rendering" (SIGGRAPH 2011, ACM TOG 30(4)).
- The lenses, from expired patents as transcribed in Nathan Hagen's LensLibrary (https://github.com/nzhagen/LensLibrary, MIT, Copyright (c) 2021 Nathan Hagen): A. W. Tronnier, US 2,645,156 (1953, the Heliar, the paper's lens); L. Bertele, US 1,975,678 (1934, the Sonnar); R. Richter, US 1,792,917 (1931, the Topogon); K. Isono, US 6,744,570 (2004, a phone camera lens).
- Thin films: H. A. Macleod, "Thin-Film Optical Filters" (characteristic matrices); the quarter-half-quarter broadband coating after A. Thelen and others.
- Glass dispersion from each glass's Abbe number (E. Abbe), with A.-L. Cauchy's two-term formula.
- Color: the CIE 1931 color matching functions, by C. Wyman, P.-P. Sloan and P. Shirley's analytic fit ("Simple Analytic Approximations to the CIE XYZ Color Matching Functions", JCGT 2(2), 2013), into sRGB (IEC 61966-2-1).
- The parallel reduction in lights: W. D. Hillis and G. L. Steele, "Data parallel algorithms" (CACM 29(12), 1986).
- Not used: a look-up table of ghost shapes precomputed over the light's angle and blended with the linear ghosts (the paper's Section 5 experiment, which it leaves out), claimed by Sungkyunkwan University's US 10,074,195. The paper's linear method was Sungkyunkwan's US 9,595,132, which has expired.
Everything else is written for this library: finding the lights by tiles gathered around the brightest, each with its spread; a ghost blurred by its light's size and turning into a blob when that is wider than itself; each coating normalized to the same total; the iris's Fourier transform done as two plain sums on the GPU; the flare up on the beat through the flash gate; the swell with the loudness. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new lens_flare.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
