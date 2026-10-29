# Film Stock

![Four views of a dancer in a hazy warehouse lit by a stage light, each named in the library's pixel font. INPUT is the clip. 16 MM shows her on color negative film: fine grain over the haze, the stage lamp with a faint warm glow, the frame nudging in the gate. SUPER 8 is far grainier and softer, the lamp's glow wider, the picture wandering further. BLACK AND WHITE 400 shows her in gray, the haze a field of grain](film_stock.webp)

*Film Stock on the dancer, the clip top left, with a song on input 2: at its defaults (Color Negative 500T on 16 mm),
on Super 8, and as Black and White 400 on 16 mm. Each beat kicks the film in the gate.*

**New to film?** Film records light as grains. A frame of film carries layers of light-sensitive crystals, and where
light falls the crystals develop into specks of silver, or into little clouds of dye in color film, more of them where
more light fell. So a photograph is made of specks, and the specks are the grain. How big the grain looks on screen
depends on how far the frame is blown up: a Super 8 frame is a quarter the height of a 35 mm one, so its grain comes
out four times as large. Film is never quite still in the camera's or the projector's gate either, so the picture
weaves, and the projector's lamp and shutter don't give the same light every frame, so it flickers. Bright lights glow
red where light bounces off the back of the film into its lowest layer (halation, which some films let through on
purpose). Prints pick up dust and scratches. And the frames step along at 24 a second. Together these are the look
that "film emulation" plug-ins sell to colorists.

This effect models those things from how the film works, rather than laying a noise texture over the picture. Each
layer of the film answers the light by its characteristic curve, and its density is made of grains: for every pixel
the number of developed grains is drawn from its Poisson law, with the grain's size set from the stock's published
granularity, and once the grains are big enough to see, each one is drawn in its place. Then the negative is printed,
or the reversal film shown, with the dyes' impurities and the stock's character. Gauge sets how much film a pixel
covers, so 16 mm and Super 8 are grainier, softer, weave further and halate wider on screen, as they do. Day for
Night turns daylight footage into a night scene the way a cinematographer's blue filter and underexposure did, with
the eye's loss of detail at night added after a paper on it. On the music, each beat kicks the film in the gate,
louder passages push the grain, a drop splices the reel and a section change shows a cue mark. The free film looks I
found for TouchDesigner lay a static Noise TOP over the picture; the paid ones are overlays too, or scanned grain
plates at a fixed size. Nothing simulates the grain.

![Up close, at 1:1: the dancer's arm and the haze as Black and White 400 on Super 8 with the grain at three times the
stock's, the haze a field of clumped specks a pixel or two across, and the clip on 35 mm color negative, its grain fine
and almost even](film_stock_grain.webp)

*Up close, one pixel to one: Black and White 400 on Super 8 with Grain 3, where each grain is drawn one by one, and
Color Negative 500T on 35 mm at Grain 1.*

**[Download film_stock.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/film_stock.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free Non-Commercial license

## Use it

1. Drag `film_stock.tox` into your network. It shows TouchDesigner's sample movie (mist over a lake) on 16 mm color
   negative straight away: grainy, stepping at 24 frames a second, weaving a little.
2. Wire any TOP into input 1. The result is on output 1, at the input's size. Footage with a bright lamp or window in
   it shows the halation.
3. Optional: wire audio or beat channels into input 2 (see Audio input). Each beat then kicks the film in the gate.

Open Window (on the effect's page) shows it full size; Esc closes the window.

To update, delete your copy and drag in the new `film_stock.tox`. Dragging a `.tox` in embeds a copy, so a new
release doesn't reach it on its own. You can also point the COMP's External .tox at a downloaded file.

## Parameters

The Film Stock page, top to bottom.

| Parameter | Default | What it does |
|---|---|---|
| Stock | Color Negative 500T | The film. Color Negative 500T: a modern tungsten negative, fine grain, warm skin. Color Negative 50D: the finest and sharpest, a daylight negative. Vintage Color Negative: a 1970s negative, coarser, softer, warmer, more halation, tamer colors. Color Reversal: a slide film, contrasty and saturated. Black and White 400: a classic fast panchromatic negative. Black and White 100: a modern tabular-grain negative, very fine. See [The stocks](#the-stocks). |
| Gauge | 16 mm | The film's size: 35 mm, 16 mm or Super 8. A smaller frame is blown up further, so its grain is bigger on screen, its picture softer, its weave wider and its halation broader. |
| Exposure | 0 | Stops over (+) or under (-) exposed, -3 to 3. |
| Contrast | 1 | The print's contrast, 0.5 to 1.5 (1: a cinema print's). |
| Saturation | 1 | The colors' saturation, 0 to 2, on top of the stock's own. |
| Grain | 1 | The grain's size, as a multiple of the stock's own (1: as measured on the real film; 0: none), up to 3. |
| Halation | 0.3 | How much light bounces off the back of the film into the red layer around bright things, 0-1, a red glow. Each stock's anti-halation backing scales it; 1 is a film without one. |
| Weave | 0.4 | How far the film wanders in the gate, 0-1: a slow drift and a jitter frame to frame, a few micrometers on the film, so further on screen for a smaller Gauge. |
| Flicker | 0.3 | How much the projector's light breathes and varies frame to frame, 0-1: never more than 5% of the light. |
| Dirt | 0.2 | How much dust, hair and how many scratches the print carries, 0-1: specks and hairs come and go each frame, scratches run for a second or two. |
| Frame Rate | 24 fps | Hold each frame as film does: 24 a second, 18 (Super 8), 16 (silent 16 mm), or follow the source as it comes. The grain, weave and flicker change once a film frame either way. |
| Day for Night | 0 | Turn the scene into a night scene, 0-1, as cinematographers shot night by day: dim, blue, the colors gone but for what is lit, fine detail lost without looking blurred. |
| Beat Kick | 0.5 | How far each beat on input 2 kicks the film in the gate (a jump down, settling back), 0-1. Flashing limits how often. |
| Loudness | 0.5 | How much louder music on input 2 pushes the grain coarser, 0-1. |
| Song Moments | On | With Fosfora's signal on input 2: a drop splices the reel (the frame line rolls through and the picture settles) and a section change shows a cue mark. Fosfora's drop detection is experimental. |
| Flashing | Calm | How often a kick or a splice may come. Off: never. Calm: at most once a second. Up to 3 per second: the WCAG 2.3.1 limit, which no setting exceeds. |
| Open Window | | Shows the picture in its own window, 1280 x 720 or filling a display. Esc closes it. |
| Full Screen | Off | Opens the window filling the whole display, for a projector or a second screen. |
| Display | 0 | Which display the window opens on; 0 is the primary display. |

The About page has Version, Built With (the TouchDesigner build it was saved in) and Open Docs.

## The stocks

![The six stocks on the dancer, each named: 500T and 50D close to the clip with fine grain, VINTAGE warmer and softer
with a glow round the lamp, REVERSAL contrasty and saturated, BLACK AND WHITE 400 grainy gray, BLACK AND WHITE 100
smooth gray](film_stock_stocks.webp)

*The six stocks on 16 mm, each recorded on its own and tiled.*

Each stock is a small table: its characteristic curve (the slope at which density grows with log exposure, where the
fog and the shoulder are), its grain (each layer's mean grain radius in micrometers and how widely the radii spread),
its resolving power (how soft it is), how much it halates, its dyes' impurity and saturation, and a tint for its
shadows and one for its highlights. The grain and the sharpness come from published figures where Kodak publishes
them: the diffuse rms granularity of Tri-X 400 (17), T-Max 100 (8) and T-Max 400 (10), read at a density of 1.0
through a 48 micrometer aperture, and Vision3 500T's granularity curves (about 11 for its red and green layers and
20 for the blue), with Nutting's formula turning a granularity into the area of the grain that makes it, and the
resolving powers from the same data sheets. The other stocks are set by eye relative to those, and every stock's
colors and curves are this library's, shaped by eye after the look of its kind of film. The names say what kind of
film each is, not which product.

## How it works

Each frame is held for a 24th of a second (Frame Rate), since film steps where video glides. The film weaves in the
gate: a slow drift of up to 20 micrometers plus a jitter of a few micrometers from frame to frame, at Weave 1, which
is a pixel or two on 16 mm at 720 high and four times that on Super 8. The picture is resampled with Catmull-Rom, so
sub-pixel movement neither blurs nor rings, and comes out in linear light as the exposure, Exposure stops over or
under.

The film's own softness comes first: a Gaussian whose width follows the stock's resolving power and the Gauge (a
stock resolving 100 lines a millimeter is sharp on 35 mm and soft on Super 8). What is brighter than white bounces off
the base and exposes the red layer most, the green a little, the blue least, as far around as the base is thick, about
a tenth of a millimeter on the film: halation, a warm glow around lamps and windows. Video clips lamps at white, so
what rises past the knee counts for more the nearer it is to white.

Then each layer of the emulsion (one in black and white, three in color: red, green and blue light each expose their
own) turns its exposure into density by an S curve in log exposure, the characteristic curve: fog at the bottom, a
straight part at the stock's gamma (about 0.6 for a negative), a shoulder at the top. A reversal stock's curve runs
the other way and steeper. Density is grains. Developed grains are opaque disks scattered at random, the Boolean
model of stochastic geometry as Newson, Delon and Galerne used it for film grain, thick enough that a point is covered
with the probability the density says. For each pixel the number of grains it holds is drawn from the Poisson law,
and that number's wobble is the grain: the pixel's coverage is what that many grains of the stock's size cover. When
the grains are bigger than a third of a pixel, each is drawn where it falls with its own log-normal radius, and the
pixel's coverage by it is the area where the two meet, the pixel taken as a disk of the same area; the union of the
grains is one minus the product of what each leaves uncovered. Both give the model's mean exactly and its spread
within about 15%, checked against the model rasterized (`dev/protos/film_stock/grain_check.py`). The grain's size
on the film comes from the stock's granularity, and on screen from the Gauge: how many micrometers of film a pixel
holds. The paper this effect was planned from, by Zhang, Wang, Tian and Pappas, derives the model's variance and
correlation and renders the grain as noise shaped to them; that method is patented, so here the model is simulated
instead (see Credits and license).

The negative is read a little soft, as a scanner reads it, and softer in color than in brightness, as scanners and
prints are, so the grain is mostly a brightness grain with color in its larger clumps. A negative is then printed on a
print stock with a steep curve (its gamma about 2.8 against the negative's 0.6, so the system's contrast comes out
about 1.7, as cinema prints do), dense negative to bright screen; a reversal is shown as it is. The dyes aren't pure
(cyan absorbs some green and blue, magenta some blue), so each channel's density mixes a little of the others', which
tames the colors as film does. The stock's tints and saturation, and Contrast and Saturation, work on the log of the
light. Last, the screen: the flicker (a slow breathing and a frame-to-frame unevenness, never over 5%), the dirt
(specks and hairs that land on one frame, white where the dirt was on the negative when it was printed, black where
it is on the print; scratches that run down the picture for a second or two, light where the base is scratched and
dark where the emulsion is), the cue mark, the red guard and sRGB.

Day for Night follows Thompson, Shirley and Ferwerda. The scene's scotopic luminance (how bright it is to the rods,
which favor blue) is computed by Larson, Rushmeier and Piatko's formula, dimmed two and a half stops and colored a
bluish gray; what is bright enough for the cones (a lamp, a lit window) keeps its own color. Then the night image is
blurred to take the fine detail out, and the edges that remain are sharpened by raising the band between a fine blur
and a wider one to the power 1/1.25, which steepens it at its zero crossings, where the edges are, so the picture loses
detail without looking blurred. The wider blur here is a triangle rather than the paper's second Gaussian.

## Audio input

**[Fosfora](https://github.com/kevinraymond/fosfora)** gives the most. Run `fosfora --signal`, drag
`fosfora_signal.tox` (in Fosfora's `integrations/touchdesigner/`) into your project, and wire it into input 2. Each
beat kicks the film in the gate (Beat Kick: a jump down, settling back over 0.3 s), louder passages push the grain
coarser (Loudness), and with Song Moments on:

- **Drops:** a drop splices the reel: the frame line rolls through, the picture dropping a tenth of its height and
  settling back over 0.2 s, through the same Flashing gate as every kick. Fosfora's drop detection is experimental.
- **Sections:** a section change shows the cue mark, the circle at the top right that warned the projectionist of a
  reel's end, for four frames.

**Any input:** kicks on its beats, and loudness pushes the grain. Raw audio (an Audio File In or Audio Device In CHOP)
gives beats from a kick detector and a beat clock that locks to the kicks' tempo (experimental: it can still add or
miss beats) and its loudness from the sound. TouchDesigner's audioAnalysis gives beats from its kick or onset
channels.

**Nothing wired:** the film runs on its own, weaving, flickering and gathering dirt, with no kicks.

## Performance

60 fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, 16 GB, macOS 15.6, TouchDesigner
2025.33230), with default parameters. Each frame took 2.3 ms on the GPU (95th percentile 3.0 ms) and 0.4 ms on the CPU, the median of three runs
with the Mac otherwise idle. The print's two reads of the negative (about 1 ms) and the negative itself (about 0.7 ms,
the grain) are the largest parts. Big grain costs more, since each grain is drawn one by one: on Super 8 at Grain 3,
about 6 ms for Color Negative 500T or Black and White 400 and about 13 ms for Vintage Color Negative, whose three
layers are all coarse enough, still at 60 fps. Day for Night adds about 1.4 ms. Nothing inside cooks while the output is
unused.

## Accessibility

- **Flashing.** A beat's kick and a splice move the whole picture at once, so both go through one gate that follows
  the Flashing setting: Off never kicks or splices, Calm (the default) allows at most one a second, and Up to 3 per
  second is the WCAG 2.3.1 limit, which no setting exceeds. After the gate, a budget keeps this effect to about 2 a
  second even at Up to 3. A kick is one jump and one settle, and a splice one roll and one settle.
- **Flicker.** The flicker never swings the light more than 5%, under the 10% change WCAG counts, so it is never a
  flash at any setting.
- **Grain and dirt.** Grain changes every frame, as it does on film, but it is fine and evens out over any area WCAG
  counts. Dirt is specks and hairs, far under WCAG's area.
- **Red.** Halation is a red glow, so every pixel goes through the red guard, which keeps reds just short of WCAG's
  saturated-red line.
- **No meaning in color.** Nothing is signaled by hue; the stocks differ in grain and contrast as well as in color.

The flash rates were measured, not assumed. The test recorded the output while it fed a beat far busier than music
(8 beats, 2 bars and 1 drop a second), and counted the flashes in the worst second by WCAG's area rule, and WCAG's red
flashes separately:

| Clip | Off | Calm | Up to 3 per second | The clip alone |
|---|---|---|---|---|
| Dancer in a hazy warehouse | 1.0 | 1.0 | 1.0 | 1.0 |
| Red flowers against the sky | 0.5, red 0 | 0.5, red 0 | 1.5, red 0 | 1.0, red 1.0 |
| Koi in a black pond | 0.5, red 0 | | | 0.5, red 1.5 |

Off adds nothing to any clip, and Calm at most a flash a second; Up to 3 per second stays well under WCAG's 3. The
kicks move the picture less than a cell of the test's grid, so they barely register; the red guard took every red
flash out, the clips' own included.

## Experimental

- Drop moments depend on Fosfora's drop detection, which is experimental.
- Beats from raw audio come from a kick detector and a beat clock that locks to the kicks' tempo. It takes a few
  beats to lock and can still add or miss beats where the kicks don't keep the beat; Fosfora or audioAnalysis give
  steadier beats.

## Credits and license

MIT. The shaders and operators are written for this library, the simulation of the grain, the stocks' tables, the
gate, the print and the screen among them.

- **The grain:** the Boolean model of stochastic geometry (G. Matheron, "Elements pour une theorie des milieux
  poreux", 1967; J. Serra, "Image Analysis and Mathematical Morphology", 1982) as A. Newson, J. Delon and B. Galerne
  used it for film grain, ["A Stochastic Film Grain Model for Resolution-Independent Rendering"](https://doi.org/10.1111/cgf.13159)
  (Computer Graphics Forum 36(8), 2017) and, with N. Faraj,
  ["Realistic Film Grain Rendering"](https://doi.org/10.5201/ipol.2017.192) (Image Processing On Line 7, 2017):
  grains as disks whose centers fall as a Poisson process with a density set by the pixel's gray level, with
  log-normal radii. Followed, not copied: the simulation here draws the count of grains in each pixel, or each grain,
  rather than their Monte Carlo sample of points.
- **The grain's size from granularity:** P. G. Nutting, "On the absorption of light in heterogeneous media"
  (Philosophical Magazine 26, 1913), the random-dot model's formula, with the diffuse rms granularity Kodak publishes
  for Tri-X 400 (17), T-Max 100 (8) and T-Max 400 (10) in its data sheets F-4017 and F-4016, and Vision3 500T's
  granularity curves (H-1-5219), and the resolving powers from the same sheets. Kodak's names are used here only to
  say which published figures the stocks follow.
- **The curves:** F. Hurter and V. C. Driffield, "Photochemical Investigations and a New Method of Determination of
  the Sensitiveness of Photographic Plates" (Journal of the Society of Chemical Industry, 1890); the negative-print
  system's contrast as cinema practice has it.
- **Day for Night:** W. B. Thompson, P. Shirley and J. A. Ferwerda,
  ["A Spatial Post-Processing Algorithm for Images of Night Scenes"](https://doi.org/10.1080/10867651.2002.10487550)
  (Journal of Graphics Tools 7(1), 2002); the scotopic luminance by G. W. Larson, H. Rushmeier and C. Piatko, "A
  Visibility Matching Tone Reproduction Operator for High Dynamic Range Scenes" (IEEE TVCG 3(4), 1997). The wider
  blur here is a triangle, not the paper's second Gaussian.
- **Halation, gate weave, flicker, cadence, dust and scratches:** the physics as the film literature describes them,
  written for this library; the cue mark is the projectionist's circle of the reel-change system.
- **Film's frame heights:** SMPTE 59 (35 mm camera aperture 22.05 x 16.03 mm), SMPTE 7 (16 mm, 10.26 x 7.49 mm) and
  SMPTE 154 (Super 8, 5.79 x 4.01 mm).
- **Dice:** Chris Wellons' lowbias32 integer hash ([hash-prospector](https://github.com/skeeto/hash-prospector),
  public domain); Catmull-Rom resampling and the red guard from this library's `lib/glsl`.
- **Not used, for active US patents.** The method of K. Zhang, J. Wang, D. Tian and T. N. Pappas,
  ["Film Grain Rendering and Parameter Estimation"](https://doi.org/10.1145/3592127) (ACM Transactions on Graphics
  42(4), 2023), which derives the Boolean model's variance and correlation and synthesizes the grain as noise with
  those statistics, is Northwestern University's [US 12,705,810](https://patents.google.com/patent/US12705810B2)
  (granted 2026, active to about 2044): nothing here derives the grain's statistics or shapes noise to them; the model
  is simulated. Netflix's [US 10,839,489](https://patents.google.com/patent/US10839489B2) (AV1's film grain) scales
  unit noise by a function of the picture's brightness: no noise is scaled anywhere here. Autodesk's
  [US 7,873,210](https://patents.google.com/patent/US7873210B2) measures grain from a reference image's tiles: the
  stocks come from published figures instead. And no two Gaussian blurs are combined (NVIDIA's US 8,064,726, as in
  Relight).
- **Seen during the survey, not used:** Vintage Lens Effect Tool, FilmFilter, Pao Olea's grain, BCC Film Damage,
  Filmbox, Dehancer.
- **Beats from raw audio** (the library's audio input, `lib/audio_callbacks.py`): inter-onset-interval tempo
  induction after S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (Journal of New
  Music Research, 2001). Followed, not copied: written for this library.
- **Flash limits:** [WCAG 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html),
  measured with this library's tools (`dev/flash.py`, `dev/flashcount.py`).

Preview footage: Kevin Raymond, touchdesigner-effects,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It is AI-generated (see the
[repository README](../../README.md#demo-footage)) and shows no real person.
