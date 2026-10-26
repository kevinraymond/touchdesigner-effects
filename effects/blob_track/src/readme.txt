Blob Track {v}: a tracking overlay. touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/blob_track.md

Blob tracking is one of the basic tricks of computer vision: software finds the patches of a picture that stand out, usually whatever moves, and follows each one from frame to frame. Drawn as numbered boxes, it gives the look of surveillance software or a targeting display in a film.

This effect finds what moves in the picture and draws a thin box around each thing, a number above it and its position below in a 5 x 7 pixel font, and lines to its nearest neighbors. Boxes glide, show once a thing has lasted a moment, fade out when it is gone, and stay with it when the detector loses it for a moment, splits it or merges it: a box coasts on and picks its thing up again. Max Count limits the boxes showing; once it is reached, new things wait for room. Audio on input 2 makes the overlay move with the music.

USE
Drag blob_track.tox into your network: it shows TouchDesigner's sample movie (grass in the wind) straight away. Wire any TOP into input 1; the result is on output 1, at the input's size. Optionally wire audio or beat channels into input 2 (below). Open Window shows it full size; Esc closes the window. Movement works best with a still camera: when the camera moves, everything moves.

WHAT GETS A BOX (top of the page)
Detector: TouchDesigner's Blob Track TOP (the default; more than 2 blobs on the free Non-Commercial license needs TouchDesigner 2025.32820 or later), or the GPU Grid: cheaper, nothing read back to the CPU, its boxes snapped to grid cells. Track: Movement (light or dark, against a background a second or two behind), Stand Out (brighter or darker than its surroundings, also on stills), Bright Areas or Dark Areas. Threshold, Merge, Min Size, Max Size, Max Count and Smoothing tune it: raise Threshold or Min Size when textured footage (leaves, water) gets boxes everywhere, and Max Count for crowds.

THE LOOK (middle of the page)
Picture (Gray, Original, Dimmed), Inside (None, Invert, Threshold, Zoom), Labels (Off, ID, ID and Position, Words), Links (Off, Nearest, Two Nearest), Line Width, Label Size and Accent (Orange, Blue, White). The numbers count the boxes in the order they appear.

AUDIO (input 2, optional)
Fosfora's signal is the best input: run `fosfora --signal`, drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. With Song Moments on: on Fosfora's downbeats the numbers turn to words and back, every other bar; a build adds the 3rd and 4th nearest links and brightens them; a drop turns the whole picture over once (a flash, through Flashing) and shows the four nearest links of every box; a new section makes every box lock on again. Fosfora's drop detection is experimental. Any input: on each beat a quarter of the labels scramble and settle (Scramble Labels), a quarter of the boxes reach for a random partner (Spawn Links) and the box insides turn over (Fill Boxes, a flash); loudness brightens the links. Raw audio (Audio File In, Audio Device In) gives beats from a kick detector and a beat clock that locks to the kicks' tempo (experimental: it can still add or miss beats) and a bar every 4 beats; TouchDesigner's audioAnalysis gives beats from its kick or onset channels. Nothing wired: no beat behaviors, and the overlay still tracks.

FLASHING
Fill Boxes and the drop's turn-over are flashes. They pass one gate that follows the Flashing parameter (Off never flashes; Calm, the default, at most once a second; Up to 3 per second is the WCAG 2.3.1 limit) and then a budget that keeps this effect to about 2 a second even at Up to 3. The overlay doesn't flicker on its own: a blob gets a box only once it has lasted 0.4 s, a lost box coasts on for 0.5 s before it fades, boxes fade in and out, and labels are drawn light enough not to flash as they come, go and move.

INSIDE
source -> small (gray, 320 x 180) -> state (the frame and a background, slow where things move, quick where the picture has gone still) -> mask -> merge -> blobs (Blob Track TOP) -> blob_info -> blob_cap -> blob_data -> bt_clean -> bt_pick; or grid -> grid_peaks -> grid_pick (GPU Grid); detector picks one. track follows each blob in 64 slots, shows at most Max Count of them and keeps a lost box coasting (match lets a box take over the blob that replaced its own, overlapping or close by), table packs the boxes with their nearest neighbors, tiles lists the boxes near each tile, and draw draws everything. Input 2 goes through audio (lib audio_in); counts and steps turn its counts into steps, beat_env, bar_env and moment_env shape them, and flash_limit, flash, flash_budget and flash_env gate and shape the flashes.

CREDITS
- The look follows the blob-tracking overlays that spread on social video from 2024: boxes, numbers and lines over whatever moves. No project's files or code were used.
- Detection: TouchDesigner's own Blob Track TOP (Derivative), or the GPU Grid.
- Scramble dice: Chris Wellons' lowbias32 integer hash (hash-prospector, public domain).
- Labels: a 5x7 pixel font drawn for this library.
- Beats from raw audio (the library's audio input): a kick is a jump in the low band's loudness; the beat clock takes its tempo from the gaps between kicks, each voting for the beat lengths it is a whole multiple of: inter-onset-interval tempo induction, the idea behind S. Dixon, "Automatic Extraction of Tempo and Beat from Expressive Performances" (J. New Music Research, 2001). Followed, not copied.
- Flash limits: WCAG 2.3.1 (W3C, Three Flashes or Below Threshold), measured with this library's tools.
Everything else (the GPU Grid, the tracking, the flash budget) is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new blob_track.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
