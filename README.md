# TouchDesigner Effects

Before [Fosfora](https://github.com/kevinraymond/fosfora), I had never heard of TouchDesigner.
While adding the examples for Fosfora's signal mode, I got the free version of TD and poked
around it a bit. Then I decided I would create some effects based on different things I've
worked on or seen, in case they are useful for anyone. If nothing else they are examples of solid
working effects. Enjoy!

Ready-to-use TouchDesigner effects you can download and use in a minute: drag in a `.tox`
and it works, and opening it shows how it works.

Every effect is one self-contained `.tox` that works on the free Non-Commercial license:
a TOP in, a TOP out, and an optional CHOP input for audio or beat data. Inside you'll find a
README, a comment on every operator, help on every parameter, and an About page that names
the TouchDesigner build it was saved in. Each effect has a page here with a preview, a
performance note, and a download link that always points at the latest release.

## Effects

| Effect | What it does |
|---|---|
| [ASCII](docs/effects/ascii.md) | ASCII art, live: the picture redrawn in text characters, heavy ones such as `@` for bright areas and light ones such as `.` for dim ones, the way old text-only terminals drew pictures. Line characters trace the outlines, and beats swap the characters and pop the contrast. |
| [Blob Track](docs/effects/blob_track.md) | The look of computer vision: whatever moves gets a numbered box that follows it, joined to its neighbors by lines, like surveillance software or a film's targeting display. Beats scramble the labels and spawn links. |
| [Datamosh](docs/effects/datamosh.md) | Glitch art: one shot smears and melts into the next, the way a compressed video does when its keyframes (the full pictures it stores now and then) go missing. Bars set off the melts; Fosfora's builds hold them back until the drop. |
| [Glitch](docs/effects/glitch.md) | Broken digital video on the beat: every beat tears thin slivers of the picture sideways, and on the one of each bar a burst makes blocks jump, freeze or lose their colors and rows slip, then the picture is whole again. Calm by default: at most one burst a second, or none at all. |
| [Particles](docs/effects/particles.md) | Particles peel off a subject and drift away like smoke, in the picture's colors: people in a depth map (Kinect, RealSense, a depth estimator) or a mask for the best result, and with only a webcam or a video, whatever moves. Loudness thickens the stream, beats kick the cloud outward, bars swing the wind. |
| *More on the way* | New effects are in the works. Watch or star the repo to see them land. |

To try them all at once, the [Showreel](docs/effects/showreel.md) holds every effect in one
`.tox`: side by side in a grid, one after another with the music, or one by name.

Every effect reacts to music on input 2 and gets the most from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal (bars, builds, drops, sections), and
works with plain audio, TouchDesigner's audio analysis, or nothing wired. Each one's flashing is
measured against WCAG 2.3.1 and can be turned off.

## Status

Four effects are done (ASCII, Datamosh-style and Glitch 0.1.0, Blob Track 0.1.1), and the
Showreel holds them all; there is no release yet, so the download links on their pages start
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
