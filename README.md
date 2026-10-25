# TouchDesigner Effects

![Every effect in the library on the same clip of a dancer in a hazy warehouse, each named in the library's pixel font. On top, what goes in: the clip and its depth map. Below, what comes out: ASCII drawing her in glyphs, Blob Track boxing her moving limbs, Datamosh-style smearing her pose into the next, Glitch tearing her on the beat, Particles shedding glowing specks off her, and Point Cloud turning her and the lit wall behind her in 3D](docs/effects/showreel.webp)

*Every effect on the same clip, all in step. On top, what goes in: the clip and its depth map.*

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

Before [Fosfora](https://github.com/kevinraymond/fosfora), I had never heard of TouchDesigner.
While adding the examples for Fosfora's signal mode, I got the free version of TD and poked
around it a bit. Then I decided I would create some effects based on different things I've
worked on or seen, in case they are useful for anyone. If nothing else they are examples of solid
working effects. Enjoy!

Opening a `.tox` shows how it works. Each is a TOP in and a TOP out, with an optional CHOP input
for audio or beat data (and, for the effects that use depth, an optional depth TOP). Inside
you'll find a README with its credits, a comment on every operator, help on every parameter, and
an About page that names the TouchDesigner build it was saved in. Each effect has a page here
with a preview, a performance note, and a download link that always points at the latest release.

## Effects

| Effect | What it does |
|---|---|
| [ASCII](docs/effects/ascii.md) | ASCII art, live: the picture redrawn in text characters, heavy ones such as `@` for bright areas and light ones such as `.` for dim ones, the way old text-only terminals drew pictures. Line characters trace the outlines, and beats swap the characters and pop the contrast. |
| [Blob Track](docs/effects/blob_track.md) | The look of computer vision: whatever moves gets a numbered box that follows it, joined to its neighbors by lines, like surveillance software or a film's targeting display. Beats scramble the labels and spawn links. |
| [Datamosh](docs/effects/datamosh.md) | Glitch art: one shot smears and melts into the next, the way a compressed video does when its keyframes (the full pictures it stores now and then) go missing. Bars set off the melts; Fosfora's builds hold them back until the drop. |
| [Glitch](docs/effects/glitch.md) | Broken digital video on the beat: every beat tears thin slivers of the picture sideways, and on the one of each bar a burst makes blocks jump, freeze or lose their colors and rows slip, then the picture is whole again. Calm by default: at most one burst a second, or none at all. |
| [Particles](docs/effects/particles.md) | Particles peel off a subject and drift away like smoke, in the picture's colors: people in a depth map (Kinect, RealSense, a depth estimator) or a mask for the best result, and with only a webcam or a video, whatever moves. Loudness thickens the stream, beats kick the cloud outward, bars swing the wind. |
| [Point Cloud](docs/effects/point_cloud.md) | The picture as a cloud of points in 3D, each at its depth (a depth camera, a depth estimator, or the picture's brightness), seen from a camera that sways round it: people stand out from the wall behind them. Solid dots, glowing dots, or a surface of blended splats. Loudness swells the dots, beats deepen the cloud, bars swing the camera. |
| *More on the way* | New effects are in the works. Watch or star the repo to see them land. |

To try them all at once, the [Showreel](docs/effects/showreel.md) holds every effect in one
`.tox`: one after another, fading from one to the next with the music, or one by name.

Every effect reacts to music on input 2 and gets the most from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal (bars, builds, drops, sections), and
works with plain audio, TouchDesigner's audio analysis, or nothing wired. Each one's flashing is
measured against WCAG 2.3.1, and an effect that can flash has a setting to turn it off.

## Status

Six effects are done (ASCII, Datamosh-style, Glitch, Particles and Point Cloud 0.1.0, Blob Track
0.1.1), and the Showreel holds them all; there is no release yet, so the download links on their pages start
working with the first one.

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
Base model (Apache 2.0).

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
