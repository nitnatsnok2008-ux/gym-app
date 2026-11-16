"""Synthesise music bed + sound effects for the Man Utd reel.

Usage: python3 audio.py <out.wav>
"""
import sys, wave
import numpy as np

SR = 44100
DUR = 57.5
N = int(SR * DUR)
rng = np.random.default_rng(7)
out_music = np.zeros(N)
out_sfx = np.zeros(N)


def add(buf, sig, t):
    i = int(t * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i]


def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def tone(freq, length, d=0.6, harm=(1, .45, .2, .08)):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = sum(h * np.sin(2 * np.pi * freq * (k + 1) * t) for k, h in enumerate(harm))
    return s * env(n, 0.01, d)


def lowpass(x, k=0.05):
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def noise(length):
    return rng.standard_normal(int(length * SR))


# ---------------- music: soft bossa groove, 104 bpm ----------------
BPM = 96
beat = 60 / BPM
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [  # minor 'comedic tension':  Am - F - Dm - E7
    (45, [57, 60, 64]), (41, [57, 60, 65]), (38, [57, 62, 65]), (40, [56, 59, 62, 64])]
shaker = lowpass(noise(0.06), 0.6) * env(int(0.06 * SR), 0.002, 0.02)
shaker = shaker - lowpass(shaker, 0.08)  # high-pass-ish
kick_t = np.arange(int(0.25 * SR)) / SR
kick = np.sin(2 * np.pi * (55 + 90 * np.exp(-kick_t * 30)) * kick_t) * np.exp(-kick_t * 14)
rim = tone(1800, 0.05, 0.015, (1, .3)) * 0.5

bar = 0
t = 0.0
while t < DUR:
    bass, ch = chords[bar % 4]
    # bossa bass: root on 1, fifth on 3 (anticipated)
    add(out_music, tone(midi(bass), 1.2, 0.5, (1, .3, .05)) * 0.55, t)
    add(out_music, tone(midi(bass + 7), 1.0, 0.45, (1, .3, .05)) * 0.45, t + 2.5 * beat)
    # Rhodes-like chord stabs on bossa rhythm
    for off in (0, 1.5, 3.0, 4.5, 6.0):
        if off >= 4:
            continue
        for m in ch:
            add(out_music, tone(midi(m), 0.9, 0.35, (1, .25, .1)) * 0.11, t + off * beat)
    for e in range(8):
        add(out_music, shaker * (0.5 if e % 2 else 0.8) * 0.5, t + e * beat / 2)
    add(out_music, kick * 0.7, t)
    add(out_music, kick * 0.55, t + 2 * beat)
    for r in (1.5, 3.0) if bar % 2 == 0 else (1.0, 2.5):
        add(out_music, rim, t + r * beat)
    t += 4 * beat
    bar += 1

# fade in/out
fade = np.ones(N)
fi, fo = int(0.3 * SR), int(1.2 * SR)
fade[:fi] = np.linspace(0, 1, fi)
fade[-fo:] = np.linspace(1, 0, fo)
out_music *= fade

# ---------------- sfx ----------------
def whoosh(length=0.28):
    n = int(length * SR)
    x = noise(length)
    sweep = np.linspace(0.02, 0.35, n)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += sweep[i] * (x[i] - acc)
        y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, n)) ** 2


def pop():
    n = int(0.12 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (300 + 900 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 30)


def tick(f=2400):
    return tone(f, 0.04, 0.01, (1,)) * 0.6


def thud():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 9) + lowpass(noise(0.35), 0.05) * np.exp(-tt * 20) * 2


def whistle(length=0.45):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = 2900 + 120 * np.sin(2 * np.pi * 32 * tt)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, tt / 0.02) * np.minimum(1, (length - tt) / 0.05)


def glitch():
    x = np.sign(np.sin(2 * np.pi * 180 * np.arange(int(0.25 * SR)) / SR)) * 0.4
    x *= (rng.random(len(x)) > 0.3)
    return x * np.linspace(1, 0, len(x))


cuts = [1.15, 2.88, 5.25, 7.45, 9.12, 10.80, 12.38, 14.88, 17.32, 19.22, 21.82, 25.72, 27.85, 29.10, 30.62,
        32.10, 35.00, 37.15, 40.40, 42.55, 45.00, 48.75, 51.00, 53.00]
for c in cuts:
    add(out_sfx, whoosh() * 0.35, c - 0.14)
for tp in (0.10, 12.42, 30.66, 42.6, 45.3, 45.6):
    add(out_sfx, pop() * 0.45, tp)

def trombone(t0):  # sad "wah wah wah waaah"
    for i, (m, l) in enumerate([(58, .32), (57, .32), (56, .32), (55, .9)]):
        n = int(l * SR); tt = np.arange(n) / SR
        f = midi(m) * (1 + (0.012 * np.sin(2 * np.pi * 6 * tt) if i == 3 else 0))
        sig = sum(h * np.sin(2 * np.pi * f * (k + 1) * tt) for k, h in enumerate((1, .7, .5, .3, .2)))
        add(out_sfx, sig * np.minimum(1, tt / .04) * np.minimum(1, (l - tt) / .08) * 0.22, t0 + sum([.32, .32, .32][:i]))
trombone(2.10)

def stamp_sfx(t0):
    add(out_sfx, thud() * 0.9, t0); add(out_sfx, lowpass(noise(.08), .3) * np.linspace(1, 0, int(.08 * SR)) * .6, t0)
for tp in (19.22 + .45, 21.82 + 1.75, 25.72 + .7):
    stamp_sfx(tp)
for i in range(10):
    add(out_sfx, tick(1800 if i else 2600) * 0.45, 14.88 + i * 0.09)
for i in range(8):
    stamp_sfx(17.32 + 0.05 + i * 0.14)
# managers counter ticks
for i in range(8):
    add(out_sfx, tick(2000 + i * 60) * 0.4, 32.3 + i * 1.5 / 8)
# cash register "ka-ching"
ch = tone(2637, .6, .25, (1, .5, .2)) * .5 + tone(3520, .6, .2, (1, .4)) * .4
add(out_sfx, lowpass(noise(.06), .4) * .5, 37.5); add(out_sfx, ch, 37.58)
for i in range(30):
    add(out_sfx, tick(2400) * 0.15, 37.6 + i * 1.4 / 30)
# neon buzz + flicker
buzz = np.sign(np.sin(2 * np.pi * 120 * np.arange(int(.9 * SR)) / SR)) * .05
add(out_sfx, buzz * np.linspace(0, 1, len(buzz)), 45.25)
add(out_sfx, glitch() * .5, 48.75)
# rimshot "ba-dum-tss" on "comedy club."
add(out_sfx, tone(180, .25, .1, (1, .4)) * .6, 50.05); add(out_sfx, tone(140, .25, .12, (1, .4)) * .6, 50.25)
cym = noise(1.0); cym = cym - lowpass(cym, .25); add(out_sfx, cym * env(len(cym), .002, .35) * .35, 50.45)
add(out_sfx, whistle() * 0.12, 10.85)
# rain ambience in rain scenes
for a, b in [(10.8, 21.82), (25.72, 27.85), (29.1, 32.1), (40.4, 48.75), (51.0, 57.5)]:
    n = noise(b - a); r = lowpass(n, .35) - lowpass(n, .05)
    k = np.ones(len(r)); f = int(.25 * SR); k[:f] = np.linspace(0, 1, f); k[-f:] = np.linspace(1, 0, f)
    add(out_sfx, r * k * .12, a)

music = out_music / np.max(np.abs(out_music)) * 0.16   # ~ -22 dB under a normalised voice
sfx = out_sfx / max(1e-9, np.max(np.abs(out_sfx))) * 0.35
mix = np.clip(music + sfx, -1, 1)
st = np.stack([mix, mix], axis=1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print('ok')
