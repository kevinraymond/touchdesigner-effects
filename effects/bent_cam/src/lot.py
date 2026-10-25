"""Bent Cam (touchdesigner-effects, MIT): the lot of cameras, the one table their shorts come from. The builder
writes it into bus.glsl and the README DAT, and dev/protos/bent_cam/lot.py draws it for the docs page.

Each camera has SHORTS shorts, connected in this order as Shorts goes from 0 to 1. A short is (how, a, b): data
line Da grounded (how 0, it reads 0), tied to power (1, it reads 1), or bridged to Db so both read the lower
(2) or the higher (3) of the two. a is one of D4 to D7, the lines whose faults show; b is any other line. The
table is drawn with the lowbias32 hash below, the same on every build, so a camera stays the same camera.
"""

CAMERAS = 50
SHORTS = 6
GROUND, POWER, LOW, HIGH = 0, 1, 2, 3
M = 0xFFFFFFFF


def _ihash(x):
    """Chris Wellons' lowbias32 (hash-prospector, public domain), as lib/glsl/common.glsl has it."""
    x &= M
    x ^= x >> 16
    x = (x * 0x7feb352d) & M
    x ^= x >> 15
    x = (x * 0x846ca68b) & M
    x ^= x >> 16
    return x


def lot():
    """[camera 1's shorts, camera 2's, ...], each a list of SHORTS (how, a, b)."""
    cams = []
    for cam in range(1, CAMERAS + 1):
        shorts = []
        for i in range(SHORTS):
            h = _ihash((cam * 0x632BE5AB + i * 0x85157AF5) & M)
            a = 4 + h % 4
            b = (h >> 4) % 7
            if b >= a:
                b += 1
            shorts.append(((h >> 8) & 3, a, b))
        cams.append(shorts)
    return cams


def describe(short):
    """One short in words: 'D7 grounded', 'D6 bridged to D4 (low wins)'."""
    how, a, b = short
    if how == GROUND:
        return 'D{} grounded'.format(a)
    if how == POWER:
        return 'D{} to power'.format(a)
    return 'D{} bridged to D{} ({} wins)'.format(a, b, 'low' if how == LOW else 'high')


def glsl_table():
    """The table as GLSL: const ivec3 LOT[CAMERAS x SHORTS], camera by camera, and the two counts."""
    rows = []
    for shorts in lot():
        rows.append(', '.join('ivec3({}, {}, {})'.format(*s) for s in shorts))
    return ('#define CAMERAS {}\n#define SHORTS {}\nconst ivec3 LOT[{}] = ivec3[{}](\n    {});\n'.format(
        CAMERAS, SHORTS, CAMERAS * SHORTS, CAMERAS * SHORTS, ',\n    '.join(rows)))


def readme_table():
    """The lot for the README DAT: one line a camera, its shorts in the order Shorts connects them."""
    return '\n'.join('{:>2}: {}.'.format(i + 1, '; '.join(describe(s) for s in shorts))
                     for i, shorts in enumerate(lot()))
