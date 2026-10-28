# Scan Processor

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. WOBBULATOR draws her in fine scan lines and ripples them sideways with the music, so her legs and the edge of the haze wave like a flag. SCANIMATE twists the picture like a ribbon about the middle, so it narrows into a lens shape on black with rippled edges, her legs waving. FM gathers the haze's light into bright zigzag pleats that run down the picture like light through rippled glass](scan_processor.webp)

*The three scans at their defaults on the dancer, the clip top left, with a song on input 2. The raster swells with the
music, and each beat strikes it, at most once a second (Flashing at Calm).*

**New to scan processors?** A television drew its picture with a beam of electrons that swept across the screen in
lines, top to bottom, sixty times a second, steered by coils around the tube called yokes. Around 1970 video artists
found they could steer it themselves. Nam June Paik and Shuya Abe added extra yokes to a black and white set and drove
them from audio amplifiers and signal generators, and the picture rippled, squeezed and stretched with the sound. They
called it the Wobbulator. Lee Harrison's Scanimate bent a picture's lines with an analog computer, twisting it like a rubber ribbon,
and colored the result band by band. It made much of the moving television graphics of the 1970s. Machines like these
were called scan processors.

This effect shows the picture as such a screen would, drawn in lines by a beam, each line as tall as the beam's spot,
the light piling up where lines bunch together and the dark between them showing where they spread. The music bends
it. One signal generator stands for each of the music's seven bands, each a wave of its own number of cycles down the
screen, the sub bass a slow bow and the brilliance a fine shiver, each as strong as its band, creeping up or down as
a tone a little off the screen's rate did. Three scans use them differently. The Wobbulator pushes the lines sideways
and up and down, the Scanimate twists the picture about its middle, bends and ripples it, and FM speeds and slows the
beam along each line so the light gathers into glowing pleats. Each beat strikes the raster. With nothing on input 2
the generators wander by themselves. I found Rutt-Etra style scan-line effects for TouchDesigner, which lift each line
by the picture's brightness, but nothing that bends the raster with the music as these machines did.

**[Download scan_processor.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/scan_processor.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `scan_processor.tox` into your network. It shows TouchDesigner's sample movie of mist over a lake, its raster
   wandering gently and struck every 2 seconds (Idle).
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Faces and figures with clear outlines
   show the bending best.
3. Wire music into input 2 (see Audio input). The raster then follows the music's bands, and the beats strike it.

Open Window (on the effect's page) shows it full size, and Esc closes the window.

To update, delete your copy and drag in the new `scan_processor.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Scan Processor page holds, top to bottom, the scan and the music, the raster, the colors, Flashing and the window.

| Parameter | Default | What it does |
|---|---|---|
| Scan | Wobbulator | Which scan processor bends the raster. Wobbulator (Paik and Abe, 1970) pushes each line sideways and up or down with the music, so the picture ripples and the lines bunch into bright bands. Scanimate (Harrison, 1969) turns the lines about the middle like a ribbon, twisting further with the low bands, bending with the middle ones and rippling with the high ones. FM (after Chowning, 1973) speeds and slows the beam along each line, so the picture gathers into glowing pleats. See [The scans](#the-scans). |
| Amount | 0.5 | How far the music bends the raster, 0 to 1. |
| Speed | 1 | How fast the signal generators' stripes creep up and down the screen, 0 to 2, faster while their bands are loud. 0 holds them still. |
| Beat Kick | 0.5 | How hard each beat on input 2 strikes the raster, 0 to 1. The Wobbulator bows it, the Scanimate twists it and FM deepens its pleats. Each strike goes the other way from the last and rings down over a third of a second, as often as Flashing allows. |
| Idle | 0.5 | With nothing on input 2, the signal generators wander at this level and the raster is struck every 2 seconds, so you can see what music would do, 0 to 1. At 0 it rests. |
| Lines | 240 | How many lines the beam draws down the picture, 60 to 720, whatever the picture's size. Fewer shows the raster more. |
| Beam | 0.7 | How wide the beam's spot is, as a share of the space between lines, 0.2 to 1. Thin lines have dark gaps between them, and at 1 the lines touch. |
| Colors | Picture | Picture keeps the picture's own colors. Colorizer gives each band of brightness a color, dark blue through teal, gray and orange to gold, twice over from dark to light, each pixel keeping its brightness, as the scan processors colored their black and white pictures. The bands slide through the tones with the low bands and slowly over time. |
| Flashing | Calm | How often a beat may strike. Off never strikes, so only the smoothed bands move the raster. Calm strikes at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit, which no setting exceeds. See [Accessibility](#accessibility). |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on. 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The scans

![Four views of a laughing woman's face against black, each named in the library's pixel font. INPUT is the clip. WOBBULATOR draws her face in fine scan lines rippled sideways, so its outline and her teeth wave. COLORIZER is the same rippled face in bands of blue and gold that follow its brightness, sliding over it as the music plays. 96 LINES draws it in a few thick lines with dark gaps between, like an old television seen up close](scan_processor_looks.webp)

*The Wobbulator on a laughing face with the song, at its defaults, through the Colorizer, and with Lines 96 and Beam
0.45.*

The picture is scanned in Lines lines, and each line carries the picture averaged over its band of rows. The beam draws
each line where the yokes put it, as a soft spot as tall as Beam times the space between lines, and a pixel adds up
every line whose spot reaches it. A CRT's beam spends the same energy on every line, so where the lines bunch together
the light piles up into bright bands, and where they spread apart the dark between them shows. Along a line it is the
same. Where the beam slows, the line glows brighter.

The signal that bends the raster is the sum of seven signal generators, one for each band of the music. Each is a sine
wave of its own number of cycles down the picture, half a cycle (a bow) for the sub bass, then 1, 2, 3, 5, 8 and 13 for
the brilliance. Each is as strong as its band, and each creeps up or down the picture at its own rate, the higher bands
faster and in turn up and down, faster still while their band is loud. So a kick bends the whole frame while hi-hats
make its edges shiver.

- **Wobbulator.** Each line is pushed sideways by the signal, the way Paik and Abe's horizontal yoke pushed it. The
  vertical yoke moves each line down or up by the same generators a quarter cycle on, each divided by its cycles, so
  the low bands move the lines most and they bunch and spread in broad bands of light. A line never moves more than
  six tenths of a line's spacing against its neighbor, so lines never cross. Lines crossing over each other streaked
  the picture like a venetian blind. A beat bows the whole raster to one side.
- **Scanimate.** Each line is turned about the middle of the picture, more for lines further from the middle, so the
  picture twists like a ribbon, narrowing into a lens shape on black. Turned past a quarter turn, a line shows the
  ribbon's back, mirrored and a little darker. The low bands twist it further, the middle bands bend every line into a
  curve that dips or lifts at the sides, and the high bands ripple the lines sideways. A beat twists it further for a
  moment. A narrowed line glows brighter, up to twice, since its light is squeezed into less width.
- **FM.** The beam's sweep along each line is frequency-modulated, as Chowning modulated one tone with another. It runs
  faster and slower in turn, seven times across the picture, so the picture is squeezed into pleats where the beam slows
  and stretched between them. The pleats glow, their light up to four times the picture's, eased toward white. The
  signal shifts each line's pleats, so they zigzag down the picture with the music, and the music's level deepens them.
  The beam never runs backward, which would fold the picture over itself.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** sends the seven bands from its feature bus. Run `fosfora
--signal --feat-bus`, drag `fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and
wire it into input 2. Its beats strike the raster. Without the feature bus, its bass, melody and drums stand in for the
bands. **Raw audio** (an Audio File In or Audio Device In CHOP) gives the bands and the beats from the sound itself.
**TouchDesigner's audioAnalysis** gives beats from its kick or onset channels and the bands from its low, mid and high
levels.

Each generator's level is its band smoothed over a second, lifted further while the band sits above its usual level
(its average over the last 4 seconds), so the raster swells as the music builds and calms in quiet passages. Each beat
strikes the raster as often as Flashing allows (once a second at Calm), and a strike rings down over a third of a
second.

**Nothing wired:** the generators wander by themselves at Idle's level, each rising and falling over 5 to 17 seconds,
and Idle strikes the raster every 2 seconds. At Idle 0 the picture rests, drawn in its lines.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 0.89 ms on the GPU (95th percentile 1.3 ms) and 0.35 ms on the
CPU, the median of three runs with the Mac otherwise idle. Almost all of it is drawing the raster, whose cost grows with
how many lines can reach a pixel. The Scanimate took 0.41 ms and FM 0.73 ms, and 720 lines with the Wobbulator 1.8 ms.
The generators and the yokes take about 0.2 ms, one small pass each. With raw audio on input 2, measuring the bands
raises the CPU time by about 0.3 ms. GPU times on this Mac wander from run to run as its GPU changes speed. Nothing
inside cooks while the output is unused.

## Accessibility

- **Flashing.** A strike moves the whole raster at once and back over a third of a second, which counts as flashing,
  so a beat strikes only through the standard flash gate, as does Idle. Off never strikes, and only the bands,
  smoothed over a second, move the raster. Calm (the default) strikes at most once a second, and Up to 3 per second is
  WCAG 2.3.1's limit.
- **The red guard.** Swaying a red that sits near WCAG's saturated-red line makes it cross the line more often, as
  [Motion Magnify](motion_magnify.md) found. The red flowers measured 2 red flashes a second while the Wobbulator swayed
  them, where the clip alone has 1. Every pixel the effect shows goes through the red guard, which keeps reds just short
  of the line.
- **No meaning in color.** The effect signals nothing by hue. The Colorizer keeps each pixel's brightness and takes its
  hue from the band of brightness it falls in, dark blue through orange and gold, so it reads in grayscale too.

The flash rates were measured, not assumed. The test recorded the output under a beat far busier than music (8 beats,
2 bars and 1 drop a second, every band swinging fully on and off 8 times a second), a dance beat at 140 BPM whose bands
pulse as drums would, a song as raw audio, or no music (Idle), and counted the flashes in the worst second by WCAG's
area rule, and WCAG's red flashes separately:

| Clip and settings | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.5 | 2.0 | 1.0 |
| People crossing a plaza | 0.5 | 0.5 | 1.5 | 0.5 |
| Red flowers against the sky | 1.0, red 0 | 2.0, red 0 | 2.5, red 0 | 1.0, red 1.0 |
| Koi in a black pond | 1.0, red 0 | 1.0, red 0 | 2.0, red 0 | 0.5, red 1.5 |
| A laughing face | 0.5 | 1.0 | 2.0 | 0.5 |
| Walkers with lanterns at night | 0 | 0 | 0 | 0 |
| Dancer, Scanimate | 1.0 | 1.0 | 2.0 | 1.0 |
| Dancer, FM | 1.5 | 1.0 | 1.0 | 1.0 |
| Flowers, Scanimate | 1.0, red 0 | 2.0, red 0 | 3.0, red 0 | 1.0, red 1.0 |
| Flowers, FM | 1.5, red 0 | 1.0, red 0 | 1.0, red 0 | 1.0, red 1.0 |
| Flowers, Colorizer | 1.0, red 0 | 2.0, red 0 | 2.5, red 0 | 1.0, red 1.0 |
| Dancer, a dance beat (140 BPM) | 1.0 | 1.5 | 2.0 | 1.0 |
| Flowers, 140 BPM | 1.0, red 0 | 1.5, red 0 | 2.5, red 0 | 1.0, red 1.0 |
| Dancer, a song | 1.0 | 1.5 | 2.0 | 1.0 |
| Flowers, a song | 1.0, red 0 | 1.5, red 0 | 2.5, red 0 | 1.0, red 1.0 |
| Dancer, no music (Idle) | 1.0 | 1.0 | 1.0 | 1.0 |
| Flowers, Amount 1, Beat Kick 1, Speed 2 | 1.5, red 0 | 2.0, red 0 | 3.0, red 0 | 1.0, red 1.0 |
| Dancer, FM, Amount 1, Beat Kick 1 | 1.5 | 1.5 | 1.5 | 1.0 |

Every row keeps its setting's promise. Off adds nothing to the clip's own beyond the measurement's half-flash margin,
Calm adds at most one a second, and nothing passes WCAG's 3. The red guard took every red flash out, the clips' own
included. FM with Flashing Off sits at that margin on both clips, since its pleats are bright and the bands
deepening them move their ridges a little. Rows that name no Scan are the Wobbulator, the default. The last two rows
are far corners of the ranges, the hardest bending and striking and the fastest generators. With no music, Idle strikes
every 2 seconds at Calm and Up to 3 per second alike, and not at all at Off, and none of it adds a flash to the
dancer's own.

## Experimental

- Without Fosfora's feature bus, the bands its bass, melody and drums stand in for are a rough guess, so the raster
  follows the music more loosely.

## Credits and license

MIT. The shaders and operators are written for this library, including the beam drawn as spots that add up where
lines bunch, one signal generator a band of the music, the fold guard on the vertical yoke, the strikes through the
flash gate and Idle.

- **The Wobbulator:** Nam June Paik and Shuya Abe's Raster Manipulation Unit (1970), extra yokes on a black and white
  set driven by audio amplifiers and signal generators, as the Experimental Television Center documented it in
  ["Raster Manipulation Unit: Operation and Construction"](https://www.videohistoryproject.org/node/6909) (1980).
- **Scanimate:** Lee Harrison III and Computer Image Corporation (1969; US patents 3,700,792 and 3,747,087, expired),
  whose analog computer twisted, bent and rippled the raster's lines and whose colorizer colored each band of gray; as
  Dave Sieg describes it in "Scanimation in the Analog Days" (SIGGRAPH Computer Graphics 32(3), 1998).
- **FM:** J. M. Chowning, "The Synthesis of Complex Audio Spectra by Means of Frequency Modulation" (Journal of the
  Audio Engineering Society 21(7), 1973; US patent 4,018,121, expired), here modulating the beam's sweep along a line
  instead of a tone.
- **The Colorizer:** Daniel Sandin's Image Processor (1971 to 1973, its plans freely distributed) and Scanimate's
  colorizer, both of which colored a picture by its bands of gray.
- **The seven bands:** Fosfora's split (its `AUDIO-FEATURES.md`), measured from raw audio by the library's audio input
  (`lib/audio_callbacks.py`).
- **The red guard** (`lib/glsl/red_guard.glsl`) is shared with VHS + CRT, Bent Cam, Motion Magnify and Slit-Scan.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).
- **Scan-line effects before this one:** the Rutt/Etra Scan Processor (Steve Rutt and Bill Etra, 1973) lifted each line
  by the picture's brightness, and TouchDesigner versions of it exist (a [forum
  component](https://forum.derivative.ca/t/rutt-etra-shader-component/7233) of 2015 and
  [interactiveimmersivehq/rutt-etra-TouchDesigner](https://github.com/interactiveimmersivehq/rutt-etra-TouchDesigner)).
  This effect doesn't do that and was written from the Wobbulator's and Scanimate's descriptions.

**Patents.** A search of US patents (October 2026) found none on bending a picture's raster or scan lines with audio.
The machines it follows are from 1969 to 1973, and their patents have long expired. Creative Technology's US 6,369,822,
on starting a deformation when the audio's energy rises sharply, expired in 2019. Apple's US 9,466,127, active, claims
switching an effect between full and reduced quality by the processing power at hand, which this effect never does.

**Not used:** the song's own waveform laid along the raster, as a real Wobbulator fed a mix would draw it. A mix's
waveform changes completely every sixtieth of a second, and held still like an oscilloscope's trace and smoothed, it
read as scratchy noise on every line rather than stripes and bends, and added a flash a second. Also tried and set
aside were an extra yoke that follows the moving subject, which looked like the plain Wobbulator at viewing size, and
Chebyshev waveshaping of the picture's brightness (Le Brun, 1979), which lifted the darks into a lavender fog.

Preview footage: Kevin Raymond, touchdesigner-effects, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
is AI-generated (see the [repository README](../../README.md#demo-footage)) and shows no real person.
