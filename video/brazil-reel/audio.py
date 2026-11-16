"""Synthesise music bed + sound effects for the Brazil reel and write bed.wav.

Usage: python3 audio.py <out.wav>
"""
import sys, wave
import numpy as np

SR = 44100
DUR = 54.3
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
BPM = 104
beat = 60 / BPM
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = [  # (bass, chord tones)  Fmaj7 - Em7 - Dm7 - G7
    (41, [57, 60, 64, 69]), (40, [55, 59, 62, 67]), (38, [53, 57, 60, 65]), (43, [53, 59, 62, 65])]
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


cuts = [1.10, 2.62, 3.60, 5.70, 7.90, 9.35, 11.15, 13.85, 16.05, 18.95, 20.35, 21.55, 22.75, 23.60, 24.95,
        27.50, 29.25, 30.95, 33.25, 34.65, 36.95, 38.95, 40.45, 41.95, 44.85, 46.30, 49.35]
for c in cuts:
    add(out_sfx, whoosh() * 0.35, c - 0.14)
for tp in (0.12, 1.94, 22.80, 22.92, 23.62, 23.74, 45.2, 45.3):
    add(out_sfx, pop() * 0.45, tp)
# scoreboard ticks + goal counter ticks
for k in range(23):
    add(out_sfx, tick(2000 + k * 25) * 0.35, 3.64 + k * 0.9 / 23)
    add(out_sfx, tick(2600) * 0.3, 5.85 + k * 1.45 / 23)
# touches: every pass, then a fast roll
for k in range(7):
    add(out_sfx, tick(1700) * 0.4, 31.0 + k / 2.6)
for k in range(40):
    add(out_sfx, tick(2200 + k * 15) * 0.22, 33.3 + k * 1.3 / 40)
add(out_sfx, thud() * 0.9, 16.05 + 1.55)
add(out_sfx, whistle() * 0.18, 22.78)
add(out_sfx, whistle(0.3) * 0.15, 23.62)
add(out_sfx, glitch() * 0.5, 44.86)
add(out_sfx, thud() * 0.5, 23.62)

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
