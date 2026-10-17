"""trilhas.py — 5 trilhas originais do Rostinho (síntese em numpy, sem samples nem bancos)
uso: python3 trilhas.py r1 cues_r1.json trilha_r1.wav
Cada trilha = música de fundo própria (instrumentos, tom e andamento diferentes) + efeitos nos cues da cena."""
import sys, json
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
def hz(n): return 440 * 2 ** ((NOTE[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)
def tv(d): return np.arange(max(1, int(d * SR))) / SR
def lp(x, f, o=2): return sosfilt(butter(o, f, 'lp', fs=SR, output='sos'), x, axis=0)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'hp', fs=SR, output='sos'), x, axis=0)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'bandpass', fs=SR, output='sos'), x, axis=0)
R = np.random.default_rng(7)

class Track:
    def __init__(s, dur):
        s.n = int(dur * SR); s.dur = dur
        s.bus = {k: np.zeros((s.n, 2)) for k in ('mus', 'wet', 'low', 'fx', 'fxwet')}
    def add(s, bus, t0, y, pan=0.0, g=1.0):
        i0 = int(round(t0 * SR))
        if i0 >= s.n or len(y) == 0: return
        if i0 < 0: y = y[-i0:]; i0 = 0
        y = y[:s.n - i0] * g
        s.bus[bus][i0:i0 + len(y), 0] += y * np.sqrt(0.5 * (1 - pan))
        s.bus[bus][i0:i0 + len(y), 1] += y * np.sqrt(0.5 * (1 + pan))

# ---------------- instrumentos ----------------
def env_ad(t, a, d): return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def musicbox(f, amp=1, dec=1.4):
    t = tv(dec * 3.5)
    y = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.4) + 0.22 * np.sin(2 * np.pi * 5.43 * f * t) * np.exp(-t / 0.07) + 0.1 * np.sin(2 * np.pi * 8.9 * f * t) * np.exp(-t / 0.03)
    return y * env_ad(t, 0.002, dec) * amp
def glock(f, amp=1, dec=1.2):
    t = tv(dec * 3)
    y = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.25) + 0.15 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t / 0.06)
    return y * env_ad(t, 0.001, dec) * amp
def marimba(f, amp=1, dec=0.45):
    t = tv(dec * 3.2)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.32 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.05) + 0.1 * np.sin(2 * np.pi * 10.1 * f * t) * np.exp(-t / 0.015)
    return y * np.minimum(1, t / 0.002) * amp
def piano(f, amp=1, dec=1.6):
    t = tv(dec * 3)
    h = [1, 0.5, 0.28, 0.16, 0.08, 0.05]; y = np.zeros_like(t)
    for k, a in enumerate(h, 1):
        y += a * np.sin(2 * np.pi * f * k * (1 + 0.0004 * k * k) * t) * np.exp(-t / (dec / (1 + 0.6 * (k - 1))))
    y += 0.08 * R.standard_normal(len(t)) * np.exp(-t / 0.004)  # martelo
    return lp(y * np.minimum(1, t / 0.004), 3800 if f < 600 else 5200) * amp
def ks(f, dur, amp=1, bright=0.6, damp=0.996, pick=None):
    """Karplus-Strong: violão / pizzicato / baixo dedilhado"""
    N = max(2, int(SR / f)); n = int(dur * SR)
    burst = R.uniform(-1, 1, N)
    burst = lp(burst, 800 + 9000 * bright, 1)
    x = np.zeros(n); x[:N] = burst
    if pick: x[:N] -= np.roll(burst, int(N * pick))  # posição do dedo
    a = np.zeros(N + 2); a[0] = 1; a[N] = -damp / 2; a[N + 1] = -damp / 2
    y = lfilter([1], a, x)
    e = np.ones(n); r = int(0.04 * SR); e[-r:] = np.linspace(1, 0, r)
    return y * e * amp / (np.max(np.abs(y)) + 1e-9)
def saw(f, t, cap=2400):
    y = np.zeros_like(t); ph = R.uniform(0, 6.28)
    for h in range(1, 40):
        if f * h > cap: break
        y += np.sin(2 * np.pi * f * h * t + ph * h) / h
    return y
def pad(f, d, amp=1, att=0.8, rel=1.2, cap=1500):
    t = tv(d + rel); y = sum(saw(f * (1 + det), t, cap) for det in (-0.004, 0.0, 0.005)) / 3
    e = np.minimum(1, t / att) ** 1.6 * np.where(t > d, np.clip(1 - (t - d) / rel, 0, 1) ** 1.5, 1)
    return y * e * amp
def soft_pad(f, d, amp=1, att=1.0, rel=1.4):
    t = tv(d + rel); y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t)
    y *= 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    e = np.minimum(1, t / att) ** 1.5 * np.where(t > d, np.clip(1 - (t - d) / rel, 0, 1) ** 1.5, 1)
    return y * e * amp
def sub(f, d, amp=1):
    t = tv(d + 0.1); y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return y * np.minimum(1, t / 0.01) * np.exp(-t / (d * 0.9)) * amp
def tuba(f, d, amp=1):
    t = tv(d + 0.05); y = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t)
    e = np.minimum(1, t / 0.02) * np.clip(1 - t / (d + 0.05), 0, 1) ** 0.6
    return lp(y * e, 900) * amp
def kick(amp=1, f0=110, f1=45, dec=0.28):
    t = tv(dec * 3); f = f1 + (f0 - f1) * np.exp(-t / 0.03); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / dec) * np.minimum(1, t / 0.002) * amp
def thump(amp=1, f0=70, f1=38, dec=0.18):
    t = tv(dec * 4); f = f1 + (f0 - f1) * np.exp(-t / 0.05); ph = 2 * np.pi * np.cumsum(f) / SR
    return lp(np.sin(ph) * np.exp(-t / dec) * np.minimum(1, t / 0.006), 300) * amp
def noise(d, a, b, dec, amp=1):
    t = tv(d); return bp(R.standard_normal(len(t)), a, b) * np.exp(-t / dec) * np.minimum(1, t / 0.001) * amp
def clap(amp=1):
    y = np.zeros(int(0.3 * SR))
    for k, off in enumerate([0, 0.011, 0.022]):
        z = noise(0.25, 900, 4200, 0.012 if k < 2 else 0.07); i = int(off * SR); y[i:i + len(z)] += z[:len(y) - i]
    return y * amp
def shaker(amp=1): return noise(0.09, 4500, 11000, 0.025, amp)
def pop(amp=1, f0=700, f1=320, dec=0.07):
    t = tv(0.25); f = f1 + (f0 - f1) * np.exp(-t / 0.02); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / dec) * np.minimum(1, t / 0.002) * amp
def whoosh(d, amp=1):
    t = tv(d + 0.1); x = R.standard_normal(len(t))
    out = np.zeros_like(x); seg = int(0.01 * SR)
    for i in range(0, len(x), seg):
        p = min(1, i / (d * SR)); fc = 300 + 3200 * p ** 1.5
        out[i:i + seg] = bp(x[max(0, i - 2048):i + seg], fc * 0.6, min(fc * 1.6, 15000))[-len(x[i:i + seg]):]
    e = np.sin(np.pi * np.clip(t / (d + 0.1), 0, 1)) ** 2
    return out * e * amp
def riser(d, notes, amp=1):
    t = tv(d); y = sum(saw(hz(n), t, 3000) for n in notes) / len(notes)
    y = lp(y, 2000) * (t / d) ** 2.2
    return y * amp
def boing(amp=1, f0=180, f1=520, d=0.45):
    t = tv(d); f = f0 + (f1 - f0) * (t / d) ** 0.5 + 40 * np.sin(2 * np.pi * 22 * t) * np.exp(-t / 0.2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.22) * np.minimum(1, t / 0.005) * amp
def slide(amp=1, f0=1300, f1=260, d=0.65):
    t = tv(d); f = f0 * (f1 / f0) ** (t / d); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.15 * np.sin(2 * ph)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6 * amp
def rattle(amp=1, d=0.5):
    t = tv(d); y = np.zeros_like(t)
    for k in range(int(d * 26)):
        z = pop(0.5, 900 + 120 * (k % 3), 500, 0.02); i = int(k / 26 * SR); y[i:i + len(z)] += z[:len(y) - i]
    return y * amp
def scribble(amp=1, d=0.5):
    t = tv(d); x = bp(R.standard_normal(len(t)), 2500, 7000) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t) ** 2)
    return x * np.sin(np.pi * np.clip(t / d, 0, 1)) * amp
def tick(amp=1, f=2200): return (np.sin(2 * np.pi * f * tv(0.05)) * np.exp(-tv(0.05) / 0.008)) * amp
def woodtick(amp=1): t = tv(0.08); return (np.sin(2 * np.pi * 1250 * t) * np.exp(-t / 0.012) + 0.4 * noise(0.08, 2000, 5000, 0.004)) * amp
def typing(t0, d, rate, tr):
    for i in range(int(d * rate)):
        tt = t0 + i / rate + (R.random() - 0.5) * 0.3 / rate
        pn = (R.random() - 0.5) * 0.4; tr.add('fx', tt, noise(0.03, 1800, 6000, 0.006, 0.22 + 0.1 * R.random()), pan=pn); tr.add('fx', tt, pop(0.1, 300, 200, 0.012), pan=pn)

def chord_notes(root_oct, names): return [hz(n) for n in names]

# ---------------- efeitos comuns a partir dos cues ----------------
def sfx(tr, cues, kit):
    for c in cues:
        t, ty, s = c['t'], c['type'], float(c.get('s', 1))
        if ty == 'whoosh': d = float(c.get('len', 0.4)); tr.add('fxwet', t - d, whoosh(d, 0.35 * s), 0)
        elif ty == 'pop': tr.add('fx', t, pop(0.42 * s), 0.1)
        elif ty == 'tick': tr.add('fx', t, kit['tick'](H=s))
        elif ty == 'click': tr.add('fx', t, noise(0.04, 1200, 4000, 0.006, 0.35 * s)); tr.add('fx', t, pop(0.25 * s, 260, 160, 0.02))
        elif ty == 'type': typing(t, float(c.get('len', 1)), float(c.get('rate', 16)), tr)
        elif ty == 'kick': tr.add('low', t, thump(1.0 * s, 85, 40, 0.22)); tr.add('fxwet', t, noise(0.2, 120, 600, 0.05, 0.25 * s))
        elif ty == 'hit': tr.add('low', t, thump(0.8 * s, 70, 36, 0.4)); kit['stab'](t, s)
        elif ty == 'big': tr.add('low', t, thump(1.2 * s, 75, 34, 0.7)); kit['stab'](t, 1.3 * s)
        elif ty == 'sparkle': kit['sparkle'](t, s)
        elif ty == 'rise': d = float(c.get('len', 1)); tr.add('wet', t - d, riser(d, kit['rise'], 0.22 * s))
        elif ty == 'boing': tr.add('fx', t, boing(0.35 * s), -0.1)
        elif ty == 'land': tr.add('low', t, thump(0.7 * s, 110, 50, 0.1)); tr.add('fx', t, pop(0.2 * s, 220, 120, 0.04))
        elif ty == 'fall': tr.add('fxwet', t, slide(0.22 * s), 0.1)
        elif ty == 'wiggle': tr.add('fx', t, rattle(0.4 * s), 0)
        elif ty == 'draw': tr.add('fx', t + 0.15, scribble(0.13 * s, 0.55), 0.2)
        elif ty == 'slot': tr.add('fx', t, woodtick(0.5 * s), (R.random() - 0.5) * 0.3)
        elif ty == 'card': tr.add('fx', t, noise(0.12, 800, 5000, 0.03, 0.22 * s), 0.15); tr.add('low', t + 0.05, thump(0.35, 120, 60, 0.06))
        elif ty == 'pluck': kit['pluck'](t, s)
        elif ty == 'stamp': tr.add('low', t, thump(1.0 * s, 95, 42, 0.2)); tr.add('fx', t, noise(0.14, 600, 3800, 0.035, 0.42 * s), 0.05)
        elif ty == 'buzz':
            for k, f in enumerate((196, 147)): tr.add('fx', t + k * 0.11, lp(saw(f, tv(0.2), 1500), 900) * np.exp(-tv(0.2) / 0.1) * 0.2 * s, -0.05)
        elif ty == 'ding':
            for k, n in enumerate(('E6', 'B6')): tr.add('wet', t + k * 0.07, glock(hz(n), 0.16 * s, 0.9), 0.1)
        elif ty == 'send': tr.add('fx', t, pop(0.3 * s, 1000, 520, 0.05), 0.2); tr.add('fxwet', t - 0.12, whoosh(0.12, 0.2 * s), 0.2)
        elif ty == 'msg': tr.add('fx', t, pop(0.26 * s, 880, 880, 0.06), -0.2); tr.add('fx', t + 0.08, pop(0.3 * s, 1320, 1320, 0.09), -0.2)
        elif ty == 'glow': tr.add('wet', t, pad(hz('A2'), 2.0, 0.25, 0.5, 2.0, 900))
        elif ty == 'swell': kit['swell'](t, float(c.get('len', 1.2)))

def seq_times(t0, t1, step):
    out = []; t = t0
    while t < t1 - 1e-6: out.append(t); t += step
    return out

# =====================================================================
# R1 · Caixinha de música à meia-noite — Lá maior, 72 BPM
# =====================================================================
def r1(cues, dur):
    tr = Track(dur); b = 60 / 72
    prog = [['A2', 'E3', 'A3', 'C#4'], ['F#2', 'C#3', 'F#3', 'A3'], ['D2', 'A2', 'D3', 'F#3'], ['E2', 'B2', 'E3', 'G#3']]
    mel = ['E5', 'C#5', 'E5', 'F#5', 'E5', 'C#5', 'D5', 'B4', 'D5', 'E5', None, None,
           'C#5', 'A4', 'C#5', 'D5', 'C#5', 'A4', 'B4', 'G#4', 'B4', 'A4', None, None]
    t_end = 28.4
    # pad grave contínuo (2 compassos de 3 tempos por acorde)
    bar = 3 * b; t = 0.0; k = 0
    while t < t_end:
        d = 2 * bar
        g = 0.10 if t < 5 else (0.14 if t < 14.2 else 0.18)
        for j, n in enumerate(prog[k % 4]): tr.add('wet', t, pad(hz(n), d, g, 1.2, 1.4, 900), pan=(-0.3 if j % 2 else 0.3))
        t += d; k += 1
    # caixinha: melodia (colcheias de tempo) + arpejo suave
    t = 0.15; i = 0
    while t < t_end - 0.2:
        n = mel[i % len(mel)]
        if n: tr.add('wet', t, musicbox(hz(n), 0.20, 1.3), pan=0.15)
        ch = prog[int(t / (2 * bar)) % 4]
        tr.add('wet', t + b / 2, musicbox(hz(ch[3][:-1] + str(int(ch[3][-1]) + 1)), 0.07, 0.8), pan=-0.35)
        t += b; i += 1
    # piano grave a partir das notas
    for t in seq_times(5.0, t_end, 2 * bar):
        ch = prog[int(t / (2 * bar)) % 4]; tr.add('wet', t, piano(hz(ch[0]) * 2, 0.20, 2.2), pan=-0.1)
    # batimento (lub-dub) durante o ultrassom
    for t in seq_times(14.3, 25.0, b):
        tr.add('low', t, thump(0.55, 60, 38, 0.12)); tr.add('low', t + 0.2, thump(0.35, 55, 36, 0.1))
    # final: acorde de Lá + frase da caixinha
    for j, n in enumerate(['A2', 'E3', 'A3', 'C#4', 'E4']): tr.add('wet', t_end, pad(hz(n), 1.4, 0.2, 0.2, 1.4, 1100), pan=(-0.3 if j % 2 else 0.3))
    for j, n in enumerate(['A5', 'E5', 'C#6', 'A5', 'E6']): tr.add('wet', t_end + 0.1 + j * 0.13, musicbox(hz(n), 0.18, 1.6), pan=(-0.3 if j % 2 else 0.3))
    kit = dict(tick=lambda H=1: tick(0.15 * H, 2600), stab=lambda t, s: [tr.add('wet', t, musicbox(hz(n), 0.16 * s, 1.6), pan=p) for n, p in (('A5', -0.3), ('C#6', 0.3), ('E6', 0))],
               sparkle=lambda t, s: None, rise=['A3', 'E4', 'A4'], pluck=lambda t, s: None, swell=lambda t, d: None)
    # logo: brilho subindo
    for c in cues:
        if c['type'] == 'big':
            for j, n in enumerate(['E5', 'A5', 'C#6', 'E6', 'A6']): tr.add('wet', c['t'] - 0.45 + j * 0.08, musicbox(hz(n), 0.12, 1.2), pan=(j - 2) / 4)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.45, tone=7000)

# =====================================================================
# R2 · Marimba de domingo — Fá maior, 112 BPM
# =====================================================================
def r2(cues, dur):
    tr = Track(dur); b = 60 / 112; e = b / 2
    prog = [['F', 'A', 'C'], ['C', 'E', 'G'], ['D', 'F', 'A'], ['Bb', 'D', 'F']]
    roots = ['F2', 'C2', 'D2', 'Bb1']
    t_end = 28.6; bar = 4 * b
    pat = [0, 2, 1, 2, 0, 1, 2, 1]  # índices do acorde nas colcheias
    octs = [4, 4, 5, 4, 5, 4, 4, 5]
    t = 0.0; i = 0
    while t < t_end - 0.05:
        k = int(t / bar) % 4; ch = prog[k]; step = i % 8
        n = ch[pat[step]] + str(octs[step]); acc = 1.0 if step in (0, 4) else 0.75
        g = 0.20 if t < 2.6 else 0.17
        tr.add('mus', t, marimba(hz(n), g * acc), pan=(-0.35 if step % 2 else 0.35))
        if t >= 2.6:
            # baixo dedilhado sincopado
            if step in (0, 3, 4, 6): tr.add('mus', t, ks(hz(roots[k]) * 2, 0.5, 0.26 if step == 0 else 0.18, bright=0.4, damp=0.993))
            if step in (2, 6): tr.add('fx', t, clap(0.22), 0.05)
            tr.add('fx', t, shaker(0.07 if step % 2 else 0.05), 0.4)
            if step == 0: tr.add('low', t, kick(0.32))
            if step == 4 and k % 2 == 1: tr.add('low', t, kick(0.24))
        t += e; i += 1
    # melodia de glock nas viradas de passo
    melo = [('A5', 0), ('C6', 1), ('D6', 2), ('C6', 3), ('A5', 4), ('G5', 6)]
    for t0 in (9.0, 15.4):
        for n, k in melo: tr.add('wet', t0 + k * e, glock(hz(n), 0.09, 0.9), pan=0.2)
    # pad leve na revelação/CTA
    for j, n in enumerate(['F3', 'A3', 'C4', 'E4']): tr.add('wet', 21.8, pad(hz(n), 6.6, 0.07, 0.4, 1.5, 2000), pan=(-0.3 if j % 2 else 0.3))
    # final
    for j, n in enumerate(['F2', 'C3', 'F3', 'A3', 'C4', 'F4']): tr.add('wet', t_end, marimba(hz(n), 0.22, 0.9), pan=(j - 2.5) / 5)
    for j, n in enumerate(['F5', 'A5', 'C6', 'F6']): tr.add('wet', t_end + 0.05 + j * 0.07, glock(hz(n), 0.1, 1.4), pan=(j - 1.5) / 3)
    kit = dict(tick=lambda H=1: marimba(hz('C6'), 0.12 * H, 0.2),
               stab=lambda t, s: [tr.add('wet', t + j * 0.01, marimba(hz(n), 0.25 * s, 0.8), pan=(j - 1) / 2) for j, n in enumerate(['F4', 'A4', 'C5'])],
               sparkle=lambda t, s: [tr.add('wet', t + j * 0.05, glock(hz(n), 0.09 * s, 1.0), pan=(j - 3) / 6) for j, n in enumerate(['C5', 'F5', 'A5', 'C6', 'F6', 'A6', 'C7'])],
               rise=['F3', 'C4', 'F4'], pluck=lambda t, s: None, swell=lambda t, d: None)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.25, tone=11000)

# =====================================================================
# R3 · Valsa da vida inteira — Dó maior, 90 BPM, 3/4 (compasso = 2 s, começa em t = 1)
# =====================================================================
def r3(cues, dur):
    tr = Track(dur); b = 60 / 90; bar = 3 * b
    prog = [('C', ['C2', 'G2'], ['E3', 'G3', 'C4']), ('Am', ['A1', 'E2'], ['E3', 'A3', 'C4']), ('F', ['F1', 'C2'], ['F3', 'A3', 'C4']), ('G', ['G1', 'D2'], ['D3', 'G3', 'B3']),
            ('C', ['C2', 'G2'], ['E3', 'G3', 'C4']), ('Em', ['E2', 'B2'], ['E3', 'G3', 'B3']), ('F', ['F1', 'C2'], ['F3', 'A3', 'C4']), ('G', ['G1', 'D2'], ['D3', 'G3', 'B3']),
            ('Am', ['A1', 'E2'], ['E3', 'A3', 'C4']), ('F', ['F1', 'C2'], ['F3', 'A3', 'C4']), ('C', ['C2', 'G2'], ['E3', 'G3', 'C4']), ('G', ['G1', 'D2'], ['D3', 'G3', 'B3']),
            ('F', ['F1', 'C2'], ['F3', 'A3', 'C4']), ('Dm', ['D2', 'A2'], ['D3', 'F3', 'A3']), ('G', ['G1', 'D2'], ['D3', 'G3', 'B3'])]
    mel = [['E5', 'D5', 'C5'], ['C5', None, 'E5'], ['A4', 'C5', 'F5'], ['D5', None, None],
           ['E5', 'G5', 'E5'], ['B4', None, 'G4'], ['A4', 'C5', 'A5'], ['G5', 'F5', 'D5'],
           ['C5', 'E5', 'A5'], ['A5', 'G5', 'F5'], ['E5', 'G5', 'C6'], ['B5', None, 'D5'],
           ['A5', 'G5', 'F5'], ['F5', 'E5', 'D5'], ['D5', None, 'B4']]
    t_end = 28.5
    # introdução: acorde arpejado antes do 1º compasso
    for j, n in enumerate(['C3', 'G3', 'C4', 'E4', 'G4']): tr.add('wet', 0.12 + j * 0.15, piano(hz(n), 0.16, 2.5), pan=(j - 2) / 4)
    for k, (nm, bass, chd) in enumerate(prog):
        t0 = 1.0 + k * bar
        if t0 >= t_end - 0.1: break
        tr.add('wet', t0, piano(hz(bass[0]), 0.32, 2.2), pan=-0.15)
        for bt in (1, 2):
            for j, n in enumerate(chd): tr.add('wet', t0 + bt * b + j * 0.006, piano(hz(n), 0.11, 0.9), pan=0.1)
        if k >= 1:
            for j, n in enumerate(mel[k][::1]):
                if n: tr.add('wet', t0 + j * b, piano(hz(n), 0.22, 1.8), pan=0.25)
        # cordas
        g = 0.05 + 0.012 * k
        for j, n in enumerate([bass[1]] + chd): tr.add('wet', t0, pad(hz(n), bar, g, 0.7, 0.8, 1300), pan=(-0.4 if j % 2 else 0.4))
    # resolução
    for j, n in enumerate(['C2', 'G2', 'C3', 'E3', 'G3', 'C4', 'E4']): tr.add('wet', t_end, piano(hz(n), 0.2, 3.0), pan=(j - 3) / 6)
    for j, n in enumerate(['C3', 'G3', 'E4', 'G4']): tr.add('wet', t_end, pad(hz(n), 1.1, 0.12, 0.2, 1.3, 1300), pan=(-0.3 if j % 2 else 0.3))
    def sparkle(t, s):
        for j, n in enumerate(['G5', 'C6', 'E6', 'G6', 'C7']): tr.add('wet', t + j * 0.045, musicbox(hz(n), 0.08 * s, 1.1), pan=(j - 2) / 4)
    def swell(t, d):
        for j, n in enumerate(['F3', 'A3', 'C4', 'F4']): tr.add('wet', t - 0.2, pad(hz(n), d + 1.5, 0.09, d, 1.0, 1600), pan=(-0.3 if j % 2 else 0.3))
    kit = dict(tick=lambda H=1: musicbox(hz('C6'), 0.06 * H, 0.5), stab=lambda t, s: None, sparkle=sparkle, rise=['C4', 'G4'], pluck=lambda t, s: None, swell=swell)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.42, tone=8000)

# =====================================================================
# R4 · Pizzicato do Zinho — Sol maior, 120 BPM
# =====================================================================
def r4(cues, dur):
    tr = Track(dur); b = 0.5; e = 0.25
    prog = [('G', 'G2', ['B3', 'D4', 'G4']), ('C', 'C3', ['C4', 'E4', 'G4']), ('D', 'D3', ['A3', 'D4', 'F#4']), ('G', 'G2', ['B3', 'D4', 'G4'])]
    t_end = 28.6; bar = 4 * b
    # 0–3: na ponta dos pés (pizz pianinho, staccato)
    sneak = ['G3', 'B3', 'D4', 'B3', 'C4', 'E4', 'G4', 'E4', 'D4', 'F#4', 'A4', 'F#4']
    for i, t in enumerate(seq_times(0.1, 2.95, e)):
        tr.add('mus', t, ks(hz(sneak[i % len(sneak)]), 0.25, 0.16, bright=0.8, damp=0.97), pan=(-0.3 if i % 2 else 0.3))
    # 4.35 em diante: banda completa (tuba + pizz no contratempo + glock + bumbo de bolha)
    glm = ['D5', 'G5', 'B5', 'A5', 'G5', 'E5', 'G5', None, 'F#5', 'A5', 'D6', 'C6', 'B5', 'G5', 'B5', None]
    t = 4.35; i = 0
    while t < t_end - 0.05:
        k = int((t - 4.35) / bar) % 4; nm, root, chd = prog[k]; beat = i % 4
        quiet = 0.55 if 16.0 <= t < 25.0 else 1.0
        # tuba: 1 e 3 (raiz e quinta)
        if beat in (0, 2):
            f = hz(root) * (1 if beat == 0 else 1.5)
            tr.add('low', t, tuba(f, 0.32, 0.30 * quiet))
            tr.add('low', t, kick(0.18 * quiet, 180, 80, 0.1))
        # pizz no contratempo
        for j, n in enumerate(chd): tr.add('mus', t + e, ks(hz(n), 0.3, 0.09 * quiet, bright=0.75, damp=0.975), pan=(j - 1) / 2)
        # glock melodia (a partir de 5.5)
        if t >= 5.5:
            n = glm[(i * 2) % len(glm)]; n2 = glm[(i * 2 + 1) % len(glm)]
            if n: tr.add('wet', t, glock(hz(n), 0.08 * quiet, 0.6), pan=0.25)
            if n2 and i % 2: tr.add('wet', t + e, glock(hz(n2), 0.06 * quiet, 0.5), pan=0.25)
        t += b; i += 1
    # final
    for j, n in enumerate(['G2', 'D3', 'G3', 'B3', 'D4', 'G4']): tr.add('mus', t_end + j * 0.03, ks(hz(n), 1.6, 0.16, bright=0.7, damp=0.998), pan=(j - 2.5) / 5)
    tr.add('low', t_end, tuba(hz('G1') * 2, 1.0, 0.3))
    for j, n in enumerate(['G5', 'B5', 'D6', 'G6']): tr.add('wet', t_end + 0.12 + j * 0.06, glock(hz(n), 0.09, 1.3), pan=(j - 1.5) / 3)
    kit = dict(tick=lambda H=1: glock(hz('D6'), 0.08 * H, 0.3),
               stab=lambda t, s: [tr.add('wet', t + j * 0.02, glock(hz(n), 0.1 * s, 1.0), pan=(j - 1) / 2) for j, n in enumerate(['G5', 'B5', 'D6'])],
               sparkle=lambda t, s: None, rise=['G3', 'D4'], pluck=lambda t, s: None, swell=lambda t, d: None)
    for c in cues:
        if c['type'] == 'big':  # despertar: glissando de glock
            for j, n in enumerate(['G4', 'B4', 'D5', 'G5', 'B5', 'D6', 'G6']): tr.add('wet', c['t'] - 0.35 + j * 0.05, glock(hz(n), 0.08, 0.8), pan=(j - 3) / 6)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.22, tone=10000)

# =====================================================================
# R5 · Violão de varanda — Ré maior, 92 BPM (dedilhado em colcheias)
# =====================================================================
def r5(cues, dur):
    tr = Track(dur); b = 60 / 92; e = b / 2; bar = 4 * b
    prog = [['D2', 'A2', 'D3', 'F#3', 'A3'], ['C#2', 'A2', 'C#3', 'E3', 'A3'], ['B1', 'F#2', 'B2', 'D3', 'F#3'], ['G1', 'D2', 'G2', 'B2', 'D3']]
    pat = [0, 2, 3, 4, 1, 3, 2, 4]
    t_end = 28.6
    t = 0.05; i = 0
    while t < t_end - 0.05:
        k = int((t - 0.05) / bar) % 4; ch = prog[k]; step = i % 8
        n = ch[pat[step]]; f = hz(n) * (2 if pat[step] == 0 else 1) if False else hz(n)
        g = 0.34 if pat[step] < 2 else 0.24
        if t < 5.0: g *= 0.8
        tr.add('mus', t + (R.random() - 0.5) * 0.012, ks(f * 2 if pat[step] >= 2 else f, 1.6, g, bright=0.42, damp=0.9975, pick=0.2), pan=(-0.25 + 0.5 * pat[step] / 4))
        if t >= 5.0:
            tr.add('fx', t, shaker(0.05 if step % 2 else 0.035), -0.35)
            if step == 0: tr.add('low', t, sub(hz(ch[0]) * 2, bar * 0.9, 0.12))
        t += e; i += 1
    # hum pad (coro suave) na família e nos slots
    for t0, t1 in ((15.5, 25.5),):
        tt = t0
        while tt < t1:
            k = int((tt - 0.05) / bar) % 4
            for j, n in enumerate(prog[k][2:]): tr.add('wet', tt, soft_pad(hz(n), bar, 0.035, 0.8, 1.0), pan=(-0.3 if j % 2 else 0.3))
            tt += bar
    # final: acorde de Ré tocado devagar + harmônico
    for j, n in enumerate(['D2', 'A2', 'D3', 'F#3', 'A3', 'D4']): tr.add('mus', t_end + j * 0.07, ks(hz(n) * (2 if j > 2 else 1), 2.5, 0.3, bright=0.45, damp=0.9985), pan=(j - 2.5) / 5)
    tr.add('wet', t_end + 0.5, glock(hz('D6'), 0.06, 1.8), 0.2)
    def pluck(t, s):  # harmônico de violão em cada linha
        tr.add('wet', t, glock(hz(['A5', 'F#5', 'D6', 'E5', 'A5'][int(t * 10) % 5]), 0.07 * s, 1.2), pan=0.3)
    kit = dict(tick=lambda H=1: tick(0.1 * H, 2400),
               stab=lambda t, s: [tr.add('mus', t + j * 0.04, ks(hz(n), 2.0, 0.22 * s, bright=0.5, damp=0.998), pan=(j - 1) / 2) for j, n in enumerate(['D3', 'A3', 'F#4'])],
               sparkle=lambda t, s: [tr.add('wet', t + j * 0.05, glock(hz(n), 0.06 * s, 1.0), pan=(j - 2) / 4) for j, n in enumerate(['D5', 'F#5', 'A5', 'D6', 'F#6'])],
               rise=['D3', 'A3'], pluck=pluck, swell=lambda t, d: None)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.3, tone=9000)

# =====================================================================
# R6 · Programa de auditório — Mi bemol maior, 118 BPM (ukulele + assobio + palmas)
# =====================================================================
def whistle(f, d, amp=1):
    t = tv(d + 0.15); vib = 1 + 0.012 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.15)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR; y = np.sin(ph) + 0.08 * np.sin(2 * ph) + 0.03 * np.sin(3 * ph)
    y += 0.02 * lp(R.standard_normal(len(t)), 3000)
    e = np.minimum(1, t / 0.03) * np.where(t > d, np.clip(1 - (t - d) / 0.15, 0, 1), 1)
    return y * e * amp
def r6(cues, dur):
    tr = Track(dur); b = 60 / 118; e = b / 2; bar = 4 * b
    chords = [['Eb4', 'G4', 'Bb4'], ['C4', 'Eb4', 'G4'], ['Ab3', 'C4', 'Eb4'], ['Bb3', 'D4', 'F4']]
    roots = ['Eb2', 'C2', 'Ab1', 'Bb1']; fifths = ['Bb2', 'G2', 'Eb2', 'F2']
    mel = ['G5', 'Bb5', 'G5', 'F5', 'Eb5', None, 'G5', None, 'Eb5', 'G5', 'Eb5', 'D5', 'C5', None, 'Eb5', None,
           'Eb5', 'Ab5', 'Eb5', 'C5', 'Ab4', None, 'C5', None, 'D5', 'F5', 'D5', 'Bb4', 'Bb4', None, 'D5', None]
    t_end = 14.15; t = 0.05; i = 0
    while t < t_end - 0.05:
        k = int((t - 0.05) / bar) % 4; step = i % 8; ch = chords[k]
        full = t >= 2.2 and t < 12.2
        if step in (0, 2, 3, 5, 6) or (step == 7 and full):
            acc = 1.0 if step in (0, 3, 6) else 0.7
            for j, n in enumerate(ch): tr.add('mus', t + j * 0.012, ks(hz(n) * (2 if t < 2.2 else 1), 0.45, (0.17 if full else 0.12) * acc, bright=0.78, damp=0.985, pick=0.15), pan=(j - 1) * 0.25)
        if full:
            if step in (0, 4): tr.add('mus', t, ks(hz(roots[k]) * 2, 0.5, 0.26 if step == 0 else 0.2, bright=0.3, damp=0.992))
            if step == 4 and k % 2: tr.add('mus', t, ks(hz(fifths[k]) * 2, 0.4, 0.14, bright=0.3, damp=0.992))
            if step in (2, 6): tr.add('fx', t, clap(0.3), 0.1)
            if step % 2: tr.add('fx', t, woodtick(0.16), 0.3)
            if step == 0: tr.add('low', t, kick(0.26))
            n = mel[(i - int(2.2 / e)) % len(mel)] if t >= 2.2 else None
        t += e; i += 1
    # assobio: motivo a cada rodada
    for T0 in (2.2, 5.5, 8.8):
        j = 0
        for q in range(8):
            n = mel[(q + (int((T0 - 2.2) / 3.3)) * 8) % len(mel)]
            if n: tr.add('wet', T0 + 0.25 + q * e, whistle(hz(n), 0.2, 0.09), pan=0.2)
    # CTA: acorde final + glock
    for j, n in enumerate(['Eb2', 'Bb2', 'Eb3', 'G3', 'Bb3', 'Eb4']): tr.add('mus', t_end + j * 0.03, ks(hz(n), 1.6, 0.2, bright=0.6, damp=0.997), pan=(j - 2.5) / 5)
    for j, n in enumerate(['Eb5', 'G5', 'Bb5', 'Eb6']): tr.add('wet', t_end + 0.1 + j * 0.07, glock(hz(n), 0.09, 1.4), pan=(j - 1.5) / 3)
    for t0 in seq_times(12.25, 14.1, b): tr.add('wet', t0, piano(hz('Eb3'), 0.0, 0.1))
    kit = dict(tick=lambda H=1: woodtick(0.45 * H), stab=lambda t, s: [tr.add('wet', t, glock(hz(n), 0.1 * s, 1.0), pan=(j - 1) / 2) for j, n in enumerate(['Eb5', 'G5', 'Bb5'])],
               sparkle=lambda t, s: [tr.add('wet', t + j * 0.05, glock(hz(n), 0.08 * s, 1.0), pan=(j - 2) / 4) for j, n in enumerate(['Bb5', 'Eb6', 'G6', 'Bb6', 'Eb7'])],
               rise=['Eb3', 'Bb3'], pluck=lambda t, s: None, swell=lambda t, d: None)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.2, tone=11000)

# =====================================================================
# R7 · Lo-fi de sábado — Si bemol maior, 84 BPM (piano elétrico + escovinha)
# =====================================================================
def epiano(f, amp=1, dec=1.3):
    t = tv(dec * 3)
    idx = 1.6 * np.exp(-t / 0.25) + 0.25
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * 14 * f * t) * 0.35 + 0.6 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.3) * 0)
    y = np.sin(2 * np.pi * f * t + idx * 0.5 * np.sin(2 * np.pi * f * t)) + 0.18 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.5)
    y *= 1 + 0.12 * np.sin(2 * np.pi * 4.2 * t)
    return lp(y * env_ad(t, 0.004, dec), 3200) * amp
def r7(cues, dur):
    tr = Track(dur); b = 60 / 84; e = b / 2; bar = 4 * b
    prog = [['Bb3', 'D4', 'F4', 'A4'], ['G3', 'Bb3', 'D4', 'F4'], ['C4', 'Eb4', 'G4', 'Bb4'], ['F3', 'A3', 'Eb4', 'G4']]
    roots = ['Bb1', 'G1', 'C2', 'F1']
    t_end = 14.15
    # chuvisco de vinil
    for tt in np.arange(0, t_end, 0.07): 
        if R.random() < 0.35: tr.add('fx', tt, noise(0.012, 3000, 9000, 0.003, 0.05 + 0.05 * R.random()), (R.random() - 0.5) * 0.8)
    k = 0; t = 0.05
    while t < t_end - 0.3:
        ch = prog[k % 4]
        for j, n in enumerate(ch): tr.add('wet', t + j * 0.025 + (R.random() - 0.5) * 0.01, epiano(hz(n), 0.17 if t > 2.0 else 0.13, 1.6), pan=(j - 1.5) * 0.18)
        tr.add('wet', t + 1.5 * b, epiano(hz(ch[1]), 0.1, 1.0), pan=0.2)
        tr.add('low', t, sub(hz(roots[k % 4]) * 2, bar * 0.9, 0.2))
        if t >= 2.0:
            for q in range(8):
                tq = t + q * e + (0.03 * e if q % 2 else 0)  # swing
                tr.add('fx', tq, noise(0.06, 6500, 12000, 0.02, 0.08 if q % 2 else 0.05), 0.3)
                if q in (0, 5): tr.add('low', tq, kick(0.24, 95, 42, 0.2))
                if q in (2, 6): tr.add('fx', tq, noise(0.16, 1200, 6000, 0.05, 0.2), -0.1); tr.add('fx', tq, pop(0.12, 330, 200, 0.05))
        t += bar; k += 1
    mel = [('F5', 0.0), ('D5', 0.5), ('A5', 1.0), ('G5', 2.0), ('F5', 2.5), ('D5', 3.0), ('C5', 3.5)]
    for T0 in (2.3, 5.2, 8.1):
        for n, off in mel: tr.add('wet', T0 + off * b, musicbox(hz(n), 0.09, 0.9), pan=0.25)
    for j, n in enumerate(['Bb2', 'F3', 'A3', 'D4', 'F4', 'A4']): tr.add('wet', t_end + j * 0.05, epiano(hz(n), 0.18, 2.2), pan=(j - 2.5) / 5)
    for j, n in enumerate(['D6', 'F6', 'A6']): tr.add('wet', t_end + 0.2 + j * 0.09, musicbox(hz(n), 0.1, 1.4), pan=(j - 1) / 2)
    kit = dict(tick=lambda H=1: tick(0.12 * H, 2000), stab=lambda t, s: [tr.add('wet', t + j * 0.02, epiano(hz(n), 0.14 * s, 1.0), pan=(j - 1) / 2) for j, n in enumerate(['Bb3', 'D4', 'F4'])],
               sparkle=lambda t, s: [tr.add('wet', t + j * 0.05, musicbox(hz(n), 0.07 * s, 1.0), pan=(j - 2) / 4) for j, n in enumerate(['F5', 'A5', 'D6', 'F6', 'A6'])],
               rise=['Bb3', 'F4'], pluck=lambda t, s: None, swell=lambda t, d: None)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.38, tone=6500)

# =====================================================================
# R8 · Notificação de família — Mi maior, 104 BPM (arpejo sintético + estalo)
# =====================================================================
def synpluck(f, amp=1, dec=0.16):
    t = tv(dec * 4); y = saw(f, t, 3500) + 0.5 * saw(f * 1.006, t, 3500)
    return lp(y * np.exp(-t / dec) * np.minimum(1, t / 0.003), 4200) * amp * 0.35
def r8(cues, dur):
    tr = Track(dur); b = 60 / 104; s16 = b / 4; bar = 4 * b
    prog = [['E3', 'G#3', 'B3', 'E4'], ['C#3', 'E3', 'G#3', 'C#4'], ['A2', 'C#3', 'E3', 'A3'], ['B2', 'D#3', 'F#3', 'B3']]
    roots = ['E2', 'C#2', 'A1', 'B1']
    t_end = 14.15; t = 0.05; i = 0
    while t < t_end - 0.05:
        k = int((t - 0.05) / bar) % 4; ch = prog[k]; step = i % 16
        full = 1.0 <= t < 12.2
        n = ch[[0, 1, 2, 3, 2, 1, 3, 2][step % 8]]
        g = 0.2 if full else 0.12
        if step % 2 == 0 or full: tr.add('mus', t, synpluck(hz(n) * 2, g * (1.0 if step % 4 == 0 else 0.7), 0.14), pan=-0.3 + 0.6 * ((step % 8) / 8))
        if full:
            if step % 8 in (0, 3, 6): tr.add('low', t, sub(hz(roots[k]) * 2, 0.32, 0.22))
            if step % 4 == 0: tr.add('low', t, kick(0.28, 105, 44, 0.2))
            if step % 8 == 4: tr.add('fx', t, clap(0.26), 0.05); tr.add('fx', t, noise(0.04, 2500, 7000, 0.01, 0.2))
            if step % 2 == 1: tr.add('fx', t, noise(0.04, 7000, 13000, 0.012, 0.08), 0.3)
        if step == 0 and t >= 1.0: 
            for j, nn in enumerate(ch): tr.add('wet', t, pad(hz(nn), bar, 0.05, 0.4, 0.6, 1100), pan=(-0.3 if j % 2 else 0.3))
        t += s16; i += 1
    for j, nn in enumerate(['E2', 'B2', 'E3', 'G#3', 'B3', 'E4']): tr.add('wet', t_end + j * 0.04, synpluck(hz(nn), 0.5, 0.5), pan=(j - 2.5) / 5)
    for j, nn in enumerate(['E5', 'G#5', 'B5', 'E6']): tr.add('wet', t_end + 0.1 + j * 0.07, glock(hz(nn), 0.09, 1.4), pan=(j - 1.5) / 3)
    kit = dict(tick=lambda H=1: pop(0.1 * H, 1800, 1800, 0.02), stab=lambda t, s: [tr.add('wet', t + j * 0.015, synpluck(hz(n), 0.6 * s, 0.4), pan=(j - 1) / 2) for j, n in enumerate(['E4', 'G#4', 'B4'])],
               sparkle=lambda t, s: [tr.add('wet', t + j * 0.05, glock(hz(n), 0.08 * s, 1.0), pan=(j - 2) / 4) for j, n in enumerate(['B5', 'E6', 'G#6', 'B6', 'E7'])],
               rise=['E3', 'B3'], pluck=lambda t, s: None, swell=lambda t, d: None)
    sfx(tr, cues, kit)
    return master(tr, dur, verb_amt=0.28, tone=10000)

# ---------------- master ----------------
def make_ir(secs=2.4, decay=2.8, lp_=4200, seed=3):
    t = tv(secs); r = np.random.default_rng(seed); out = []
    for c in range(2):
        x = lp(r.standard_normal(len(t)) * np.exp(-t * decay), lp_); x[:int(0.018 * SR)] = 0
        out.append(x / np.sqrt(np.sum(x ** 2)))
    return out
IR = make_ir()
def verb(x, wet): return x + np.stack([fftconvolve(x[:, c], IR[c])[:len(x)] for c in range(2)], 1) * wet

def master(tr, dur, verb_amt=0.3, tone=9000):
    B = tr.bus
    x = (verb(B['mus'], verb_amt * 0.6) + verb(B['wet'], verb_amt) + 0.6 * hp(lp(B['low'], 400), 55) + B['fx'] + verb(B['fxwet'], 0.25))
    x = lp(hp(x, 45, 3), tone)
    x = x / (np.max(np.abs(x)) + 1e-9); x = np.tanh(x * 2.2) / np.tanh(2.2)
    t = np.arange(len(x)) / SR; g = np.clip((dur - t) / 0.6, 0, 1) ** 1.3; n = int(0.005 * SR); g[:n] *= np.linspace(0, 1, n)
    x *= g[:, None]
    return x / (np.max(np.abs(x)) + 1e-9) * 0.89

if __name__ == '__main__':
    which, cues_f, out = sys.argv[1:4]
    info = json.load(open(cues_f)); dur = float(info.get('dur', 30)); cues = sorted(info.get('cues', []), key=lambda c: c['t'])
    x = {'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4, 'r5': r5, 'r6': r6, 'r7': r7, 'r8': r8}[which](cues, dur)
    wavfile.write(out, SR, (x * 32767).astype(np.int16))
    print(f'  ✔ trilha {which} {x.shape[0] / SR:.2f}s -> {out}')
