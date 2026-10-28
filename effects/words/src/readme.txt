Words {v}: the picture rebuilt from words, packed into its subject, filling it, or written in lines around it.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/words.md

The picture is made of the words of a text, the start of Walt Whitman's "I Sing the Body Electric" unless you give it your own. It has three layouts.

Cloud is a word cloud in the shape of the subject: a dancer, a hand, whatever stands in front in a depth map or is bright or moving. The most frequent words come biggest and deepest inside it, each word once, and smaller ones fill in around them. The words ride the subject as it moves, and the ones it leaves behind fade while new ones fill its new shape.

Portrait fills the whole picture with the text in its order, each word colored by the picture under it. Words are big where the picture is plain and small on its features, so a face keeps its eyes and mouth.

Lines writes the text in small lines that run around the subject's outline, ring after ring, as Hebrew micrography draws a figure with lines of tiny script. The lines move slowly as the subject moves.

Placing is Wordle's way: one word at a time, at the biggest size it fits, at the best free spot, never on a word already there. The effect keeps every word from frame to frame and places new ones only into the room the others leave.

USE
Drag words.tox into your network. It shows TouchDesigner's sample movie of a misty lake as a word cloud in the bright mist. Wire a TOP into input 1: the result is on output 1 at its size. For Cloud and Lines, wire a depth map or a mask into input 3 (a depth camera, Depth Anything, a person mask): the subject is then what stands in front, and without it the bright parts of the picture. Wire music into input 2 and the words swell on the beat. Open Window shows the picture full size, and Esc closes the window.

YOUR TEXT
Point Text at any DAT holding your text: a Text DAT, or a table, read cell by cell. Words are what lies between spaces, with punctuation trimmed from their ends. The effect uses up to 1024 different words and the first 4096 words of the text. Cloud leaves out common English words (the, and, of) unless you turn Skip Common Words off, and sizes the rest by how often they come. A Text TOP inside draws every word once with the font you name, so any language and script the font has works, and no font ships in this file.

THE PAGE
Layout picks Cloud, Portrait or Lines. Text, Case, Skip Common Words, Font and Bold are the words and how they are set. Largest and Smallest set the words' sizes (Lines writes every word at Smallest). Detail sets how much the picture's detail makes Portrait's words smaller. Shape From picks where the subject is for Cloud and Lines: Depth (what stands in front in the depth map on input 3, floors and walls left out), Mask (inside the mask on input 3), Brightness or Movement. Sensitivity sets how easily a part counts, and Depth Type and Max Distance say what input 3 holds. Spread lets Cloud's words go past the subject's edge. Follow sets how much Cloud's words ride the subject's movement. Fade is how long a word takes to come and go, Fill Speed how many may come each second, and Reset starts over. Color picks each letter colored by the picture under it, each word one color, or white; Lift brightens dark colors; Backdrop is how much of the picture shows behind the words. Beat Pump and Swell are for input 2, and Flashing says how often a beat may pump the words.

AUDIO (input 2)
On each beat every word swells a quarter bigger and brightens, then settles over a third of a second, as often as Flashing allows (Beat Pump). As the music gets louder than it has been the words brighten (Swell), following the loudness over a second. Raw audio (Audio File In, Audio Device In) gives the beats and loudness from the sound itself. Fosfora's signal gives them too. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too.

FLASHING
A beat swelling every word at once changes large parts of the picture together, which counts as flashing, so a beat does it only through a gate that follows the Flashing parameter. Off never pumps the words. Calm (the default) does at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. Small text that moves flashes too, since each stroke passing a spot is light and dark, so Lines' lines move at most a line's spacing a second, and Portrait's words stay where they are while the picture moves under them. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
About {perf} on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
The text lane makes the words: text holds the built-in text and text_in the DAT Text names; words, a Script DAT, finds the distinct words, measures them with measure and packs them into atlas, a Text TOP that draws them all at once; ink, a compute shader, finds where each word's ink lies there; vocab turns the words' numbers into a texture, and order (the order the layout takes the words) into order_tex. The grid lane cuts the picture into cells of 8 x 8 pixels (cells: the subject, detail and brightness), steadies the subject (region), finds its outline (seed) and the distance from every cell to it by jump flooding (jfa, field), and readies Lines' lines (rings). layout, a compute shader with one workgroup of 1024, keeps every word's slot from frame to frame and places new ones (layout_fb is its last frame). word_geo has a square for every slot and word_mat's shaders place, size and color each word from the atlas; render draws them and look puts them over the picture. The motion lane is the picture's optical flow (lib optical_flow and flow_speed), which Cloud's words ride; moving passes it on only then (or for Shape From Movement), so the flow rests otherwise. Input 3 goes through depth, near and find (lib depth_near, depth_find) to subject. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, flash_limit and flash let it through as often as Flashing allows, and pump holds the words up; level, level_now and level_usual are the loudness, over a second and its usual level over 4 seconds.

CREDITS
- Placing words: Wordle, by J. Feinberg (2008), as described in F. B. Viegas, M. Wattenberg and J. Feinberg, "Participatory Visualization with Wordle" (IEEE InfoVis 2009, TVCG 15(6)): one word at a time, biggest first, at the first free spot, never overlapping one already placed.
- Cloud's shape: Y. Wang et al., "ShapeWordle: Tailoring Wordles using Shape-aware Archimedean Spirals" (IEEE VIS 2019, TVCG 26(1), 2020): the words placed out from the shape's deepest point, by its distance field.
- Keeping words in place and moving only those an edit disturbs, words as rigid bodies pushed apart: Y. Wang et al., "EdWordle: Consistency-preserving Word Cloud Editing" (IEEE VIS 2017, TVCG 24(1), 2018).
- Lines: the old art of micrography (Hebrew micrography above all), drawing a figure with lines of tiny script, and R. Maharik, M. Bessmeltsev, A. Sheffer, A. Shamir and N. Carr, "Digital Micrography" (SIGGRAPH 2011, ACM TOG 30(4)), text laid along lines that follow a figure.
- The distance field: jump flooding, G. Rong and T.-S. Tan, "Jump Flooding in GPU with Applications to Voronoi Diagram and Distance Transform" (I3D 2006).
- The motion: this library's Lucas-Kanade optical flow (B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to Stereo Vision", 1981), shared with Datamosh, Fluid, Motion Magnify, Pencil, Slit-Scan and VHS + CRT. Finding what stands in front in a depth map (lib depth_find) is shared with Fluid, Particles, Point Cloud and Reaction-Diffusion.
- The built-in text: Walt Whitman, "I Sing the Body Electric" (Leaves of Grass), its first two sections up to "in all their performances", public domain, from Project Gutenberg's eBook #1322.
- The font: whichever you name, drawn by TouchDesigner's Text TOP at run time; none ships here.
- Not used: two Adobe patents near this work, which the effect stays clear of: US 11,610,350 (cells filling a shape turned to follow its medial axis; nothing here finds a medial axis, and Lines follows the distance to the outline) and US 10,559,061 (ornaments placed between streamlines drawn from a user's guide strokes, matched to the spaces by shape; nothing here takes a guide or matches shapes).
Everything else is written for this library: the layout on a grid of cells, one bit a cell in shared memory, with every spot at every size tried at once and the best taken by an atomic maximum; Portrait's sizes from the picture's detail; Lines' lines as the level sets of the distance to the outline, slowed, each word turned along its line and written on from the last; the words kept, carried, pushed and faded from frame to frame; each word's ink found in the atlas; the beat pump through the flash gate and the swell with the loudness. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new words.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
