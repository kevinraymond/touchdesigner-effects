# touchdesigner-effects (MIT), Words: the text as words, for two Script DATs that cook only when the text, the font,
# the case or the layout changes, never every frame.
#   words  (input: the text) every distinct word once: where the atlas Text TOP draws it (x its left edge, y its
#          baseline from the bottom, at the font size fpx it picks so they all fit 1280 x 1280), its width, the font's
#          ascender and descender there, how often it comes in the text, and its rank (most frequent first, ties by
#          first appearance; -1 for a common word when Skip Common Words is on).
#   order  (inputs: the text, words) the words the layout takes in turn, as indices into words, in rows of 1024 down
#          four columns: the ranks in order for Cloud, the text as written for Portrait and Lines.
# Words are what lies between spaces, with ASCII punctuation trimmed from their ends; a word keeps the case it is
# written in unless Case says otherwise. The Text TOP draws whole words, so its shaping (joined scripts,
# right-to-left) survives. measure, a Text TOP nothing draws, gives the sizes (evalTextSize, ascender, descender).

ATLAS = 1280        # the atlas is ATLAS x ATLAS
PAD = 3             # pixels around each word in the atlas
REF = 100.0         # measure draws at this size; sizes scale with the font size
MAX_WORDS = 1024    # distinct words the atlas and the layout take
MAX_TOKENS = 4096   # words of the text the layout reads (4 x 1024)
TRIM = '.,;:!?"()[]{}<>*_`\'~|/\\'
COMMON = set('''a about after all also am an and any are as at be been but by can could did do does down for from
had has have he her him his how i if in into is it its just like me more my no not now of off on one only or our out
over she so some than that the their them then there these they this those to too under up upon us was we were what
when where which while who whom why will with would yet you your'''.split())


def tokens(text, case):
    out = []
    for raw in text.split():
        w = raw.strip(TRIM)
        if not w:
            continue
        if case == 'upper':
            w = w.upper()
        elif case == 'lower':
            w = w.lower()
        out.append(w)
    return out[:MAX_TOKENS]


def vocabulary(toks, skip_common):
    """The distinct words in order of first appearance (compared without case), each with its count and rank."""
    index, words, count = {}, [], []
    for w in toks:
        k = w.lower()
        if k not in index:
            if len(words) >= MAX_WORDS:
                continue
            index[k] = len(words)
            words.append(w)
            count.append(0)
        count[index[k]] += 1
    ranked = [i for i in range(len(words)) if not (skip_common and words[i].lower() in COMMON)]
    ranked.sort(key=lambda i: (-count[i], i))
    rank = [-1] * len(words)
    for r, i in enumerate(ranked):
        rank[i] = r
    return index, words, count, rank, ranked


def text_of(dat):
    if dat is None:
        return ''
    if dat.isTable:
        return ' '.join(c.val for row in dat.rows() for c in row)
    return dat.text


def pack(sizes, asc, desc, fpx):
    """Shelf-pack the words at font size fpx: their (x, baseline y) in the atlas, or None if they don't fit."""
    k = fpx / REF
    line = (asc + desc) * k + 2 * PAD
    x, top, places = 0.0, float(ATLAS), []
    for w in sizes:
        ww = w * k + 2 * PAD
        if ww > ATLAS:
            return None
        if x + ww > ATLAS:
            x, top = 0.0, top - line
        if top - line < 0:
            return None
        places.append((x + PAD, top - PAD - asc * k))
        x += ww
    return places


def onCook(scriptOp):
    scriptOp.clear()
    comp = scriptOp.parent()
    case = comp.par.Case.eval()
    skip = comp.par.Skipcommon.eval()
    comp.par.Font.eval(), comp.par.Bold.eval()          # read here so a change cooks this again
    toks = tokens(text_of(scriptOp.inputs[0] if scriptOp.inputs else None), case)
    index, words, count, rank, ranked = vocabulary(toks, skip)
    if scriptOp.name == 'order':
        layout = comp.par.Layout.eval()
        seq = ranked if layout == 'cloud' else [index[w.lower()] for w in toks if w.lower() in index]
        scriptOp.appendRow(['c0', 'c1', 'c2', 'c3'])
        for r in range(1024):
            scriptOp.appendRow([seq[c * 1024 + r] if c * 1024 + r < len(seq) else -1 for c in range(4)])
        return
    m = scriptOp.parent().op('measure')
    sizes = [m.evalTextSize(w)[0] for w in words]
    asc, desc = abs(m.ascender), abs(m.descender)
    fpx, places = 128.0, None
    while fpx >= 8:
        places = pack(sizes, asc, desc, fpx)
        if places is not None:
            break
        fpx = float(int(fpx * 0.9))
    k = fpx / REF
    scriptOp.appendRow(['text', 'x', 'y', 'w', 'asc', 'desc', 'count', 'rank', 'fpx'])
    for i, w in enumerate(words):
        if places is None or i >= len(places):
            break
        x, y = places[i]
        scriptOp.appendRow([w, round(x, 2), round(y, 2), round(sizes[i] * k, 2), round(asc * k, 2),
                            round(desc * k, 2), count[i], rank[i], fpx])
    if scriptOp.numRows == 1:                  # no words: one blank, so every texture made from this has a pixel
        scriptOp.appendRow([' ', 0, 0, 0, 0, 0, 0, -1, fpx])
