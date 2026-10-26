Paint {v}: the live picture as a painting, flat strokes that follow its edges, in oil, watercolor or ink.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/paint.md

A Kuwahara filter turns a photo into something like a painting. Around each pixel it looks at several neighborhoods
and takes the average color of the most even one, so busy texture flattens into patches of color while the edges
between patches stay sharp. The anisotropic version stretches those neighborhoods along the edges in the picture, so
the patches become strokes that follow the shapes: a cheek is painted around its curve, and grass along its blades.

This effect does that live, from the papers. It finds the direction of the edges at every pixel, paints with an
ellipse turned along them, and can draw ink lines along the edges as well. Oil lays the painting on canvas. Watercolor
washes it onto paper, broader, with darker edges and pigment that pools unevenly. Ink turns it into two tones, like a
woodcut. A depth map or mask on input 3 paints near things finely and far things broadly, and on each beat of the
music a broad stroke sweeps across the picture.

USE
Drag paint.tox into your network. It shows TouchDesigner's sample movie of a river running over rocks, painted. Wire
any TOP into input 1, and the result is on output 1 at the input's size. You can also wire audio or beat channels into
input 2 and a depth map or mask into input 3 (below). Open Window shows the picture full size, and Esc closes the
window.

THE PAGE
Style picks Oil, Watercolor or Ink. Brush is the strokes' size, their radius in pixels at 720 high (it scales with the
picture). Watercolor paints {wash:g} times broader. Sharpness says how crisply neighboring strokes meet, and Stretch
how far they stretch along the edges. Passes paints over the painting again, up to 3 times, which flattens it further.
Half Size paints at half the size, which halves the painting's cost and softens its strokes. Texture is the surface: a
canvas weave under Oil, paper and pooling pigment under Watercolor, paper under Ink. The surface stays put while the
picture moves over it, as paper would. Lines is how dark the ink lines along the edges are (Oil and Watercolor), and
Line Width how wide they are. Ink Level says how much of the picture fills with ink in Ink: at 0.5, everything darker
than the picture's average brightness. Depth Brush, Depth Type and Max Distance are input 3's (below), and Beat Kick,
Loudness, Song Moments and Length are the music's.

AUDIO (input 2, optional)
Fosfora's signal is the best input. Run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's
integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. On
each beat a broad stroke sweeps across the picture in {sweep:g} s, each beat from another direction: where it passes
the painting goes loose, the brush up to {kick:g} times its size at Beat Kick 1, and then tightens again (Oil and
Watercolor: in Ink a sweep would flip whole patches between ink and paper, which is a flash). Louder music broadens
the strokes and quiet passages refine them (Loudness). With Song Moments on, a build broadens them as it rises, and a
drop paints in broad strokes for Length seconds (Fosfora's drop detection is experimental). Raw audio (Audio File In,
Audio Device In) gives beats from a kick detector and a beat clock that locks to the kicks' tempo. That clock is
experimental and can still add or miss beats. TouchDesigner's audioAnalysis gives beats from its kick or onset
channels. With nothing wired, the brush keeps its size.

DEPTH OR MASK (input 3, optional)
A depth map, brighter nearer, makes the strokes finer near and broader far, as a painter details the subject and
sketches the background. Depth Brush says how much: at 1 the nearest strokes are half Brush and the farthest twice. A
mask, brighter inside, paints its inside finely and the rest broadly. Depth Type reads depth cameras too: the
RealSense and Kinect TOPs give distance from 0 to 1 (black where the camera got no reading, which is left out), and the
Kinect Azure TOP gives meters, scaled by Max Distance. With nothing on input 3 the brush is the same everywhere.

FLASHING
Paint doesn't flash. In Oil and Watercolor a beat's sweep only paints a band of the picture in broader strokes for a
moment, which keeps each area's colors, and the surface never changes. In Ink a sweep flipped whole patches between
ink and paper, which is a flash, so Ink doesn't sweep. Measured under a beat far busier than music (8 beats a second),
no style added more than half a flash a second to the test clips' own, so it has no Flashing setting.

PERFORMANCE
Painting costs most of the frame. The strokes are read on a grid turned with each ellipse, a few samples along its
radius, each from the mipmap level that averages the pixels between them, so a broad brush costs the same as a fine
one. Each pass costs as much as the first. Half Size paints at half the size and brings it back up along the
picture's edges, which halves the painting's cost.

INSIDE
tensor, tensor_h, tensor_v and flow (lib structure_tensor) find the direction of the edges at every pixel and how
clear it is. kuwahara1 paints: each pixel takes the evenest sectors of an ellipse turned along that direction, its
size from brush_scale (input 3 through depth and near with Depth Brush, and the beat's sweep) and swell (loudness, a
build or a drop). kuwahara2 and kuwahara3
paint over it again, and the Switch kuwahara picks the last pass asked for, so the others don't cook. upsample brings a
Half Size painting back up, and painted picks it. dog blurs the painting's brightness twice across the edges and lic
smooths both along them, and paint takes their difference for the ink lines, adds the surface and finishes the style.
mean is the picture's average color, Ink's middle level. Input 2 goes through audio (lib audio_in): counts and steps
turn its counts into steps, sweep and beat_n time each beat's band and turn its direction, drop_env shapes a drop's
broad strokes, level_smooth eases the loudness, and swell multiplies them into the brush's size.

CREDITS
- The anisotropic Kuwahara filter: J. E. Kyprianidis, H. Kang and J. Doellner, "Image and Video Abstraction by
  Anisotropic Kuwahara Filtering" (Computer Graphics Forum 28(7), Pacific Graphics 2009). The ellipse along the flow,
  its anisotropy, the 8 sectors and their weighting by standard deviation are from the paper.
- Its polynomial weights: J. E. Kyprianidis, A. Semmo, H. Kang and J. Doellner, "Anisotropic Kuwahara Filtering with
  Polynomial Weighting Functions" (EG UK Theory and Practice of Computer Graphics 2010). zeta, eta for 8 sectors and
  computing the 8 weights from two sets of 4 (its Listing 1) are from the paper.
- The structure tensor as J. E. Kyprianidis and J. Doellner use it ("Image and Video Abstraction by Multi-scale
  Anisotropic Kuwahara Filtering", NPAR 2011, 3.2): the derivative filter of B. Jaehne, H. Scharr and S. Koerkel
  ("Principles of filter design", 1999), the color tensor of S. Di Zenzo ("A note on the gradient of a multi-image",
  1986), smoothing the tensor rather than the picture (T. Brox et al. 2006), and the anisotropy of G.-Z. Yang et al.
  ("Structure adaptive anisotropic image filtering", 1996).
- The ink lines and Ink: H. Winnemoeller, J. E. Kyprianidis and S. C. Olsen, "XDoG: An eXtended Difference-of-Gaussians
  Compendium Including Advanced Image Stylization" (Computers & Graphics 36(6), 2012): the difference of Gaussians,
  the sharpened image, the soft threshold and the flow-based version, after H. Kang, S. Lee and C. K. Chui, "Coherent
  Line Drawing" (NPAR 2007). The smoothing along the edges is a line integral convolution, after B. Cabral and
  L. Leedom, "Imaging Vector Fields Using Line Integral Convolution" (SIGGRAPH 1993).
- Watercolor: A. Bousseau, M. Kaplan, J. Thollot and F. X. Sillion, "Interactive Watercolor Rendering with Temporal
  Coherence and Abstraction" (NPAR 2006): the pigment density formula, the turbulence, dispersion and paper layers,
  edge darkening by the painting's symmetric gradient, and wobbling by the paper's gradient are from the paper. The
  layers themselves are drawn here with noise, where the paper used Perlin noise, Gaussian noise and scanned paper.
- Gradient noise after K. Perlin, "Improving Noise" (SIGGRAPH 2002), on Chris Wellons' lowbias32 integer hash
  (hash-prospector, public domain).
- Half Size: joint bilateral upsampling, J. Kopf, M. F. Cohen, D. Lischinski and M. Uyttendaele, "Joint Bilateral
  Upsampling" (SIGGRAPH 2007). Mipmaps: L. Williams, "Pyramidal Parametrics" (SIGGRAPH 1983).
- Read during the survey, not used: yeataro's TD-Anisotropic-Kuwahara (GPL-3.0, unfinished) and ogrew's
  TD-PostEffectShader (MIT, a basic Kuwahara).
- Beats from raw audio (the library's audio input). A kick is a jump in the low band's loudness, and the beat clock
  takes its tempo from the gaps between kicks, each voting for the beat lengths it is a whole multiple of. That is
  inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from
  Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits from WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (reading the ellipse on a turned grid from mipmap levels, the canvas weave, the depth and the music)
is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new paint.tox from
https://github.com/kevinraymond/touchdesigner-effects/releases/latest, or point the COMP's External .tox at a
downloaded copy. The version and the build it was saved in are on the About page.
