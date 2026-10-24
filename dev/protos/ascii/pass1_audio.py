"""DEV ONLY. ASCII pass 1: the beat layer, on repeatable inputs made here in TDLIB_PARENT.

    TD_PARENT=/tdlib_dev_ascii dev/td.sh dev/protos/ascii/pass1_audio.py
    TD_PARENT=/tdlib_dev_ascii dev/td.sh --pull dev/out/ascii/audio/done

Copies of TDLIB_PARENT/ascii on the dancer clip, each with its own input 2:
  song   a Fosfora-shaped CHOP: beat_count 2/s, bar_count 0.5/s, beat_phase, bar_phase, energy,
         build ramping over 8 s, a drop and a section change every 8 s (as dev/selftest.py shapes it)
  mp3    TouchDesigner's sample MP3 (raw audio)
  wcag   the song with Pop On Beats and Flashing Up to 3 per second
For 16 s it logs, every frame, the flash gate and envelopes, counts the flashes that pass the gate
and the shortest gap between two, saves frames at pop peaks and drops, and sums cook times.
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(_ROOT, 'dev', 'out', 'ascii', 'audio')
CLIP = os.path.join(_ROOT, 'private', 'assets', 'ready', 'b1_dancer.mp4')
SECONDS = 16

host = op(TDLIB_PARENT)
fx = host.op('ascii')
for o in list(host.children):
    if o.name.startswith(('t_', 's_')) or (o.name.startswith('ascii_') and o.name != 'ascii'):
        o.destroy()
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))


def make(kind, name, x, y, **pars):
    o = host.create(kind, name)
    o.nodeX, o.nodeY = x, y
    for k, v in pars.items():
        setattr(o.par, k, v)
    return o


clip = make(moviefileinTOP, 't_clip', -1200, -900, file=CLIP)
parts = []
for i, (chan, hz, phase) in enumerate((('beat_count', 2, 0), ('bar_count', 0.5, 0), ('boundary_count', 0.125, 0.5),
                                       ('drop_count', 0.125, 0))):
    lfo = make(lfoCHOP, 's_lfo_' + chan, -1200, -1100 - 100 * i, wavetype='square', frequency=hz, offset=0.5,
               amp=0.5, phase=phase)
    cnt = make(countCHOP, 's_count_' + chan, -1000, -1100 - 100 * i)
    cnt.inputConnectors[0].connect(lfo)
    ren = make(renameCHOP, 's_name_' + chan, -800, -1100 - 100 * i, renamefrom='*', renameto=chan)
    ren.inputConnectors[0].connect(cnt)
    parts.append(ren)
for i, (chan, wave, hz, off, amp) in enumerate((('build', 'ramp', 0.125, 0.5, 0.5), ('beat_phase', 'ramp', 2, 0.5, 0.5),
                                                ('energy', 'sin', 2, 0.5, 0.35))):
    lfo = make(lfoCHOP, 's_lfo_' + chan, -1200, -1600 - 100 * i, wavetype=wave, frequency=hz, offset=off, amp=amp)
    ren = make(renameCHOP, 's_name_' + chan, -800, -1600 - 100 * i, renamefrom='*', renameto=chan)
    ren.inputConnectors[0].connect(lfo)
    parts.append(ren)
const = make(constantCHOP, 's_bar_phase', -800, -2000, const0name='bar_phase', const0value=0.5)
parts.append(const)
song = make(mergeCHOP, 's_song', -600, -1300)
for i, p in enumerate(parts):
    song.inputConnectors[i].connect(p)
mp3 = make(audiofileinCHOP, 't_mp3', -600, -1700)
mp3.par.file.expr = "app.samplesFolder + '/Audio/JeremyCaulfield_www.dumb-unit.com.mp3'"

copies = {}
for i, (name, src, pars) in enumerate((('song', song, {}), ('mp3', mp3, {}),
                                       ('wcag', song, {'Popon': 'beats', 'Flashing': 'wcag'}))):
    c = host.copy(fx, name='ascii_' + name)
    c.nodeX, c.nodeY = 600 * i, -1200
    c.inputConnectors[0].connect(clip)
    c.inputConnectors[1].connect(src)
    for k, v in pars.items():
        setattr(c.par, k, v)
    copies[name] = c

state = {n: dict(flashes=0, prev=0.0, last=None, gaps=[], saved=0, drops=0, beats0=None) for n in copies}
log = []
cook = {n: [0.0, 0.0, 0] for n in copies}
t0 = absTime.seconds


def tick():
    t = absTime.seconds - t0
    row = ['{:6.2f}'.format(t)]
    for n, c in copies.items():
        c.op('out_top').cook()
        st = state[n]
        gate = c.op('flash')[0].eval()
        pop, drop, beat = c.op('pop_env')[0].eval(), c.op('drop_env')[0].eval(), c.op('beat_env')[0].eval()
        a = c.op('audio')
        if st['beats0'] is None:
            st['beats0'] = (a['beat_count'].eval(), a['bar_count'].eval())
        if gate > 0.5 and st['prev'] <= 0.5:
            st['flashes'] += 1
            if st['last'] is not None:
                st['gaps'].append(t - st['last'])
            st['last'] = t
        st['prev'] = gate
        g = c.op('render')
        row.append('{} g{:.0f} pop{:.2f} drop{:.2f} beat{:.2f} set{:.0f} build{:.2f} lvl{:.2f} src{:.0f}'.format(
            n, gate, pop, drop, beat, g.par.vec5valuex.eval(), g.par.vec6valuez.eval(), g.par.vec6valuew.eval(),
            a['source'].eval()))
        if n == 'song' and pop > 0.95 and st['saved'] < 6:
            c.op('out_top').save(os.path.join(OUT, 'song_peak{}{}.png'.format(st['saved'], '_drop' if drop > 0.5 else '')))
            st['saved'] += 1
        if t > 2:
            ops = [o for o in c.findChildren() if o.isTOP or o.isCHOP]
            cook[n][0] += sum(o.cpuCookTime for o in ops)
            cook[n][1] += sum(o.gpuCookTime for o in ops)
            cook[n][2] += 1
    log.append(' | '.join(row))
    if t < SECONDS:
        run('args[0]()', tick, delayFrames=1)
    else:
        finish(t)


def finish(t):
    lines = []
    for n, st in state.items():
        a = copies[n].op('audio')
        beats = a['beat_count'].eval() - st['beats0'][0]
        bars = a['bar_count'].eval() - st['beats0'][1]
        cpu, gpu, k = cook[n]
        lines.append('{}: Flashing {}, Pop On {}: {} flashes passed in {:.1f} s (beats {:.0f}, bars {:.0f}); shortest gap '
                     '{}; cook cpu {:.2f} ms gpu {:.2f} ms per frame (mean of {})'.format(
                         n, copies[n].par.Flashing.eval(), copies[n].par.Popon.eval(), st['flashes'], t, beats, bars,
                         '{:.2f} s'.format(min(st['gaps'])) if st['gaps'] else '-', cpu / max(k, 1), gpu / max(k, 1), k))
    per_op = sorted(((o.gpuCookTime, o.cpuCookTime, o.name) for o in copies['song'].findChildren() if o.isTOP),
                    reverse=True)[:8]
    lines.append('song TOPs last frame (gpu, cpu ms): ' + ', '.join('{} {:.2f}/{:.2f}'.format(n, g, c) for g, c, n in per_op))
    with open(os.path.join(OUT, 'audio.txt'), 'w') as f:
        f.write('\n'.join(lines + [''] + log) + '\n')
    open(os.path.join(OUT, 'done'), 'w').write('audio.txt\n')


def shoot(i):
    for n, c in copies.items():
        c.op('out_top').save(os.path.join(OUT, '{}_{}.png'.format(n, i)))


for i, s in enumerate((3, 6, 9, 12, 15)):
    run('args[0](args[1])', shoot, i, delayMilliSeconds=s * 1000)
tick()
print('logging {} s into {}'.format(SECONDS, OUT))
