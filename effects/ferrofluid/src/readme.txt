Ferrofluid {v}: a black glossy liquid over the live picture that bristles into spikes where the picture is bright or near, on the bass.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/ferrofluid.md

A ferrofluid is an oil full of tiny magnetic particles. Over a magnet it doesn't just cling: once the field is strong enough, its flat surface rises into a lattice of sharp spikes, all the same distance apart, packed in hexagons. The spikes stand up as the field passes a threshold and lie down again as it falls.

This effect pours that liquid over the live picture. Where the picture is bright, or what stands in front in the depth map is, the field is strong and the liquid bristles; elsewhere it lies flat and the picture shows through it. The bass sets how strong the field is, so the spikes rise and fall with the music. The liquid is a black mirror: it reflects the picture and a soft light hung above it, and the view leans a little, so each spike shows its side.

USE
Drag ferrofluid.tox into your network. It shows TouchDesigner's sample movie, and the liquid bristles over its bright parts within a second. Wire any TOP into input 1, and the result is on output 1 at the input's size. You can also wire audio or beat channels into input 2 and a depth map or mask into input 3 (below). Open Window shows the picture full size, and Esc closes the window. Reset lays the liquid flat, and the spikes grow back.

THE PAGE
Style picks Black (a black liquid that reflects the picture) or Tinted (the liquid takes the picture's colors). Spike Size sets how far apart the spikes are: Small, Medium or Large, each twice the last. Height says how tall they stand for their spacing, Tilt how far the view leans (at 0 it is straight on), and Picture how much of the picture shows through where the liquid lies flat (at 0 a black pool).

Strength says how strong the field is: below about 0.3 the liquid lies flat, and past 1 the spikes join into ridges, as a real ferrofluid's do in a strong field. By Brightness and By Nearness say how much the picture's bright parts and what stands out in front draw the spikes up. Magnet is a magnet under the liquid that draws spikes up wherever it is and wanders.

Input 3 Holds, Sensitivity, Depth Type and Max Distance read input 3. Bass and Beat Pulse are the music's.

AUDIO (input 2, optional)
Fosfora's signal is the best input. Run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. The bass sets the field's strength (Bass): at 1 silence lays the liquid flat and every bass note raises the spikes, which rise in a twentieth of a second and fall back over a third. Each beat makes them jump up at once, as often as Flashing allows (Beat Pulse). Each bar moves the magnet a step along its path, at most once every 2 seconds. Raw audio (Audio File In, Audio Device In) gives the bass from its own low band and beats from a kick detector and a beat clock that locks to the kicks' tempo. That clock is experimental and can still add or miss beats. TouchDesigner's audioAnalysis gives beats from its kick or onset channels. With nothing wired, the field holds steady and the magnet drifts on its own.

DEPTH OR MASK (input 3, optional)
A depth map, brighter nearer, says what stands in front of its surroundings: that draws the spikes up, so a person bristles. Floors and walls don't count as standing out, someone cut off by the left or right edge of the frame drops out, and feet merge with the floor they stand on. With Input 3 Holds on Mask, what is inside the mask (white inside: MediaPipe, the NVIDIA Background TOP) does instead. Sensitivity says how easily something counts as standing out, or how gray a mask counts as inside. Depth Type reads depth cameras too: the RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. A spike needs about its own spacing of room, so thin arms and fingers don't bristle. With nothing on input 3, the picture's brightness alone draws the spikes up.

FLASHING
A beat's jump changes a wide area at once, so it goes through the Flashing setting: Off never jumps, Calm (the default) at most once a second, Up to 3 per second at most three times. Every pixel goes through a red guard. The flashes were measured on the output under a beat far busier than music, both styles and five clips: none added to the clip's own, and none flashed red (docs page, Accessibility).

PERFORMANCE
Ferrofluid costs about 3 ms a frame on the GPU and 0.5 ms on the CPU at 1280 x 720 on an M2 Pro. The spikes' 20 steps a frame cost the most, about 1.4 ms, then the look (0.8 ms) and the cones (0.55 ms). Spike Size Small grows the spikes on a grid four times as large and costs about 4.4 ms.

INSIDE
Input 3 goes through depth, near (nearness at a quarter size) and find (what stands out, or the mask), lib depth_near and depth_find. drive works out the field at the spikes' grid (half, a quarter or an eighth of the picture's size, by Spike Size): strong where the picture is bright, what stands out and the magnet are, as strong as Strength and the bass say. seed takes the height last frame (height_fb) and adds a trace of noise, and field steps the Swift-Hohenberg equation 20 times a frame at 60 fps, so spikes rise where the field passes the threshold. shape finds each spike's peak, and surface shapes the spikes into cones at the picture's size. look draws the liquid: it marches each pixel's ray down the leaning view to the surface, then mirrors the picture and a soft light in it and shows the picture through it where it lies flat. clear is the nothing the height starts from, and Reset sends it back. Input 2 goes through audio (lib audio_in): counts and steps turn its counts into steps, ask, flash_limit and flash let beats through as often as Flashing allows, beat_env shapes a beat's jump, bar_gap, bars and magnet_lag count the bars (at most one every 2 seconds) and ease the magnet's steps, and bass_lag eases the bass.

CREDITS
- The phenomenon: M. D. Cowley and R. E. Rosensweig, "The interfacial stability of a ferromagnetic fluid" (J. Fluid Mech. 30, 1967): a magnetic fluid's flat surface turns unstable past a critical field and rises in a hexagonal lattice of spikes with a set spacing. A. Gollwitzer, I. Rehberg and R. Richter, "Via hexagons to squares in ferrofluids" (J. Phys.: Condens. Matter 18, 2006): the hexagons measured from the flat surface on, and their turn to squares at higher fields, which this effect doesn't reach (its equation turns from hexagons to ridges).
- The spikes' growth: J. Swift and P. C. Hohenberg, "Hydrodynamic fluctuations at the convective instability" (Phys. Rev. A 15, 1977), the equation physicists use for such patterns, with a quadratic term for hexagons; the isotropic 9-point Laplacian of Y. Oono and S. Puri, "Study of phase-separation dynamics by use of cell dynamical systems" (Phys. Rev. A 38, 1988). Using it for a ferrofluid's surface on a picture, at a frame's pace, is this library's design: no published real-time method was found.
- The view: steep parallax mapping (T. Kaneko et al., "Detailed shape representation with parallax mapping", ICAT 2001; M. McGuire and M. McGuire, "Steep Parallax Mapping", I3D 2005), the reflection by C. Schlick's approximation of Fresnel's equations (Computer Graphics Forum 13(3), 1994), the highlight Blinn-Phong (J. F. Blinn, SIGGRAPH 1977).
- The library's depth reading (lib depth_near and depth_find), Catmull-Rom resampling and Chris Wellons' lowbias32 integer hash (hash-prospector, public domain; lib common.glsl) and the red guard (lib red_guard.glsl), which keeps reds short of WCAG's red flash line.
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness; the beat clock takes its tempo from the gaps between kicks, inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
- Not used: a menu of simulated phenomena for the user to pick from and apply to an image, or a simulation steered by pointing at the image, Adobe's US 11,409,423 and US 11,755,187: this effect runs one simulation, its Style changes only how the liquid is drawn, and nothing takes pointer or touch input. A phase field carried along by a velocity worked out from it, Huawei's pending US 2025/0117558: the height here rises and falls in place and is never carried along.
Everything else is written for this library: the picture and the depth as the field, the magnet that wanders on the bars, the cones from the field's peaks, the picture showing through the flat liquid. MIT.

EXPERIMENTAL
Raw audio's beats are experimental (AUDIO).

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new ferrofluid.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
