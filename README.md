# TouchDesigner Effects

Before [Fosfora](https://github.com/kevinraymond/fosfora), I had never heard of TouchDesigner.
While adding the examples for Fosfora's signal mode, I got the free version of TD and poked
around it a bit. Then I decided I would create some effects based on different things I've
worked on or seen, in case they are useful for anyone. If nothing else they are examples of solid
working effects. Enjoy!

![Every effect in the library on the same clip of a dancer in a hazy warehouse, each named in the library's pixel font. First the clip and its depth map (optional), the inputs, on a row of their own, then every effect: ASCII draws her in glyphs, Bent Cam turns her through a circuit-bent webcam into purple shadows, contoured light and torn green lines, Blob Track boxes her moving limbs, Caustics lights her and the haze with a moving net of bright lines, as sunlight through rippling water lights a pool's floor, Chladni Sand pulls the haze's light into glowing curves and rings on each beat and lets it settle back, Datamosh smears her pose into the next, Detail sculpts the haze into textured smoke and brings out the grain of the floor, Fluid pours flames off her as she moves, Glitch tears her on the beat, Lens Flare throws blue-white hexagons from the stage light across the warehouse, a thin star on the light, Motion Magnify makes her every swing and step larger, Paint turns her and the haze into soft strokes of paint, Particles shed glowing specks off her, Pencil draws her in quick graphite lines on white paper, the dark warehouse around her shaded in pencil strokes, Pixel Art draws her and the haze in big square pixels of a few flat grays and skin tones, jumping into bigger blocks on the beat, Pixel Sort sorts the haze and her clothes down each column into a pale curtain of light, Point Cloud turns her and the lit wall behind her in 3D, Reaction-Diffusion draws her alone on black, in white stripes that curve along her body like a fingerprint, Scan Processor draws her in fine scan lines and ripples them with the music like an old television's, Slit-Scan shows each row of her from a moment earlier than the one above, so her limbs twist as she turns, Temporal Resonator fans her arms out behind her in echoes a beat apart, each fainter and softer than the last, VHS + CRT plays her off a worn tape on an old TV as a band of torn lines crosses her, Video Vocoder brings out the grain of the haze and the edges of her clothes, crisper still when the music swells, Voxel Space makes her a row of pale mesas in the colors of her clothes and glides down the avenue between them, and Words fills her silhouette with the words of a poem in her own pale colors](docs/effects/showreel.webp)

*Every effect on the same clip, all in step, with the clip and its depth map (optional) as inputs on top.*

- **Free and MIT-licensed.** Use them in your own work, commercial work included; keep the
  license notice. See [License](#license).
- **Nothing to install.** Each effect is one self-contained `.tox`: no plugins, no C++
  operators, no Python packages, no files beside it. Drag it into your network and it runs,
  showing TouchDesigner's own sample movie until you wire in your picture.
- **Runs on the free license.** Every effect works on TouchDesigner's free Non-Commercial
  license.
- **Extras are optional.** Music on input 2 ([Fosfora](https://github.com/kevinraymond/fosfora)'s
  signal, any audio, TouchDesigner's audio analysis) and depth on input 3 (a depth camera or
  estimator) make some effects richer, and each page says what they add. None is needed to
  start.

Opening a `.tox` shows how it works. Each is a TOP in and a TOP out, with an optional CHOP input
for audio or beat data (and, for the effects that use depth, an optional depth TOP). Inside
you'll find a README with its credits, a comment on every operator, help on every parameter, and
an About page that names the TouchDesigner build it was saved in. Each effect has a page here
with a preview, a performance note, and a download link that always points at the latest release.

## Effects

| Effect | What it does |
|---|---|
| [ASCII](docs/effects/ascii.md) | ASCII art, live: the picture redrawn in text characters, heavy ones such as `@` for bright areas and light ones such as `.` for dim ones, the way old text-only terminals drew pictures. Line characters trace the outlines; each beat sends a ripple of changed characters out from the middle, and bars pop the contrast. |
| [Bent Cam](docs/effects/bent_cam.md) | A circuit-bent webcam filming a screen that shows its own picture, modeled down to the bytes. Wires across the sensor's pins stick and bridge the data lines the picture travels on, so it breaks into false colors and flat bands, slipped bytes turn it green and pink, and broken JPEG blocks streak it. The camera filming its own screen adds trails, spirals and rainbow moiré, and a mirror folds it into a kaleidoscope. It comes with a lot of 50 cameras, each shorted differently. On every beat the loose wires crackle with colored static, and on the bars a wire touches for a moment. |
| [Blob Track](docs/effects/blob_track.md) | The look of computer vision: whatever moves gets a numbered box that follows it, joined to its neighbors by lines, like surveillance software or a film's targeting display. Beats scramble the labels and spawn links. |
| [Caustics](docs/effects/caustics.md) | The picture as the floor of a pool under moving water, lit by the net of bright lines the ripples focus, as sunlight lights a swimming pool's floor. Slow swells roll across the water, whatever moves in the picture pushes it into wakes, and each beat drops a raindrop into it, so the light's net swims and ripples with the music. The floor wobbles under the waves and deeper water turns it bluer; a depth map makes the water shallower over what is nearer. The caustics are worked out from the waves, after Yuksel and Keyser (2009); TouchDesigner's caustics are tutorials and 3D scenes. |
| [Chladni Sand](docs/effects/chladni_sand.md) | The picture as sand on a vibrating plate, the experiment Chladni showed in 1787: each beat strikes the plate, and the picture's light slides into the lines of a figure of curves, stars and rings, piling up there in its own colors while the parts between go dark, then settles back until the next beat. The music's seven bands choose the figure, the bass the simplest and the treble the busiest, so it turns as the music does. With nothing wired, it strikes itself every 2 seconds in each figure in turn. |
| [Datamosh](docs/effects/datamosh.md) | Glitch art: one shot smears and melts into the next, the way a compressed video does when its keyframes (the full pictures it stores now and then) go missing. Beats make the picture bloom and catch up, bars set off the melts, and Fosfora's builds hold them back until the drop. |
| [Detail](docs/effects/detail.md) | Halo-free local contrast, live: the picture's fine detail made stronger, every crease, leaf and wisp of smoke standing out, while its edges stay clean, the crisp "HDR look" without the outlines sharpening draws. Or smoothed away, edges kept sharp, so a face turns to wax and a street to paint. It can also flatten the picture's big changes of light or deepen them. Beats make the detail jump and loudness swells it. Written from the papers (Paris, Hasinoff and Kautz's local Laplacian filters, and Aubry and colleagues' fast form); TouchDesigner's own TOPs sharpen edges and texture alike. |
| [Fluid](docs/effects/fluid.md) | A real fluid simulation over the picture, stirred by its movement: whatever moves pours fire, smoke or ink, which rises, curls into eddies and fades, so a hand trails smoke and a dancer burns. A depth map or mask on input 3 sets a whole silhouette alight. Beats make the flames leap and flare. Runs on any GPU, where NVIDIA Flow needs Windows and an NVIDIA card. |
| [Glitch](docs/effects/glitch.md) | Broken digital video on the beat: every beat tears thin slivers of the picture sideways, and on the one of each bar a burst makes blocks jump, freeze or lose their colors and rows slip, then the picture is whole again. Calm by default: at most one burst a second, or none at all. |
| [Lens Flare](docs/effects/lens_flare.md) | Real lens flare from real lenses: every bright light in the picture, a lamp, a headlight, the sun, throws the ghosts a camera lens would, copies of the iris's shape strung along the line through the middle of the picture and moving as the light moves, each tinted by the glass's coating, and a starburst of thin spikes. Worked out from the designs of four lenses in their patents (a 1953 Heliar, a 1934 Sonnar, a 1931 wide angle and a phone camera), after Lee and Eisemann; the free TouchDesigner flares flip and blur the highlights or draw made-up ghosts. Beats make the flare flare up and loudness strengthens it. |
| [Motion Magnify](docs/effects/motion_magnify.md) | The picture's movements made larger: grass sways wide, a nod becomes a bow, a dancer's bounce leaps, while whatever stands still stays put. It measures how each part of the picture moves and draws it further, keeping the movements that go back and forth (a sway, a step, a nod) and leaving a steady walk across the picture as it was, and it stretches rather than tears. Beats push the movement larger for a moment, and it can follow the music's tempo. Lagrangian, after Liu and colleagues' motion magnification; the better-known Eulerian methods are patented, and its page says why it doesn't use them. |
| [Paint](docs/effects/paint.md) | The picture as a painting, live: flat strokes that follow its edges, so a cheek is painted around its curve and grass along its blades, with ink lines along the edges. Oil on canvas, Watercolor washed onto paper with darker edges and pooling pigment, or Ink in two tones like a woodcut. A depth map or mask on input 3 paints near things finely and far things broadly, and each beat sweeps a band of broad strokes across the picture. Written from the papers (the anisotropic Kuwahara filter with polynomial weights, XDoG, watercolor rendering), and it costs the same at any brush size; the free TouchDesigner versions are a basic Kuwahara or an unfinished port under the GPL. |
| [Particles](docs/effects/particles.md) | Particles peel off a subject and drift away like smoke, in the picture's colors, or fill the frame for the subject to shove through (Push) or for a stream to part round it (Flow): people in a depth map (Kinect, RealSense, a depth estimator) or a mask for the best result, and with only a webcam or a video, whatever moves. Loudness thickens the stream, beats kick the cloud outward with a burst of sparks, bars swing the wind. |
| [Pencil](docs/effects/pencil.md) | The picture as a pencil drawing: quick lines along its edges that run past the corners and cross, as a fast hand draws them, and its tones matched to a real pencil drawing's (mostly paper, a band of mild strokes, a few dark accents) and drawn in pencil strokes. Sketch shades it in soft graphite, short strokes laid every way, Hatching in long parallel strokes that follow the picture's edges and cross only in the darks, and Lines draws the lines alone, in graphite, colored pencil, an animator's blue or white on black. The strokes travel with what moves rather than staying on the screen, beats redraw the drawing like the next frame of a hand-drawn animation, and loudness presses the pencil harder. Written from the papers (Lu, Xu and Jia's pencil drawing, Praun and colleagues' hatching); I found no TouchDesigner version of the method. |
| [Pixel Art](docs/effects/pixel_art.md) | The picture as pixel art in a small palette it picks itself, after Gerstner and his colleagues (2012). Each art pixel is a region of the picture shaped around its features, so an eye, a mouth or a fin lands on whole pixels instead of smearing, and the palette splits from one color into as many as you ask for, then follows the picture's colors as it moves. Dither draws the in-between shades in checkerboards as old consoles did, and each beat kicks the art into bigger blocks like the Super Nintendo's mosaic. |
| [Pixel Sort](docs/effects/pixel_sort.md) | Pixel sorting, really sorted: runs of pixels, those between two brightness thresholds, between the picture's edges, inside a depth map or mask, or whole lines cut at random, are rearranged in order of brightness, hue or saturation, so a sky pours, a face drips and a lamp rains light while the rest of the picture stays put. Every span of every line is fully sorted every frame, along any angle, on any GPU. The sort turns over on the bars, and beats tear thin streaks against the grain. As far as I could find, no other free TouchDesigner pixel sorter really sorts spans; the others sort whole rows or fake the look with a feedback loop, and the one real span sort is a paid plugin for NVIDIA cards only. |
| [Point Cloud](docs/effects/point_cloud.md) | The picture as a cloud of points in 3D, each at its depth (a depth camera, a depth estimator, or the picture's brightness), seen from a camera that sways round it: people stand out from the wall behind them. Solid dots, glowing dots, or a surface of blended splats. Loudness swells the dots, beats deepen the cloud, bars swing the camera. |
| [Reaction-Diffusion](docs/effects/reaction_diffusion.md) | The picture drawn by a growing reaction-diffusion pattern, the stripes and spots that may give a zebra its markings, steered by the picture so the stripes run along its edges, around an eye or down a stem, like a fingerprint. Lines draws the picture by the width of its stripes, as an engraving does; Dots and Coral change the pattern itself with the picture's darkness. It can grow everywhere or only on what is bright, what moves, or what stands out in a depth map or mask on input 3, and the beats send ripples through the drawing. Written from the papers (Gray-Scott, and Witkin and Kass's steered diffusion); the free TouchDesigner versions diffuse the same way in every direction. |
| [Scan Processor](docs/effects/scan_processor.md) | The picture on an old television whose raster the music bends, as video artists bent theirs around 1970. It is drawn in scan lines by a beam, and it ripples sideways and squeezes into bright bands like Paik and Abe's Wobbulator, twists and bends like a ribbon like Harrison's Scanimate, or gathers into glowing pleats as the beam speeds and slows (FM). One signal generator follows each band of the music, so a kick bends the whole frame while the hi-hats make its edges shiver, and beats strike it. A Colorizer paints it in bands of blue, orange and gold. |
| [Slit-Scan](docs/effects/slit_scan.md) | Each part of the picture comes from its own moment, so the top might be now and the bottom a second ago, and whatever moves bends, stretches and smears through time. The moment can follow a sweep across the picture, rings from a center, a depth map or mask, or a drifting noise, or a slit with film running past it as in a photo-finish camera. Between the input's frames it fills in along the movement, so even a slow video bends smoothly. The map flips on the bars, and beats tear thin slivers of the picture open onto other moments. Its page says what the frame history costs in GPU memory, measured. |
| [Temporal Resonator](docs/effects/temporal_resonator.md) | Every pixel a plucked string tuned to the beat: whatever moves comes round again on the next beat, and the next, each echo fainter and softer than the last, the way a string's note repeats and dies away. A dancer's arms fan out in echoes a beat apart and people crossing a square leave chains of footsteps on the beat, while the live picture stays in front of its own echoes. Alternating brings every other echo back as a shadow. It follows the music's tempo by itself and is plucked on its beats, after Karplus and Strong's plucked-string synthesis (1983). |
| [VHS + CRT](docs/effects/vhs_crt.md) | An old VHS tape played on a CRT TV, modeled the way the signal goes rather than drawn on top: colors bleed to the right, grain and white specks, a band of torn lines where the tracking drifts, composite dots and rainbows, then lines that widen as they brighten, the phosphor mask and the glow of curved glass. The tracking slips on the bars, and a drop makes the TV lose vertical hold for a moment. Or show it on an LCD (smearing, its tones shifting with the viewing angle), a plasma panel (false contours on moving gradients) or e-ink (a few updates a second, ghosts, a full refresh on the bar). |
| [Video Vocoder](docs/effects/video_vocoder.md) | A vocoder for pictures: the picture split into seven octaves of detail, from its largest shapes and glow to its finest grain, each made stronger or weaker by the matching band of the music, as a vocoder does to a synthesizer with a voice. The bass pumps the big shapes, the mids sharpen the edges and the treble sparkles the fine grain. Each band is judged against its usual level, so a quiet moment softens the picture to a haze and a loud one makes it crisp and vivid. With nothing wired, the seven sliders are an equalizer for the picture's detail. |
| [Voxel Space](docs/effects/voxel_space.md) | The picture as the land of an early 1990s flight game, flown over. Its colors are the ground and its depth map the hills, so a dancer becomes a mountain range in the colors of her clothes, moving as she moves; without a depth map its bright parts stand up as peaks. Drawn as Comanche drew its landscapes in 1992, a column of the screen at a time, each nearer hill hiding what's behind it, with no geometry at all. Fly weaves low over it to the horizon, Orbit circles it as an island, Hover looks across it, and the camera can be moved, turned and zoomed on top of each. The bass lifts the hills, each beat dips the camera and the tempo sets the pace. |
| [Words](docs/effects/words.md) | The picture rebuilt from the words of a text, laid out live as they would be on a page. Cloud is a word cloud in the shape of the subject (a dancer, a hand, whatever stands in front in a depth map), its most frequent words biggest and deepest inside, riding along as it moves. Portrait fills the whole picture with the text, each word in the picture's colors, small on its features and big where it is plain. Lines writes the text in small lines that circle the subject's outline ring after ring, as micrography does. Wordle's layout, run on the GPU every frame after the papers (ShapeWordle, EdWordle, Digital Micrography), with any text and any installed font. Beats swell the words. |
| *More on the way* | New effects are in the works. Watch or star the repo to see them land. |

To try them all at once, the [Showreel](docs/effects/showreel.md) holds every effect in one
`.tox`: one after another, fading from one to the next with the music, or one by name.

Every effect reacts to music on input 2 and gets the most from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal (bars, builds, drops, sections), and
works with plain audio, TouchDesigner's audio analysis, or nothing wired. Each one's flashing is
measured against WCAG 2.3.1, and an effect that can flash has a setting to turn it off.

## Status

Twenty-five effects are done (ASCII 0.2.1, Bent Cam, Fluid and Glitch 0.1.2, Datamosh and VHS + CRT 0.2.2,
Blob Track and Point Cloud 0.1.4, Particles 0.3.3, Paint, Pixel Sort and Slit-Scan 0.1.1, Caustics, Chladni Sand,
Detail, Lens Flare, Motion Magnify, Pencil, Pixel Art, Reaction-Diffusion, Scan Processor, Temporal Resonator, Video
Vocoder, Voxel Space and Words 0.1.0), and the Showreel holds them all. All but Caustics, Scan Processor, Temporal
Resonator and Voxel Space are in the latest release,
[v0.5.0](https://github.com/kevinraymond/touchdesigner-effects/releases/tag/v0.5.0), which adds Pixel Art, Lens Flare
and Words.

- [docs/BRIEF.md](docs/BRIEF.md): what the library is for and what every effect promises.
- [docs/BUILDING.md](docs/BUILDING.md): how the `.tox` files are generated, checked and released.

## Demo footage

The previews and demo clips use test footage generated with two open models, run locally:
still images from [Krea 2](https://github.com/krea-ai/krea-2), brought to life as video with
[Wan 2.2](https://github.com/Wan-Video/Wan2.2). Thanks to both teams for releasing them. The
footage is AI-generated and shows no real people, places or brands. Krea 2's weights are
released under the [Krea 2 Community License](https://www.krea.ai/krea-2-licensing) and Wan
2.2's under [Apache 2.0](https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt); neither
claims rights over what it generates. The depth maps behind the depth effects' previews were
estimated from that footage with [Depth Anything 3](https://github.com/ByteDance-Seed/Depth-Anything-3)'s
Mono-Large model (Apache 2.0), one frame at a time, and held steady from frame to frame by fitting
each frame's scale to the one before (written for this library).

The beat the effects follow in the previews comes from "Prison of Pixels", a song by Kevin Raymond
made with [Suno](https://suno.com), licensed like the rest of the media (below). The previews are
silent, and the song isn't in this repository.

None of it ships inside an effect's `.tox`: with nothing wired in, every effect shows
TouchDesigner's own sample media. The Showreel is the one exception: it carries the 5-second dancer
clip and her depth map, so it shows motion (and depth) straight away. No `.tox` here makes sound.

## License

- Code, `.tox` files and docs: MIT; see [LICENSE](LICENSE).
- Media (the demo footage, the preview images and videos on the effect pages, and the song "Prison
  of Pixels"): [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Use them however you
  like, including commercially; credit them as "Kevin Raymond, touchdesigner-effects" with a link
  to this repo.

Each effect's page credits anything it derives from.
