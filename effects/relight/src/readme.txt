Relight {v}: the picture lit again by colored lights that move over it, its shape from a depth map.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/relight.md

A picture already has its light baked in. To light it again you need its shape, and a depth map gives one: how near each point is. Treat the depth as a surface standing out of the picture, and each point's slope says which way it faces. A light then brightens what faces it, leaves in shadow what something nearer stands in front of, and glints where the surface mirrors it toward you. Not every surface is hard: light goes into skin, wax or marble, spreads and comes out again redder, and a thin part, a finger's edge or an ear, glows when lit from behind.

This effect does that to your picture. Its own light is flattened, then lamps sweep over it on slow paths, each casting shadows and highlights, their light spreading a little under the surface and glowing through thin parts. Each beat flares the lights and louder music brightens them. A depth map or mask on input 3 gives the shape. Without one, the picture's brighter parts bulge a little, like a relief lit across.

USE
Drag relight.tox into your network. It shows TouchDesigner's sample picture under moving lights. Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire a depth map or mask into input 3 (optional, brighter nearer) for the light to fall on its shapes. Wire music into input 2 (below) for the lights to flare on the beats. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Look picks the lights: Stage (violet, teal and amber lamps sweeping), Studio (a warm key, a cool fill and a white light from above), Sun (one low warm sun swinging round, long shadows) or Two Tone (amber from the left, blue from the right). Brightness is how bright they are, Ambient how much light reaches everything evenly, Height how high they hang (lower lights cast longer shadows), and Speed how fast they move. Relief is how far what is nearest stands out of the picture, and Roundness how far shapes round off at their edges. Flatten is how much of the picture's own light is taken out first. Shininess and Specular are the highlights' sharpness and brightness, Shadows and Softness the shadows' darkness and softness, and Occlusion how much darker creases and folds are. Scatter is how far light spreads under the surface, red furthest, and Glow how much comes through thin parts from behind. Beat Kick is how bright each beat's flare is, Loudness how much louder music brightens the lights. Depth Type says what input 3 holds, Max Distance how far a Kinect Azure's meters reach, and Bumps how far the picture's brighter parts bulge with nothing on input 3. Flashing limits the flares.

AUDIO (input 2)
Each beat of the music flares the lights, and louder music brightens them. Raw audio (Audio File In, Audio Device In) gives the beats and loudness from the sound itself. Fosfora's signal gives them from its analysis. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too. With nothing wired the lights keep moving.

FLASHING
A flare brightens the whole picture at once, so the flares go through the Flashing setting: Off never flares, Calm (the default) at most once a second, Up to 3 per second WCAG's limit. Every pixel goes through the red guard, which keeps reds just short of WCAG's saturated-red line.

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
near is input 3 as nearness at half size; near_fine smooths it finely and near_round averages it broadly with a triangle filter, and relief mixes them into the shape. With nothing on input 3, luma, luma_fine and luma_broad give the picture's brighter parts as bumps instead, and shape picks one. surface is the shape as a height field at half the picture's size, with its normals and occlusion, and shadows marches it toward each light at a quarter size, a channel a light, which shadows_soft smooths. lights is where each light is this frame and its color. surface_wide averages the surface broadly, which says how thin each part is. irradiance is the light falling on the surface and coming through thin parts; sss_h and sss_v scatter it under the surface. luma8, shade and shade_avg are the picture's own light, which show flattens before lighting the picture again with the light and the highlights. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, flash_limit and flash ration the flares, flare_env shapes them; level_pick and level_smooth are the loudness; speed and clock move the lights.

CREDITS
- Lambert's diffuse light; the GGX microfacet distribution (Walter et al., EGSR 2007) with Smith's shadowing and Schlick's Fresnel (1994) for the highlights.
- Ambient occlusion after T. Luft, C. Colditz and O. Deussen, "Image Enhancement by Unsharp Masking the Depth Buffer" (SIGGRAPH 2006), sampled, with screen-space occlusion's range check.
- Scattering: J. Jimenez et al., "Separable Subsurface Scattering" (Computer Graphics Forum 34(6), 2015), the light blurred under the surface in two one-dimensional passes, here one Gaussian a color; and J. Jimenez et al., "Real-Time Realistic Skin Translucency" (IEEE CG&A 2010), light through thin parts.
- The shadows' march starts each pixel's samples by J. Jimenez's interleaved gradient noise ("Next Generation Post Processing in Call of Duty: Advanced Warfare", SIGGRAPH 2014).
- Input 3's depth from lib depth_near.glsl; the red guard (lib red_guard.glsl) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan Processor, Voxel Space, Temporal Resonator and Caustics.
- Not used, for three active US patents (docs page, Credits and license): finding a region of the picture, such as skin by its color, to scatter or shade differently (Canon US 11,948,282 and 11,106,938), so light scatters and glows the same everywhere; shading a shadow by the highest point seen from each pixel (Adobe US 8,379,021), so a shadow multiplies the light its samples let through; and adding Gaussian blurs together (NVIDIA US 8,064,726), so the broad smoothings are triangle averages.
Everything else is written for this library. MIT.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new relight.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
