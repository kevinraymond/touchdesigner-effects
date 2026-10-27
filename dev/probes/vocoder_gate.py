# DEV ONLY probe: Video Vocoder's gate on the bands' jumps, in /tdlib_dev/video_vocoder as just built: ask (should
# sit at -JUMP with nothing wired), open, the Flashing menu, and the jump and steady followers.
fx = op(TDLIB_PARENT).op('video_vocoder')
for n in ('ask', 'flash', 'open', 'bands_jump', 'bands_steady', 'bands_now'):
    o = fx.op(n)
    o.cook(force=True)
    print(n, o.numChans, [(c.name, round(c.eval(), 3)) for c in o.chans()][:3])
print('Flashing', fx.par.Flashing.eval(), list(fx.par.Flashing.menuNames))
print('jump lags', fx.op('bands_jump').par.lag1.eval(), fx.op('bands_jump').par.lag2.eval(),
      'steady', fx.op('bands_steady').par.type.eval(), fx.op('bands_steady').par.width.eval())
