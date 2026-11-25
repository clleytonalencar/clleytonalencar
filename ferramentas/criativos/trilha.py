"""Original 10s soundtrack for otica_oftalmo_14nov_c4 (120 BPM, A minor pop/house).

Synced to the v2.html timeline: tense intro + ticking (hook), riser over the
eye-chart "focus" (1.6-2.95s), drop at 3.0s, SFX on scene changes.
Usage: python3 music.py out.wav
"""
import sys
import wave
import numpy as np
import os
TR = int(os.environ.get("TR", "0"))
PROG = os.environ.get("PROG", "A,F,C,G,A").split(",")

SR = 44100
DUR = 10.0
N = int(SR * DUR)
rng = np.random.default_rng(int(os.environ.get("SEED", "11")))
BEAT = 0.5  # 120 BPM


def t_arr(sec):
    return np.arange(int(sec * SR)) / SR


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += gain * sig[: j - i]


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for k in range(len(x)):
        acc = (1 - a) * x[k] + a * acc
        y[k] = acc
    return y


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n + TR - 69) / 12)


# ---------- instruments ----------
def kick():
    t = t_arr(0.35)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 9)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.3
    return body + click


def clap():
    t = t_arr(0.22)
    n = rng.standard_normal(len(t))
    n = n - lowpass(n, 900)  # high-pass-ish
    env = np.exp(-t * 22) * (1 + 0.6 * (t < 0.012))
    return n * env * 0.6


def hat(open_=False):
    t = t_arr(0.18 if open_ else 0.05)
    n = rng.standard_normal(len(t))
    n = n - lowpass(n, 6000)
    return n * np.exp(-t * (18 if open_ else 90)) * 0.35


def bass(freq, dur):
    t = t_arr(dur)
    w = sum(np.sin(2 * np.pi * freq * h * t) / h for h in (1, 2, 3, 4))
    env = np.minimum(1, t / 0.005) * np.exp(-t * 3.5)
    return lowpass(w * env, 700) * 0.9


def pluck(freqs, dur=0.35):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for f in freqs:
        for h, a in ((1, 1.0), (2, 0.35), (3, 0.18)):
            s += a * np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6.28))
    env = np.minimum(1, t / 0.004) * np.exp(-t * 9)
    return s * env / len(freqs) * 0.55


def pad(freqs, dur):
    t = t_arr(dur)
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.6, 0.6):
            s += np.sin(2 * np.pi * (f + det) * t)
    env = np.minimum(1, t / (dur * 0.7)) * np.minimum(1, (dur - t) / 0.15)
    return lowpass(s * env / (2 * len(freqs)), 1200) * 0.5


def riser(dur):
    t = t_arr(dur)
    n = rng.standard_normal(len(t))
    out = np.zeros_like(t)
    seg = int(0.05 * SR)
    for k in range(0, len(t), seg):  # stepwise brightening noise sweep
        frac = k / len(t)
        chunk = n[k:k + seg]
        out[k:k + seg] = chunk - lowpass(chunk, 300 + 7000 * frac)
    tone = np.sin(2 * np.pi * np.cumsum(220 + 660 * (t / dur) ** 2) / SR) * 0.25
    env = (t / dur) ** 2
    return (out * 0.5 + tone) * env


def whoosh(dur=0.45):
    t = t_arr(dur)
    n = rng.standard_normal(len(t))
    n = lowpass(n, 2500) - lowpass(n, 300)
    env = np.sin(np.pi * t / dur) ** 2
    return n * env * 1.4


def pop(f0=700, f1=350):
    t = t_arr(0.12)
    f = f1 + (f0 - f1) * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * 0.8


def tick():
    t = t_arr(0.03)
    return np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 200) * 0.5


def crash():
    t = t_arr(1.2)
    n = rng.standard_normal(len(t))
    n = n - lowpass(n, 4000)
    return n * np.exp(-t * 3.2) * 0.35


# ---------- arrangement ----------
mix = np.zeros(N)
A, F, C, G = (57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)
roots = {"A": 45, "F": 41, "C": 48, "G": 43}
chords = {"A": A, "F": F, "C": C, "G": G}

# Hook hits at 0s: groove starts immediately (no slow intro).
place(mix, crash(), 0.0, 0.9)
prog = PROG
for bar, name in enumerate(prog):
    t0 = bar * 4 * BEAT
    for b in range(4):
        tb = t0 + b * BEAT
        if tb >= DUR:
            break
        place(mix, kick(), tb, 1.0)
        if b in (1, 3):
            place(mix, clap(), tb, 0.8)
        place(mix, hat(), tb + BEAT / 2, 0.8)
        place(mix, hat(), tb, 0.35)
        place(mix, bass(note(roots[name]), BEAT * 0.45), tb + BEAT / 2, 0.75)
        place(mix, pluck([note(n) for n in chords[name]]), tb + BEAT / 2, 0.9)
    place(mix, hat(open_=True), t0 + 3.5 * BEAT, 0.6)

# Riser into the end card, crash on the price.
place(mix, riser(0.9), 6.05, 0.7)
place(mix, crash(), 7.0, 0.8)
# SFX synced to c4.html.
for at in (2.4, 4.6, 6.75):
    place(mix, whoosh(), at, 0.8)
for at in (2.6, 2.85, 4.85, 5.1, 7.3, 7.6, 8.2):
    place(mix, pop(), at, 0.7)
for at in (8.6, 9.15):
    place(mix, tick(), at, 1.2)

# Master: fade out, soft clip, normalize.
fade = np.ones(N)
fl = int(0.6 * SR)
fade[-fl:] = np.linspace(1, 0, fl)
mix *= fade
mix = np.tanh(mix * 0.9)
mix /= np.max(np.abs(mix)) + 1e-9
mix *= 0.89

stereo = np.stack([mix, mix], axis=1)
pcm = (stereo * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok", sys.argv[1])
