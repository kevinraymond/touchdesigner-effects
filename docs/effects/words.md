# Words

![Four views of a dancer turning in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. CLOUD fills her silhouette with the words of a poem in her own pale colors over the dimmed picture, a few such as charge and balks bigger than the rest. PORTRAIT fills the whole picture with the poem's words, big gray ones such as sing, electric and armies over the dark warehouse and small bright ones packed where she and the lit haze are. LINES writes the poem in tiny lines that circle her outline ring after ring, like a fingerprint spreading across the picture. On each beat the words swell a little](words.webp)

*The three layouts on a dancer, the clip at top left, with her depth map on input 3 and a song on input 2.
Cloud's words ride her as she turns, Portrait's stay where they are while she moves under them, and Lines' rings
follow her slowly. The words swell on the beat at most once a second (Flashing at Calm).*

**New to word clouds?** A word cloud is a picture of a text, its words packed together and the ones it uses most drawn
biggest. Jonathan Feinberg's Wordle made them famous in 2008, placing the words one at a time, biggest first, each at
the first spot along a spiral where it touches nothing already placed. Word clouds in a shape followed, a cloud in the
outline of a heart or a map. Older still is micrography, an art from Hebrew manuscripts of the Middle Ages, where a
scribe drew a figure, an animal or a flower or an ornament, with lines of tiny script that follow its outline. And
typographic portraits draw a face with the words of a text, big words where the face is plain and small ones on its
eyes and mouth.

Words does all three live, on video, from any text. Cloud packs the words into the subject, a dancer or a hand or
whatever stands in front in a depth map, the most frequent biggest and deepest inside it, and the words ride the
subject as it moves. Portrait fills the whole picture with the text in its order, each word colored by the picture
under it and sized by its detail. Lines writes the text in small lines that run around the subject's outline, ring
after ring, as micrography does. Each frame it keeps every word where it was, lets the ones that no longer fit fade, and
places new ones into the room they leave, Wordle's way. The built-in text is the start of Walt Whitman's "I Sing the
Body Electric"; point it at your own.

**[Download words.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/words.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `words.tox` into your network. It shows TouchDesigner's sample movie of a misty lake as a word cloud in the
   bright mist.
2. Wire a TOP into input 1. The result is on output 1, at the input's size.
3. For Cloud and Lines, wire a depth map or a mask into input 3: a depth camera (Kinect, RealSense), a depth estimator
   such as Depth Anything, or a person mask. The subject is then whatever stands in front of its surroundings (or is
   inside the mask). With nothing on input 3 it is the bright part of the picture, and Shape From can make it whatever
   moves.
4. Wire music into input 2 (see Audio input). The words then swell on the beats and brighten as the music swells.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

**Your own text.** Point Text at any DAT that holds your text: a Text DAT, or a table, read cell by cell. Words are
what lies between spaces, with punctuation trimmed from their ends, as written unless Case says otherwise. The effect
uses up to 1024 different words and the first 4096 words of the text. Cloud leaves out common English words (the, and,
of and the like) unless Skip Common Words is off, and sizes the rest by how often the text uses them. A Text TOP inside
draws every word once with the font you name, at run time, so any script the font has works (the Text TOP shapes whole
words, so joined and right-to-left scripts come out as the font draws them), and no font ships in the file. Edit the text
while the effect runs and the words of the old one give way to the new.

To update, delete your copy and drag in the new `words.tox`. Dragging a `.tox` in embeds a copy, so a new release
doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Words page holds, top to bottom, the layout and the words, their sizes, the subject, how they move and come and
go, their colors, the music, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Layout | Cloud | How the words make the picture. Cloud is a word cloud in the shape of the subject, the most frequent words biggest and deepest inside it. Portrait fills the whole picture with the text in its order, big words where the picture is plain and small ones on its features. Lines writes the text in small lines that run around the subject's outline, ring after ring (without a subject, across the picture like a page). |
| Text | ./text | The DAT holding the text. The built-in one, `text` inside the effect, is the start of Walt Whitman's "I Sing the Body Electric". |
| Case | As Written | The words as the text writes them, or all in capitals, or all in small letters. |
| Skip Common Words | On | Cloud leaves out common English words, as a word cloud does, so the words that matter come biggest. Portrait and Lines read every word. |
| Font | Arial | The font, by name: any installed on the computer. Arial is on Mac and Windows. A missing font falls back to TouchDesigner's own. |
| Bold | On | The bold face of the font. |
| Largest | 0.2 | Cloud and Portrait: how tall the biggest words may be, as a share of the picture's height, 0.05 to 0.5 (a line of text, its letters and the space above and below them). |
| Smallest | 18 | How tall the smallest words are, in pixels, 8 to 64. Lines writes every word at this size. Smaller fills more closely. |
| Detail | 0.5 | Portrait: how strongly the picture's detail makes words smaller, 0 to 1. At 1 even faint texture takes small words; at 0 only the strongest edges do. |
| Shape From | Depth (Input 3) | Cloud and Lines: where the subject is. Depth is what stands in front of its surroundings in the depth map on input 3, floors and walls left out. Mask is what is inside the mask on input 3 (white inside). Brightness is the bright parts of the picture, Movement what moves. With nothing on input 3, Depth and Mask take the bright parts. |
| Sensitivity | 0.5 | How easily a part counts as the subject: farther depth, a grayer mask, dimmer brightness or slower movement counts as well. |
| Depth Type | Brighter Is Nearer | What input 3 holds. Brighter Is Nearer suits depth estimators and masks. Distance 0-1 suits the RealSense and Kinect TOPs (0 near, 1 far, black where the camera got no reading). Distance in Meters suits the Kinect Azure TOP, scaled by Max Distance. |
| Max Distance | 4 | For Distance in Meters: how far away, in meters, counts as the far end of the depth. |
| Spread | 16 | Cloud: how far past the subject's edge the words may go, in pixels, 0 to 80. |
| Follow | 1 | Cloud: how much the words ride the subject's movement, 0 to 1. At 0 they stay put and the subject moves under them. Portrait's words stay put; Lines' follow their lines. |
| Fade | 0.4 | How long a word takes to appear, in seconds, 0.1 to 2. It goes in half that. |
| Fill Speed | 600 | How many new words may appear each second, 30 to 1200, filling the room words leave. |
| Reset | | Clears every word and lays the picture out anew. |
| Color | Picture | Picture colors each letter by the picture under it. Word gives each word one color, the picture's across it. White makes white words. |
| Lift | 0.5 | How much dark colors are brightened, 0 to 1, so words on a dark part of the picture still read. White stays white. In Cloud black words also lift toward gray, so a dark subject shows. |
| Backdrop | 0.15 | How much of the picture shows behind the words, 0 to 1. At 0 the words are on black. |
| Beat Pump | 0.5 | On each beat on input 2 every word swells and brightens, then settles, 0 to 1, as often as Flashing allows. |
| Swell | 0.5 | How much the music getting louder than usual brightens the words, 0 to 1. It follows the loudness over a second. |
| Flashing | Calm | How often a beat may pump the words. Off never does. Calm does at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The layouts

![Four views of two hands spread open against black, each named in the library's pixel font. INPUT is the clip. CLOUD packs each hand with words in its own skin tones, account and charge biggest across one palm and body across the other, smaller words in the fingers. PORTRAIT fills the picture with the poem's words, small warm ones packed into the hands and fingers and big dim ones in the dark around them. LINES writes the poem in tiny lines that follow the outline of each hand and finger, ring inside ring, and spread out across the dark](words_layouts.webp)

*The three layouts on hands, with their depth map on input 3 and a song on input 2. Each hand gets its own cloud,
Portrait keeps the hands' shapes in small words against big dim ones, and Lines' rings run around every finger.*

## How it works

**The words.** A Script DAT splits the text into words and finds the distinct ones, counting how often each comes. It
measures each with a Text TOP that nothing draws (its `evalTextSize()`), packs them into rows on a 1280 x 1280 atlas at
the biggest font size that fits them all, and one Text TOP draws them all there at once, from a table of each word and
where it goes. A compute shader then finds where each word's ink lies in the atlas, a workgroup a word, so the layout
packs the letters themselves and not the line they sit on: "soul" has nothing below its baseline and "body" has. All of
this runs only when the text, the font or the case changes.

**The grid.** The layout works on cells of 8 x 8 pixels, 160 x 90 of them at 1280 x 720 (bigger cells for a picture
past 1280 on a side, so there are never more than 160 across or down). A pass a pixel a cell gives each cell how much
of it is the subject, how much detail the picture holds there (the mean slope
of its brightness) and how bright it is. The subject is smoothed over its neighbors and eased over a seventh of a
second, so its edge doesn't flicker. Its outline is found, and every cell's distance to it by jump flooding (Rong and
Tan), eight passes on the grid, signed (negative inside) and smoothed.

**The layout.** One compute shader holds 1024 slots for words, one workgroup, an invocation a slot, and keeps them
from frame to frame. Each frame:

- Each word is carried: in Cloud by the picture's motion (this library's optical flow) at its middle, in Lines along
  with its line. Portrait's words stay put.
- A word that runs into an older one is pushed off it by half the overlap a frame, as EdWordle moves words as rigid
  bodies (Lines' words only along their line, and only against words on the same line). One that is still on it, or out
  of its region (off the subject, or on detail too fine for its size), for more than 0.15 seconds starts to fade out.
  In Portrait and Lines its place is free at once, so the next word fades in over it rather than leave a dark hole in
  the page; in Cloud it keeps its place until it has gone.
- The free cells become masks in shared memory, a bit a cell, rows of 32-bit words: one for the cells words cover,
  with a little room around each word, and for each of eight sizes the cells a word of that size may not cover.
- Then new words go in, a few a frame (Fill Speed), the way Wordle places them. The next word comes from the text (in
  Cloud, the most frequent word not yet showing, then repeats, smaller). Every invocation tries its share of the
  spots, at every size the word may take, by testing its box's rows of bits, and the best spot wins by an atomic
  maximum on a key that puts size first, then how good the spot is: in Cloud the deepest inside the subject's distance
  field (ShapeWordle starts at the shape's deepest point and spirals out), in Portrait the first in reading order. Once
  the picture is full the search rests until a word leaves.

Cloud caps each word's size by its rank, so the few most frequent words can be big and the many rare ones small, as in
a word cloud. Portrait sizes words by the picture's detail against its mean detail, so a word may be big only where the
picture is plain under all of it. Lines turns each word to its line: the lines are the level sets of the distance to
the outline, a line's height apart, and a word lies along one, upright, its ends checked to stay on it. Its text is
written on from the last word placed, along the line, as long as there is room, and only where there isn't does it
search for a new start, just after another word if it can, then on the lines nearest the subject.

**Drawing.** Every slot is one square, drawn by a Geometry COMP with an instance for each and placed, sized, turned and
faded by its material's vertex shader from the slot. The pixel shader cuts the word from the atlas. Drawn bigger than
the atlas holds it, the letters' antialiased edge is treated as a distance and cut at one pixel's width, so even the
biggest words stay crisp. A Render TOP draws them all, and the result goes over the picture, dimmed to Backdrop.

**Limits.** The layout is greedy, Wordle's, so a cloud is never as tightly packed as one an optimizer arranges at
leisure. A cell is 8 pixels, so boxes round up to whole cells and gaps between words vary by a few pixels. And the
subject is only as good as what finds it: a depth map from a camera or Depth Anything gives a clean figure, while
Brightness and Movement give whatever is bright or moving.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends beats and loudness. Drag `fosfora_signal.tox` (in
Fosfora's `integrations/touchdesigner/`) into your project and wire it into input 2. **Raw audio** (an Audio File In or
Audio Device In CHOP) gives the beats and the loudness from the sound itself. **TouchDesigner's audioAnalysis** gives
beats from its kick or onset channels and loudness from its level.

On each beat every word swells, up to an eighth bigger and a quarter brighter at the default Beat Pump (a quarter and a
half at 1), and settles over a third of a second, as often as Flashing allows (once a second at Calm). The words keep
their places through it, so neighbors overlap for a moment at the peak. The loudness, smoothed over a second and judged
against its usual level over the last 4 seconds, brightens the words as the music swells (Swell).

**Nothing wired:** the words as they are, with no pump and no swell.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters, on the dancer clip with its depth on input 3 and a beat far busier than music on
input 2, the Mac otherwise idle. Each frame took, on the GPU, 2.4 ms for Cloud (95th percentile 3.8 ms), 1.8 ms for
Portrait (2.6 ms) and 3.0 ms for Lines (4.4 ms), and 0.8 to 1.1 ms on the CPU, the medians of three runs each. Most of
it is the layout's compute shader: 0.7 ms for Cloud, 0.8 ms for Portrait and 2.1 ms for Lines, whose words are
small, many (about 800 at once) and turned, and which searches more often, since words come and go around a moving
subject. Cloud adds the optical flow its words ride (0.7 ms), which Portrait and Lines leave resting. Drawing the words
is about 0.6 ms. The search for room, most of the layout's cost, rests once the picture is full, until a word leaves.
Laying the text out (measuring the words, drawing the atlas, finding each word's ink) runs only when the text, the
font or the case changes. Nothing inside cooks while the output is unused.

## Accessibility

- **Flashing.** A beat swelling every word at once changes large parts of the picture together, which counts as
  flashing, so a beat does it only through the standard flash gate. Off never does, Calm (the default) at most once a
  second, and Up to 3 per second is WCAG 2.3.1's limit.
- **Text that moves.** Small text flashes when it moves: each stroke passing a spot is light and each gap dark. Lines'
  lines are about as far apart as the test's cells (a line every 21 pixels), so lines that followed a dancer at once
  swung every spot they swept between text and gap, 2 flashes a second with Flashing Off where the clip has 1. They now
  move at most a line's spacing a second. White words riding the dancer through Portrait's packed page did the same,
  so Portrait's words stay put and the picture moves under them; Cloud's fewer, bigger words ride her within the
  limits. A word squeezed between two older ones, pushed out of all of its overlap each frame, jumped to the other side
  and back every other frame (19 flashes a second in one spot, in white); pushed out of half, it settles. And fading
  every word out at a cut, to lay the new shot out afresh, took the whole picture to black and back; the words now stay
  through a cut and only those that no longer fit go.
- **Legible text.** At the default Smallest a line is 18 pixels tall (letters about 13 pixels) at 1280 x 720, in a
  bold face. Lift keeps words on a dark picture from vanishing, and in Cloud black words lift toward gray.
- **No meaning in color.** The words take the picture's own colors (or white); their sizes and places carry the
  picture, and nothing is signaled by hue.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, the loudness swinging 8 times a second) or a dance beat at 140 BPM, and counted the flashes
in the worst second by WCAG's area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse, Cloud (the defaults) | 0.5 | 0.5 | 0.5 | 1.0 |
| Dancer, Portrait | 0.5 | 1.0 | 3.0 | 1.0 |
| Dancer, Lines | 1.0 | 1.0 | 2.0 | 1.0 |
| Hands, Cloud | 1.0 | 1.0 | 1.0 | 1.5 |
| Red flowers against the sun, Cloud | 1.0 | 1.0 | 3.0, red 0.5 | 1.0, red 1.0 |
| Dancer, a dance beat (140 BPM) | 0.5 | 0 | 0.5 | 1.0 |
| Dancer, Lines in white | 1.0 | 1.0 | 1.0 | 1.0 |
| Dancer, Portrait in white | 1.0 | 1.0 | 3.0 | 1.0 |
| Dancer, Beat Pump 1 | 0.5 | 0.5 | 1.0 | 1.0 |

Every row keeps its setting's promise, and none goes past WCAG's 3. With Flashing Off the words add nothing to the
clip's own flashes beyond the measurement's half-flash margin. Up to 3 per second reaches WCAG's 3 where the words
cover the picture brightly (Portrait, and Cloud over the sunlit flowers): every beat lets every word swell, as that
setting allows. The last three rows are corners, spot-checked: white words, which change the most when they move, and
the strongest pump.

## Credits and license

MIT. The shaders and operators are written for this library, including the layout on a grid of cells with a bit a
cell in shared memory, every spot at every size tried at once and the best taken by an atomic maximum; Portrait's sizes
from the picture's detail; Lines' lines as the level sets of the distance to the outline, slowed, each word turned
along its line and written on from the last; the words kept, carried, pushed and faded from frame to frame; each word's
ink found in the atlas; the beat pump through the flash gate and the swell with the loudness.

- **Placing words:** Wordle, by J. Feinberg (2008), as described in F. B. Viégas, M. Wattenberg and J. Feinberg,
  ["Participatory Visualization with Wordle"](https://doi.org/10.1109/TVCG.2009.171) (IEEE InfoVis 2009, TVCG 15(6)):
  one word at a time, biggest first, at the first free spot, never overlapping one already placed.
- **Cloud's shape:** Y. Wang et al., ["ShapeWordle: Tailoring Wordles using Shape-aware Archimedean
  Spirals"](https://doi.org/10.1109/TVCG.2019.2934783) (IEEE VIS 2019, TVCG 26(1), 2020): the words placed out from the
  shape's deepest point, by its distance field.
- **Keeping the layout:** Y. Wang et al., ["EdWordle: Consistency-preserving Word Cloud
  Editing"](https://doi.org/10.1109/TVCG.2017.2745859) (IEEE VIS 2017, TVCG 24(1), 2018): moving only the words an
  edit disturbs, words as rigid bodies pushed apart.
- **Lines:** the old art of micrography, Hebrew micrography above all, drawing a figure with lines of tiny script; and
  R. Maharik, M. Bessmeltsev, A. Sheffer, A. Shamir and N. Carr, ["Digital
  Micrography"](https://doi.org/10.1145/2010324.1964995) (SIGGRAPH 2011, ACM TOG 30(4)): text laid along lines that
  follow a figure.
- **The distance field:** jump flooding, G. Rong and T.-S. Tan, ["Jump Flooding in GPU with Applications to Voronoi
  Diagram and Distance Transform"](https://doi.org/10.1145/1111411.1111431) (I3D 2006).
- **The motion:** this library's Lucas-Kanade optical flow (B. D. Lucas and T. Kanade, "An Iterative Image
  Registration Technique with an Application to Stereo Vision", 1981), shared with Datamosh, Fluid, Motion Magnify,
  Pencil, Slit-Scan and VHS + CRT. Finding what stands in front in a depth map (lib `depth_find`) is shared with Fluid,
  Particles, Point Cloud and Reaction-Diffusion.
- **The built-in text:** Walt Whitman, "I Sing the Body Electric" (*Leaves of Grass*), its first two sections up to
  "in all their performances", public domain, from [Project Gutenberg's eBook
  #1322](https://www.gutenberg.org/ebooks/1322).
- **The font:** whichever you name, drawn by TouchDesigner's Text TOP at run time; none ships in the file.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

**Patents.** A search of US patents (October 2026) found no patent from these papers' authors on word clouds, their
layout, calligrams or micrography; the many patents that mention word clouds use them to show text analytics. Two
Adobe patents come near, and the effect stays clear of both. US 11,610,350 fills a shape with cells turned to follow
its medial axis: nothing here finds a medial axis, Cloud's words stay level, and Lines follows the distance to the
outline. US 10,559,061 places ornaments in the spaces between streamlines drawn from a user's guide strokes, matched to
the spaces by their shapes: nothing here takes a guide or matches shapes, and a word simply takes the biggest free
spot it fits. Wordle's own layout dates from 2008.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
