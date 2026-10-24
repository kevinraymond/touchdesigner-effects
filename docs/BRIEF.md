# TD Effects Library (working title)

A library of ready-to-use TouchDesigner effects that people can download and use within
a minute: drag in a .tox, it works, and opening it shows how. The goal is the answer to
"that looks great, how can I get it?", which today is usually "it's in my TD project".

## Step 1: research what's already out there (before building anything)

Survey what's publicly available for TouchDesigner, and write it up as a table:
- Sources: Derivative's own Palette and OP Snippets (they ship inside TouchDesigner),
  the Derivative community forum and shared-file posts, GitHub repos that publish .tox
  files, creators who sell or give away components (Patreon, Gumroad, personal sites),
  and tutorial channels whose project files circulate.
- For each: what it does, license, TouchDesigner version, whether it is self-contained,
  how it is documented, whether it is maintained, free or paid.
- Then the gaps: which effects people ask for that have no good, free, documented,
  drop-in version. Pick the first ten effects from those gaps, not from what's easy.

## What every effect in the library promises

- **One .tox, self-contained.** Relative references only. Nothing points outside the
  component except TouchDesigner's own /sys and /ui operators. No absolute file paths;
  bundled sample media comes from `app.samplesFolder`, never shipped. (One exception: the
  showreel bundle carries short clips of the library's own CC BY footage, the dancer and her
  depth map, since the samples barely move and have no depth. No component ever makes sound.)
- **Works the moment it's dragged in**, on the free Non-Commercial license
  (resolution cap 1280 x 1280), and states the oldest TouchDesigner build it was saved in.
  Files saved in a newer build may not open in older ones.
- **Readable inside:** a README DAT, a comment on every operator, an About page
  (Version, Built With, Open Docs), tags, a node color, and a node size saved large
  enough that the picture reads on the node.
- **Standard inputs and outputs:** TOP in, TOP out; an optional CHOP input for audio
  or beat data, so an effect can follow TouchDesigner's own audio analysis or an
  external analyzer (for example Fosfora's `fosfora_signal` channels). An effect that uses
  depth or a mask takes it as an optional third input, a grayscale TOP (brighter is nearer, or
  inside), and works without it from the picture alone. Input 2 is always the audio.
- **Parameters with help text,** sensible defaults, an Open Window button for full-size
  viewing, and a performance note (fps on a stated reference machine).
- **Accessible by default:** no signal carried by hue alone (also brightness, size or
  motion). A colorblind-safe palette such as orange and blue. Text legible at the
  size it is shown. Flashing follows WCAG 2.3.1 (never more than three flashes a second),
  defaults to calm, and can be switched off entirely.
- **Honest labels:** anything unreliable is marked experimental in its help and docs.
- **A preview** (GIF or short clip) and a one-paragraph description per effect, after a
  short plain-words intro to the technique (ASCII art, blob tracking, datamoshing) for anyone
  who has never heard of it. The README's table says it in one line.
- **A clear license** (MIT or CC0 for code), with credits for anything derived.

## How the .tox files are made (lessons from building Fosfora's TD component)

- **Generated, never hand-edited.** A builder script per component assembles it from
  plain source files (callbacks .py, shaders .glsl) and saves the .tox. Run it in the
  textport with `__file__ = '/path/build_x.py'; exec(open(__file__).read())`.
- **A manifest beside every .tox:** version, TouchDesigner build, a hash of the sources
  and a hash of the .tox. A plain-Python test (pre-commit and CI) fails when a source
  changed without a rebuild, or when a bundle embeds an older component. Break every
  guard once on purpose and watch it fail, or it guards nothing.
- **Save-time checks in the builder:** refuse to save anything pointing outside the
  component (absolute paths, external .tox, clone, global shortcut), and any unused
  docked DAT.
- **Fill docked DATs; don't add your own.** Script CHOP, OSC In DAT, GLSL TOP and Ramp TOP
  create docked DATs when created (callbacks, shaders, keys). A builder that adds its own
  leaves the docked one behind as junk inside the .tox.
- **Release automation:** CI attaches the .tox files to each GitHub release, and the docs
  link to `releases/latest/download/<name>.tox`, so the download link never goes stale.
- **A remote dev loop:** an Execute DAT in a dev project watches a `cmd.py` file and runs
  it on change, writing output to a file. Edit and copy the script from your editor or
  another machine, read the result, and save TOPs to PNG (`top.save(path)`) to look at
  frames. Keep it out of anything shipped.
- **Prototype several options live, then polish the chosen ones.** Building five rough
  versions and looking at them with real input beat describing them in text.

## TouchDesigner behaviors that silently broke things

- A COMP's own operator parameters (Geometry COMP `instanceop`, `material`) resolve among
  its siblings: `'grid'`, not `'../grid'`. To connect from a COMP, use
  `comp.outputConnectors[0]`. Wires cannot cross network levels.
- Palette .tox files wrap the real COMP one level down; copy the inner one out.
- CHOPs cook only when something reads them. A one-frame pulse can be missed, so publish
  a running count beside every pulse and let logic watch the count (CHOP Execute
  `onValueChange`). Judge "stale" in seconds, not frames: a dropped frame advances
  `absTime.frame` by several. Script CHOPs: `CookLevel.WHEN_USED`.
- Reading a CHOP twice in one Python call sees one cook; read again next frame.
- A Time COMP's frame can't be set from Python while it plays. The Beat CHOP's default
  play mode ignores the timeline. LFO and Timer CHOPs have no beat units.
- A new DMX Out CHOP starts active on Art-Net: switch it off before wiring it.
- On a Mac, TouchDesigner stops producing frames while the display sleeps; a Window COMP
  can block display sleep while open.
- Useful patterns: a Switch TOP cooks only its selected input (cheap view selectors);
  a Layout TOP tiles views; a CHOP to TOP in 32-bit float turns channels into a data
  texture for a GLSL TOP (row 0 is the first channel); numpy in a Script CHOP drives
  instancing for hundreds of instances at 60 fps; TouchDesigner 2025 renders real Gaussian
  splats (Point File In POP with splat format PLY, plus the palette's GaussianSplats
  components).

## Lessons about signals and honesty

- **Steady beats the precise for visuals.** A receiver should smooth what jumps: a bar
  that restarts mid-bar looks broken even if the analysis "corrected" itself. Let bars
  finish and follow a change only once it holds, and fix the source when you can.
- **Measure before you claim.** Record the input, replay it, count the problem, and
  re-count after the fix.
- **Label what isn't reliable.** "Drop-like (experimental)" kept trust where "drop
  detected" would have broken it.

## First milestones

1. Research table and gap list (above).
2. Repo skeleton: builders, shared save checks, manifests, the stale-file test, CI that
   attaches .tox files to releases, a docs page per effect.
3. Three effects end to end, chosen from the gaps, each with a preview and a
   performance note.
4. A bundle .tox with a View selector that shows them all, like a showreel.
