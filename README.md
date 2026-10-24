# TouchDesigner Effects

Before [Fosfora](https://github.com/kevinraymond/fosfora), I had never heard of TouchDesigner.
While adding the examples for Fosfora's signal mode, I got the free version of TD and poked
around it a bit. Then I decided I would create some effects based on different things I've
worked on, in case they are useful for anyone. If nothing else they are examples of solid
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

Every effect reacts to music on input 2 and gets the most from
[Fosfora](https://github.com/kevinraymond/fosfora)'s signal (bars, builds, drops, sections), and
works with plain audio, TouchDesigner's audio analysis, or nothing wired. Each one's flashing is
measured against WCAG 2.3.1 and can be turned off.

## Status

Version 0.1.0 of the first three effects is done; there is no release yet, so the download links
on their pages start working with the first one.

- [docs/BRIEF.md](docs/BRIEF.md): what the library is for and what every effect promises.
- [docs/BUILDING.md](docs/BUILDING.md): how the `.tox` files are generated, checked and released.

## Demo footage

The previews and demo clips use test footage generated with two open models, run locally:
still images from [Krea 2](https://github.com/krea-ai/krea-2), brought to life as video with
[Wan 2.2](https://github.com/Wan-Video/Wan2.2). Thanks to both teams for releasing them. The
footage is AI-generated and shows no real people, places or brands. Krea 2's weights are
released under the [Krea 2 Community License](https://www.krea.ai/krea-2-licensing) and Wan
2.2's under [Apache 2.0](https://github.com/Wan-Video/Wan2.2/blob/main/LICENSE.txt); neither
claims rights over what it generates.

None of it ships inside a `.tox`: with nothing wired in, every effect shows TouchDesigner's own
sample media.

## License

- Code, `.tox` files and docs: MIT; see [LICENSE](LICENSE).
- Media (the demo footage, and the preview images and videos on the effect pages):
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Use them however you like, including
  commercially; credit them as "Kevin Raymond, touchdesigner-effects" with a link to this repo.

Each effect's page credits anything it derives from.
