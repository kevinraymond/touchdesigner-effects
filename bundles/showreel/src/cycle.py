# Showreel (touchdesigner-effects, MIT): where Cycle is, as Script CHOP callbacks (the builder fills
# the CHOP's docked callbacks DAT with this). Input 1 is audio (lib audio_in: bar_count, source),
# input 2 a clock that changes every frame, so this cooks every frame it is used and never
# otherwise; the view reads it only while View is Cycle.
#
# Two channels. step: how many times Cycle has moved on. It moves on every Every bars of input 2
# while bars are arriving (one came within BARS_LAPSE bars' worth of seconds), else every Every
# times SECONDS_A_BAR seconds; and never within MIN_GAP seconds of the last move, whatever the bars
# do. fade: how far the fade from the last effect to the next has come, 0 at the move to 1 FADE
# seconds later. A fade rather than a cut: a cut from one effect to the next changes the whole
# picture's brightness at once, and on top of the effects' own flashes it took Cycle past WCAG's
# three a second at Up to 3 per second (3.5 under dev/flash.py's stress beat).
# State lives in _state, by operator id: not in storage, so nothing of a run is saved into the .tox.

SECONDS_A_BAR = 2.0   # Cycle's bar while input 2 gives none: 4 beats at 120 BPM
BARS_LAPSE = 4        # bars arriving: one came within this many SECONDS_A_BAR x Every seconds
MIN_GAP = 2.0         # seconds between two moves, at least
FADE = 1.0            # seconds the fade from one effect to the next takes (at most MIN_GAP)

_state = {}


def onSetupParameters(scriptOp):
    return


def onPulse(par):
    return


def onGetCookLevel(scriptOp):
    return CookLevel.WHEN_USED


def onCook(scriptOp):
    now = absTime.seconds
    every = max(1, int(scriptOp.parent().par.Every.eval()))
    audio = scriptOp.inputs[0] if scriptOp.inputs else None
    bars = audio['bar_count'] if audio is not None else None
    source = audio['source'] if audio is not None else None
    bar_count = int(bars.eval()) if bars is not None and source is not None and source.eval() > 0 else None
    s = _state.get(scriptOp.id)
    if s is None:
        s = _state[scriptOp.id] = dict(step=0, last=now, mark=None, bars=bar_count, bar_at=-1e9)
    if bar_count is not None and bar_count != s['bars']:
        s['bars'], s['bar_at'] = bar_count, now
    if bar_count is not None and now - s['bar_at'] < BARS_LAPSE * SECONDS_A_BAR * every:
        mark = ('bars', bar_count // every)
    else:
        mark = ('time', int(now // (SECONDS_A_BAR * every)))
    if s['mark'] is None:
        s['mark'] = mark
    elif mark != s['mark'] and now - s['last'] >= MIN_GAP:
        s['mark'], s['last'] = mark, now
        s['step'] += 1
    scriptOp.clear()
    scriptOp.numSamples = 1
    scriptOp.appendChan('step')[0] = s['step']
    scriptOp.appendChan('fade')[0] = min(1.0, (now - s['last']) / FADE) if s['step'] > 0 else 1.0
    return
