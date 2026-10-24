<!-- Copy to docs/effects/<name>.md. tests/check_tox.py requires the download link below and
     a preview that exists beside this page (dev/clips.py --preview makes the .webp). Delete this comment. -->

# Effect name

![Effect name: what the preview shows](name.webp)

**New to <technique>?** A few sentences for someone who has never heard of it: what it is, how
it works in plain words (explain any term you can't avoid), and where they may have seen it.

One paragraph: what this effect does, what it is good for, what makes it different from the
nearest thing in the Palette or elsewhere.

**[Download name.tox](https://github.com/kevinraymond/touchdesigner-effects/releases/latest/download/name.tox)**
· saved in TouchDesigner 2025.33230 (older builds may not open it) · works on the free
Non-Commercial license

## Use it

1. Drag `name.tox` into your network. It shows a sample picture straight away.
2. Wire any TOP into input 1. The result is on output 1.
3. Optional: wire audio or beat channels into input 2 (see Audio input).
4. (Effects with `depth=True` only.) Optional: wire a depth map or mask into input 3, grayscale,
   brighter nearer (or inside). Without it, the effect uses ... (say what stands in).

Open Window (on the effect's page) shows it full size; Esc closes the window.

## Parameters

| Parameter | Default | What it does |
|---|---|---|
| Amount | 0.5 | ... |

## Audio input

Lead with [Fosfora](https://github.com/kevinraymond/fosfora): wire `fosfora_signal` into input 2,
and what its bars, builds, drops and sections add. Then what plain audio or TouchDesigner's
audio analysis drives (the channels from docs/BUILDING.md, The audio input), and what the effect
does with nothing wired (it must still work).

## Performance

N fps at 1280 x 720 on the reference machine (MacBook Pro, Apple M2 Pro, TouchDesigner
2025.33230), with default parameters. Which parameters cost the most.

## Accessibility

How it carries meaning without relying on hue alone (brightness, size, motion); its palette.
If it can flash: the Flashing parameter (Off / Calm, the default / Up to 3 per second, the
WCAG 2.3.1 limit) and the measured flash rate at each setting.

## Experimental

Anything unreliable, said plainly. Delete this section if there is nothing.

## Credits and license

MIT. Derived from / inspired by: ... (with links and their licenses).
