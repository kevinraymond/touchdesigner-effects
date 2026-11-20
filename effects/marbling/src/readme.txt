Marbling {v}: the live picture floated on a marbler's tray, inks dropped on the beats and combed into the classic patterns on the bars.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/marbling.md

Marbling is the old craft behind the swirled end papers of books, called ebru in Turkey. A marbler floats inks on a tray of thickened water (the size): each drop spreads into a disc and pushes the inks already there aside, and then combs and styluses drawn through the tray pull the inks into patterns. Paper laid on the surface takes the pattern.

This effect floats the live picture on the size, as if it were the first ink. On each beat a drop of ink falls and pushes the picture aside; on each bar a comb is drawn through the tray in the classic order, across and back (gel-git), then a fine comb at right angles (nonpareil), then a comb drawn along a wave (bouquet). The picture stays live through it all, so a dancer is combed into feathers mid-step. Every drop and stroke holds for a few bars and then relaxes, so the picture comes back while new ones are made.

USE
Drag marbling.tox into your network. It shows TouchDesigner's sample movie, marbled at 120 BPM by itself. Wire any TOP into input 1, and the result is on output 1 at the input's size. You can also wire audio or beat channels into input 2 and a depth map or mask into input 3 (below). Open Window shows the picture full size, and Esc closes the window. Reset clears the tray at once.

THE PAGE
Inks picks Picture (each drop is the picture's own color where it falls, taken the moment it falls) or Ebru (traditional pigments: indigo, ochre, rose, off-white, umber and sea green, in turn). Pattern says how far each tray is combed over its four bars: Stone (drops only), Gel-Git, Nonpareil or Bouquet. Drop Size sets how big the drops are (0 drops none), Comb how hard the combs pull and Tine Spacing how far apart their tines are. Hold says how many bars a drop or a stroke lasts before it relaxes, and Relax how many bars it takes to relax. Tine Spacing, Hold and Relax apply to the next drops and strokes; Drop Size and Comb change the whole tray at once.

Keep Subject, Input 3 Holds, Sensitivity, Depth Type and Max Distance read input 3. Drops and Loudness are the music's.

AUDIO (input 2, optional)
Fosfora's signal is the best input. Run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. Each beat drops ink (Drops: every beat, every other beat or the first of each bar), at most three a second; the louder the beat, the bigger the drop (Loudness). The drops spread over the whole tray, each well away from the last few. Each bar draws the tray's next stroke, at most one every 2 seconds, a stroke taking a beat to draw. A new section of the song relaxes the whole tray over a bar and starts a new one. Raw audio (Audio File In, Audio Device In) gives beats from a kick detector and a beat clock that locks to the kicks' tempo. That clock is experimental and can still add or miss beats. TouchDesigner's audioAnalysis gives beats from its kick or onset channels. With nothing wired, the tray keeps 120 BPM by itself.

DEPTH OR MASK (input 3, optional)
With Keep Subject on, what stands in front of its surroundings in a depth map (brighter nearer) stays the live picture, clear of the inks and the combs, so a person dances in front of a marbled room. Floors and walls don't count as standing out, someone cut off by the left or right edge of the frame drops out, and feet merge with the floor they stand on. With Input 3 Holds on Mask, what is inside the mask (white inside: MediaPipe, the NVIDIA Background TOP) is kept clear instead. Sensitivity says how easily something counts as standing out, or how gray a mask counts as inside. Depth Type reads depth cameras too: the RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3, the whole picture is marbled.

FLASHING
Marbling has no Flashing setting: a drop spreads over a quarter of a second and a stroke over a beat, at most three drops a second and one stroke every 2 seconds, and nothing jumps at once. The flashes were measured on the output under a beat far busier than music on four clips: the dancer, red flowers and a plaza at the clip's own, the koi half a flash a second over the clip's own (the combs sweep their orange and white past the dark water), all well within WCAG's 3, and no red above the clip's own (docs page, Accessibility).

PERFORMANCE
Marbling costs about 1.8 ms a frame on the GPU and 0.6 ms on the CPU at 1280 x 720 on an M2 Pro, with a song on input 2 and about 25 drops and strokes on the tray. marble takes about 1 ms of it, and its cost grows with the tray: Hold at 16 bars fills it with about 50 and costs about 6 ms.

INSIDE
Input 2 goes through audio (lib audio_in). idle stands in for the beats while nothing is wired. tray, a Script CHOP, keeps the tools on the tray, newest first: a drop on each beat, a stroke on each bar, each with when it was made and how long it rises, holds and relaxes. ta, tb and tc hand its channels four at a time to the shaders, as uniform arrays. ink takes each new drop's color from the picture where it falls and keeps it (ink_fb is the inks last frame; clear is where they start). Input 3 goes through depth, near (nearness at a quarter size) and find (what stands out, or the mask), lib depth_near and depth_find. marble draws the picture: for each pixel it works out each tool's strength now and undoes the tools newest first, and the point lands in a drop's ink or, past every tool, on the picture; four samples a pixel. The Parameter Execute DAT reset starts a clean tray.

CREDITS
- The method: S. Lu, A. Jaffer, X. Jin, H. Zhao and X. Mao, "Mathematical Marbling" (IEEE Computer Graphics and Applications 32(6), 2012): ink drops, straight and wavy combs as closed-form maps of the tray that keep areas, each undone by its inverse, and the picture drawn by undoing every tool at once at each pixel, sampled on a rotated 2 x 2 grid. A. Jaffer, Mathematical Marbling (people.csail.mit.edu/jaffer/Marbling): the drop's inverse, and pst-marble's shift, after which each comb here gives back its mean pull so it doesn't carry the whole tray along. Drawing all the tools from scratch at each pixel follows K. Sims, "Choreographed Image Flow" (J. Visualization and Computer Animation 3(1), 1992), as the paper does.
- The patterns: gel-git (a rake across and back, its tines offset) and nonpareil (then a fine comb at right angles) as Jaffer's How-To draws them. Bouquet here is the paper's wavy pattern, a comb with a sine wave after it (its Figure 8), standing in for the bouquet a marbler draws with two rakes on curved tracks.
- The drops spread over the tray by the R2 sequence: M. Roberts, "The Unreasonable Effectiveness of Quasirandom Sequences" (extremelearning.com.au, 2018).
- The library's depth reading (lib depth_near and depth_find).
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness; the beat clock takes its tempo from the gaps between kicks, inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
- Not used: a map of texture coordinates kept from frame to frame and carried along by a velocity, GritWorld's application US 2023/0106802 (its status unknown), or a displayed color carried along by a backtrace, ByteDance's US 12,694,597: nothing here is carried over from the last frame, and the picture is read through the tools undone afresh each frame. A menu of simulated phenomena to apply to an image, or one steered by pointing at the image, Adobe's US 11,409,423 and US 11,755,187: this effect runs one kind of marbling, Inks changes only the drops' colors, and nothing takes pointer or touch input.
Everything else is written for this library: the live picture as the first ink, the drops on the beats and the strokes on the bars, the tools relaxing so the picture comes back, the subject kept clear. MIT.

EXPERIMENTAL
Raw audio's beats are experimental (AUDIO).

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new marbling.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
