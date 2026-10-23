"""A 5 x 7 bitmap font drawn for this library, shared by every effect that draws text in a
shader (labels, glyph grids). Glyphs live in the shader as constants, so an effect needs no font
file and draws the same pixels on Mac and Windows. Merged from the round-1 blob-track and ASCII
prototypes (dev/protos/blob, dev/protos/ascii), each drawn row by row in the usual 5 x 7
dot-matrix forms; no font file was copied or traced.

A builder loads it with lib_module(_ROOT, 'font5x7') and pastes glsl_font() into a shader:

    float glyph(int g, ivec2 p)   1.0 where glyph g lights pixel p (x 0..4 left to right, y 0..6 top down)

index(ch) gives a character's glyph number for the shader, glsl_ints() a constant array of them,
ramp() orders characters by how much they light (darkest first) for density ramps.
"""

# Each glyph: 7 rows of 5, top row first; '#' lit, '.' unlit.
GLYPHS = {
    ' ': '..... ..... ..... ..... ..... ..... .....',
    '.': '..... ..... ..... ..... ..... .##.. .##..',
    ',': '..... ..... ..... ..... .##.. ..#.. .#...',
    "'": '..#.. ..#.. .#... ..... ..... ..... .....',
    '`': '.#... ..#.. ..... ..... ..... ..... .....',
    ':': '..... .##.. .##.. ..... .##.. .##.. .....',
    ';': '..... .##.. .##.. ..... .##.. ..#.. .#...',
    '-': '..... ..... ..... ##### ..... ..... .....',
    '_': '..... ..... ..... ..... ..... ..... #####',
    '~': '..... ..... .#... #.#.# ...#. ..... .....',
    '^': '..#.. .#.#. #...# ..... ..... ..... .....',
    '"': '.#.#. .#.#. .#.#. ..... ..... ..... .....',
    '=': '..... ..... ##### ..... ##### ..... .....',
    '+': '..... ..#.. ..#.. ##### ..#.. ..#.. .....',
    '*': '..... ..#.. #.#.# .###. #.#.# ..#.. .....',
    '|': '..#.. ..#.. ..#.. ..#.. ..#.. ..#.. ..#..',
    '/': '....# ...#. ...#. ..#.. .#... .#... #....',
    '\\': '#.... .#... .#... ..#.. ...#. ...#. ....#',
    '<': '...#. ..#.. .#... #.... .#... ..#.. ...#.',
    '>': '.#... ..#.. ...#. ....# ...#. ..#.. .#...',
    '(': '...#. ..#.. .#... .#... .#... ..#.. ...#.',
    ')': '.#... ..#.. ...#. ...#. ...#. ..#.. .#...',
    '[': '.###. .#... .#... .#... .#... .#... .###.',
    ']': '.###. ...#. ...#. ...#. ...#. ...#. .###.',
    '!': '..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..',
    '?': '.###. #...# ....# ...#. ..#.. ..... ..#..',
    'o': '..... ..... .###. #...# #...# .###. .....',
    'x': '..... ..... #...# .#.#. ..#.. .#.#. #...#',
    '#': '.#.#. .#.#. ##### .#.#. ##### .#.#. .#.#.',
    '%': '##... ##..# ...#. ..#.. .#... #..## ...##',
    '&': '.##.. #..#. #.#.. .#... #.#.# #..#. .##.#',
    '$': '..#.. .#### #.#.. .###. ..#.# ####. ..#..',
    '@': '.###. #...# #.### #.#.# #.### #.... .###.',
    '0': '.###. #...# #..## #.#.# ##..# #...# .###.',
    '1': '..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.',
    '2': '.###. #...# ....# ...#. ..#.. .#... #####',
    '3': '##### ...#. ..#.. ...#. ....# #...# .###.',
    '4': '...#. ..##. .#.#. #..#. ##### ...#. ...#.',
    '5': '##### #.... ####. ....# ....# #...# .###.',
    '6': '..##. .#... #.... ####. #...# #...# .###.',
    '7': '##### ....# ...#. ..#.. .#... .#... .#...',
    '8': '.###. #...# #...# .###. #...# #...# .###.',
    '9': '.###. #...# #...# .#### ....# ...#. .##..',
    'A': '.###. #...# #...# ##### #...# #...# #...#',
    'B': '####. #...# #...# ####. #...# #...# ####.',
    'C': '.###. #...# #.... #.... #.... #...# .###.',
    'D': '###.. #..#. #...# #...# #...# #..#. ###..',
    'E': '##### #.... #.... ####. #.... #.... #####',
    'F': '##### #.... #.... ####. #.... #.... #....',
    'G': '.###. #...# #.... #.### #...# #...# .####',
    'H': '#...# #...# #...# ##### #...# #...# #...#',
    'I': '.###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.',
    'J': '..### ...#. ...#. ...#. ...#. #..#. .##..',
    'K': '#...# #..#. #.#.. ##... #.#.. #..#. #...#',
    'L': '#.... #.... #.... #.... #.... #.... #####',
    'M': '#...# ##.## #.#.# #.#.# #...# #...# #...#',
    'N': '#...# #...# ##..# #.#.# #..## #...# #...#',
    'O': '.###. #...# #...# #...# #...# #...# .###.',
    'P': '####. #...# #...# ####. #.... #.... #....',
    'Q': '.###. #...# #...# #...# #.#.# #..#. .##.#',
    'R': '####. #...# #...# ####. #.#.. #..#. #...#',
    'S': '.#### #.... #.... .###. ....# ....# ####.',
    'T': '##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..',
    'U': '#...# #...# #...# #...# #...# #...# .###.',
    'V': '#...# #...# #...# #...# #...# .#.#. ..#..',
    'W': '#...# #...# #...# #.#.# #.#.# #.#.# .#.#.',
    'X': '#...# #...# .#.#. ..#.. .#.#. #...# #...#',
    'Y': '#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..',
    'Z': '##### ....# ...#. ..#.. .#... #.... #####',
}
ORDER = list(GLYPHS)


def _bits(rows):
    rows = rows.split()
    assert len(rows) == 7 and all(len(r) == 5 for r in rows), rows
    return [c == '#' for r in rows for c in r]


def coverage(ch):
    """How many of the 35 pixels the glyph lights."""
    return sum(_bits(GLYPHS[ch]))


def index(ch):
    return ORDER.index(ch)


def codes(text):
    return [index(c) for c in text]


def ramp(chars):
    """The glyphs in chars, darkest first (fewest lit pixels; ties keep their order)."""
    return ''.join(sorted(chars, key=coverage))


def glsl_font():
    words = []
    for ch in ORDER:
        b = _bits(GLYPHS[ch])
        lo = sum(1 << i for i in range(32) if b[i])
        hi = sum(1 << (i - 32) for i in range(32, 35) if b[i])
        words.append('uvec2({}u, {}u)'.format(lo, hi))
    return ('// 5 x 7 bitmap font drawn for touchdesigner-effects (lib/font5x7.py), MIT.\n'
            '#define FONT_N {n}\n'
            'const uvec2 FONT[FONT_N] = uvec2[](\n    {w});\n'
            '// 1.0 where glyph g lights pixel p (x 0..4 left to right, y 0..6 top to bottom).\n'
            'float glyph(int g, ivec2 p) {{\n'
            '    if (p.x < 0 || p.x > 4 || p.y < 0 || p.y > 6) return 0.0;\n'
            '    int i = p.y * 5 + p.x;\n'
            '    uvec2 w = FONT[clamp(g, 0, FONT_N - 1)];\n'
            '    uint bit = i < 32 ? (w.x >> uint(i)) & 1u : (w.y >> uint(i - 32)) & 1u;\n'
            '    return float(bit);\n'
            '}}\n').format(n=len(words), w=',\n    '.join(words))


def glsl_ints(name, chars):
    """const int name[] = the glyph numbers of chars, in order."""
    return 'const int {}[{}] = int[]({});\n'.format(name, len(chars), ', '.join(str(index(c)) for c in chars))
