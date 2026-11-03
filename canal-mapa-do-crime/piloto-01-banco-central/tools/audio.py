"""Trilha sintetizada (drone + impactos + efeitos) sincronizada ao timeline.
Gera build/audio/trilha.wav e mixa com a narração em build/piloto-01.mp4."""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
TL = json.loads((B / "timeline.json").read_text(encoding="utf-8"))
SR = 48000
N = int(TL["total"] * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(5)
S = {s["id"]: s for s in TL["scenes"]}
out = np.zeros((N, 2))


def lowpass(x, a):  # filtro 1 polo simples
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); n = min(len(sig), N - i)
    if n <= 0: return
    out[i:i + n, 0] += sig[:n] * gain * (1 - pan) ** .5
    out[i:i + n, 1] += sig[:n] * gain * (1 + pan) ** .5

# drone grave com pulsação lenta
lfo = .6 + .4 * np.sin(2 * np.pi * t / 7.5)
drone = (np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.41 * t) * .25 + np.sin(2 * np.pi * 110.3 * t) * .12) * lfo
air = lowpass(rng.standard_normal(N), .02) * .6
fade = np.clip(t / 2.5, 0, 1) * np.clip((TL["total"] - t) / 2.0, 0, 1)
bed = (drone + air) * fade * .22
out[:, 0] += bed; out[:, 1] += bed * .96

def impact(dur=1.6, f=48):
    n = int(dur * SR); x = np.arange(n) / SR
    body = np.sin(2 * np.pi * f * x * (1 - .25 * x)) * np.exp(-x * 3.2)
    click = rng.standard_normal(n) * np.exp(-x * 60) * .5
    return body + click

def whoosh(dur=.7):
    n = int(dur * SR); x = np.arange(n) / SR
    env = np.sin(np.pi * x / dur) ** 2
    return lowpass(rng.standard_normal(n), .08) * env * 3

def tick():
    n = int(.03 * SR); x = np.arange(n) / SR
    return np.sin(2 * np.pi * 2400 * x) * np.exp(-x * 220)

# máquina de escrever na abertura
for i in range(18):
    add(tick() * .5, .1 + i * .045, .5, pan=rng.uniform(-.3, .3))
add(impact(2.2, 42), 1.75, .9)
# impacto em cada virada de cena + whoosh nas trocas de "mundo"
for sid in ["terreno", "fachada", "tunel", "esgoto", "laje", "cofre", "fecho"]:
    add(impact(), S[sid]["start"] - .02, .55)
for sid in ["tunel", "cofre", "fecho"]:
    add(whoosh(), S[sid]["start"] - .35, .35)
# serra na laje
la = S["laje"]; dur = la["end"] - la["start"]
s0, s1 = la["start"] + .3 * dur, la["start"] + .85 * dur
n = int((s1 - s0) * SR); x = np.arange(n) / SR
saw = (((x * 180) % 1) - .5) * .6 + lowpass(rng.standard_normal(n), .3) * .4
saw *= np.clip(x / .2, 0, 1) * np.clip((s1 - s0 - x) / .2, 0, 1) * (.7 + .3 * np.sin(2 * np.pi * 7 * x))
add(saw, s0, .22, pan=.2)
add(impact(2.4, 38), la["start"] + .86 * dur, 1.0)
# relógio correndo no cofre
co = S["cofre"]
k = co["start"] + .2
while k < co["end"] - .2:
    add(tick(), k, .35, pan=.4); k += .25
# card final
add(impact(3, 36), TL["total"] - 3.6, .9)

out /= max(1e-9, np.abs(out).max()) / .9
pcm = (out * 32767).astype("<i2")
with wave.open(str(B / "audio" / "trilha.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("trilha ok")

import sys
if "--mix" in sys.argv:
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-i", str(B / "video_mudo.mp4"), "-i", str(B / "audio" / "narracao.wav"), "-i", str(B / "audio" / "trilha.wav"),
        "-filter_complex",
        "[1:a]highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,asplit=2[v][vsc];"
        "[2:a]volume=0.20[m];[m][vsc]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"
        "[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", str(B / "piloto-01-banco-central.mp4")])
    print("mix ok")
