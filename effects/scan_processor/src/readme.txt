Scan Processor {v}: the picture shown on a television whose raster the music bends, as the scan processors of 1969 to 1973 bent theirs.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/scan_processor.md

A television draws its picture with a beam that sweeps across the screen line by line, top to bottom, sixty times a second. Around 1970 video artists found they could bend that sweep. Nam June Paik and Shuya Abe added extra deflection coils to a black and white set and drove them from audio amplifiers and signal generators, and the picture rippled, squeezed and stretched with the sound. They called it the Wobbulator. Lee Harrison's Scanimate did it with an analog computer, twisting and bending a picture's lines like a rubber ribbon, and its pictures went through a colorizer that gave each shade of gray a color. Machines like these were called scan processors.

This effect draws the picture that way, as lines a beam draws, and lets the music bend them. One signal generator stands for each of the music's seven bands, the lowest a slow bow down the screen and the highest a fine ripple, each as loud as its band, so a kick bends the whole frame while hi-hats shiver its edges. Where the lines bunch together the light piles up, and where they spread apart the dark between them shows, as it did on the real screens.

USE
Drag scan_processor.tox into your network. It shows TouchDesigner's sample movie of mist over a lake, its raster wandering gently and struck every 2 seconds (Idle). Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and the music bends the raster. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Scan picks the machine. Wobbulator pushes each line sideways and up or down with the signal, so the picture ripples and the lines bunch into bright bands. Scanimate turns the lines about the middle like a ribbon, twisting further with the low bands, bending with the middle ones and rippling with the high ones. FM speeds and slows the beam along each line, so the picture gathers into glowing pleats where it slows. Amount is how far the music bends the raster, Speed how fast the signal generators' stripes creep up and down the screen, and Beat Kick how hard each beat strikes it (a bow, a twist or deeper pleats). Idle keeps the raster moving with nothing on input 2. Lines is how many lines the beam draws, and Beam how wide its spot is, from thin lines with dark gaps between them to lines that touch. Colors shows the picture's own colors or puts it through a colorizer, which colors each band of brightness, blue through gold, twice over from dark to light. Flashing says how often a beat may strike.

AUDIO (input 2)
The signal generators follow the music's seven bands, Fosfora's split, from the sub bass (20 to 60 Hz) through bass, low mid, mid, upper mid and presence to the brilliance (above 6000 Hz). Each band's level is smoothed over a second, with a lift when it rises above its usual level over the last 4 seconds, so the raster swells with the music and calms in quiet passages. Each beat strikes the raster as often as Flashing allows. Raw audio (Audio File In, Audio Device In) gives the bands and beats from the sound itself. Fosfora's signal gives them from its feature bus. Run `fosfora --signal --feat-bus`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too. Without Fosfora's feature bus, its bass, melody and drums stand in for the bands.

FLASHING
A strike moves the whole raster at once and back, which counts as flashing, so a beat strikes only through a gate that follows the Flashing parameter. Off never strikes, so only the smoothed bands move the raster. Calm (the default) strikes at most once a second, and Up to 3 per second is the WCAG 2.3.1 limit. Swaying a red near WCAG's saturated-red line makes it cross the line more often, so every pixel goes through the red guard, which keeps reds just short of it. The limits were measured on the output (docs page, Accessibility).

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
scan draws the raster: each line the picture averaged over its band of rows, drawn where yokes puts it as a beam's spot, adding up where lines overlap. show gives it its colors and guards its reds. yokes works out each line's push, drop, twist or pleat phase from the seven signal generators, whose phases phase carries from frame to frame (phase_fb is its last frame, phase_size its size). Input 2 goes through audio (lib audio_in): bands, bands_now and bands_usual are the seven bands, smoothed over a second and their usual level over 4 seconds; counts and steps notice a beat, idle_count and idle_steps make Idle's strikes, strike_ask takes either, flash_limit and flash let a strike through as often as Flashing allows, strike_env rings it down and strikes counts them, so each strike goes the other way from the last. levels holds each generator's level and the strike, and drive what Scanimate and FM read from them: the low, middle and high bands, the bend and FM's depth.

CREDITS
- The Wobbulator: Nam June Paik and Shuya Abe's Raster Manipulation Unit (1970), extra yokes on a black and white set driven by audio, as the Experimental Television Center documented it ("Raster Manipulation Unit: Operation and Construction", 1980, https://www.videohistoryproject.org/node/6909).
- Scanimate: Lee Harrison III and Computer Image Corporation (1969; US patents 3,700,792 and 3,747,087, expired), the raster's lines twisted, bent and rippled by an analog computer, and its colorizer; as Dave Sieg describes it in "Scanimation in the Analog Days" (SIGGRAPH Computer Graphics 32(3), 1998).
- FM: J. M. Chowning, "The Synthesis of Complex Audio Spectra by Means of Frequency Modulation" (JAES 21(7), 1973; US patent 4,018,121, expired), here modulating the beam's sweep along a line instead of a tone.
- The colorizer: Daniel Sandin's Image Processor (1971 to 1973, its plans freely distributed) and Scanimate's colorizer, which colored each band of gray.
- The seven bands: Fosfora's split (its AUDIO-FEATURES.md), measured from raw audio by the library's audio input.
- Not used: the song's own waveform laid along the raster, as a real Wobbulator fed a mix would draw it; a mix's waveform changes completely every sixtieth of a second, and held still and smoothed it read as scratchy noise on every line rather than stripes and bends (board #4744).
- The red guard (lib red_guard.glsl) is shared with VHS + CRT, Bent Cam, Motion Magnify and Slit-Scan.
Everything else is written for this library: the beam drawn as Gaussian spots that add up where lines bunch, one signal generator a band of the music, the strikes through the flash gate and the Idle wandering. MIT.

EXPERIMENTAL
The bands Fosfora's bass, melody and drums stand in for, without its feature bus, are a rough guess.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new scan_processor.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
