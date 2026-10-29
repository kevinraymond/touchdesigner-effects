Caustics {v}: the picture as the floor of a pool under moving water, lit by the bright lines of light its waves focus.
touchdesigner-effects, MIT.
Docs: https://github.com/kevinraymond/touchdesigner-effects/blob/main/docs/effects/caustics.md

Sunlight through rippling water lights the floor of a pool in a moving net of bright lines. Each wave is a weak lens. Where the surface curves like a magnifying glass it gathers the light into a line, and where it curves the other way it spreads it thin. Those lines are called caustics. In 2009 Cem Yuksel and John Keyser showed how to compute them fast for water whose surface is a height field over a flat floor. Every point of the floor gathers the light from the patch of surface above it, each bit of surface bending its light down through its own slope.

This effect makes your picture the floor of such a pool. The water rolls in slow swells, whatever moves in the picture pushes it into wakes, and each beat drops a raindrop into it. The floor is seen through the moving surface, lit by the caustics, and colored by the water on the way, deeper water bluer. A depth map on input 3 makes the water shallower over what is nearer.

USE
Drag caustics.tox into your network. It shows TouchDesigner's sample movie of grass swaying in front of a building, under rolling water. Wire any TOP into input 1, and the result is on output 1 at the input's size. Wire music into input 2 (below) and each beat drops into the water. Wire a depth map or mask into input 3 (optional, brighter nearer) and the water is shallower over what is nearer. Open Window shows the picture full size, and Esc closes the window.

THE PAGE
Depth is how deep the water is. The waves focus the light sharpest about Depth 1. Shallower water lights the floor more evenly, and deeper water crosses the lines into a busier net, bends the view further and colors it more. Waves is how high the waves are, Wind how fast the swells roll, and Size how long they are, which is the size of the caustics' net (longer swells are steeper too, so they still focus at the same depth). Caustics is how much of the focused light shows, Rainbow how far its colors split, Refraction how far the waves bend the view, and Water Color how much the water colors the floor. Wake is how hard what moves pushes the water, Beat Kick how big each beat's raindrop is, and Loudness how much louder music raises the waves. Depth Type says what input 3 holds, and Max Distance how far a Kinect Azure's meters reach.

AUDIO (input 2)
Each beat of the music drops a raindrop into the water, somewhere new each time, and its rings spread across the pool. Louder music raises the waves. Raw audio (Audio File In, Audio Device In) gives the beats and loudness from the sound itself. Fosfora's signal gives them from its analysis. Drag fosfora_signal.tox (in Fosfora's integrations/touchdesigner/, https://github.com/kevinraymond/fosfora) into your project and wire it into input 2. TouchDesigner's audioAnalysis works too. With nothing wired the swells roll and what moves makes wakes.

FLASHING
Caustics are bright lines that move, and on a bright floor every line that passes a spot is a change between light and dark there. Short, steep ripples focus the light hardest, so the water is kept to broad swells and broad wakes, which the flash test measured at the clip's own flashes (docs page, Accessibility). Every pixel goes through the red guard, which keeps reds just short of WCAG's saturated-red line.

PERFORMANCE
About {perf} ms on the GPU a frame at 1280 x 720 on an M2 Pro (docs page, Performance).

INSIDE
water is the water's surface at a quarter of the picture's size, the damped wave equation stepped once a frame (water_fb is its last frame). push is how the picture changed since its last frame (lib optical_flow's luma), and push_blur spreads it into broad wakes. surface adds the swells to the water at half the picture's size and gives its height, slope and the water's depth (near, input 3 as nearness, softened by near_soft, makes it shallower over what is nearer). caustics, a compute shader, gathers the light the surface focuses onto the floor, a 16 x 16 patch at a time, and light softens it by about a pixel. show is the floor seen through the surface, lit by the caustics, colored by the depth, the sun glinting. Input 2 goes through audio (lib audio_in): counts and steps notice a beat, drop_env pours its drop for a tenth of a second and drops counts them, which says where each falls; level_pick and level_smooth are the loudness; wind_rate and wind are the swells' clock.

CREDITS
- C. Yuksel and J. Keyser, "Fast Real-time Caustics from Height Fields" (The Visual Computer 25, 2009): the caustics gathered from the surface above each point of the floor, a one-pixel square of light from each surface sample.
- The water's wave equation as Evan Wallace's WebGL Water steps it (https://github.com/evanw/webgl-water, MIT, Copyright 2011 Evan Wallace); none of its rendering is used.
- The color the water takes with depth: Beer-Lambert absorption, red first.
- What moves comes from the library's optical flow input (lib optical_flow: its luma and its cut detection), and input 3's depth from lib depth_near.glsl.
- The red guard (lib red_guard.glsl) is shared with VHS + CRT, Bent Cam, Motion Magnify, Slit-Scan, Scan Processor, Voxel Space and Temporal Resonator.
Everything else is written for this library: the picture as the pool's floor, the swells, the wakes and the drops on the beat, the gather done a patch at a time in shared memory. MIT.

EXPERIMENTAL
The cut that keeps a new shot from slamming the water is found from how much the picture changes at once, a guess that a very fast pan can fool.

UPDATING
Dragging a .tox in embeds a copy. To update, delete this one and drag in the new caustics.tox from https://github.com/kevinraymond/touchdesigner-effects/releases/latest (or point the COMP's External .tox at a downloaded copy). The version and the build it was saved in are on the About page.
