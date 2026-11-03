"""Trilha chiptune (8-bit) + efeitos de "jogo" para a versão pixel, mixada com a narração.
Saída: build/piloto-01-pixel.mp4 (usa build/video_mudo_px.mp4 e build/audio/narracao.wav)."""
import json, subprocess, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "build"
TL = json.loads((B / "timeline.json").read_text(encoding="utf-8"))
SR = 48000; TOT = TL["total"]; N = int(TOT * SR)
S = {s["id"]: s for s in TL["scenes"]}
out = np.zeros(N)
rng = np.random.default_rng(1)

def hz(note):  # 'A2', 'G#2'
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    n, o = note[:-1], int(note[-1]); return 440 * 2 ** ((names[n] + (o - 4) * 12) / 12)

def square(f, dur, duty=.5, vol=1.0):
    n = int(dur * SR); x = np.arange(n) / SR; w = np.where((x * f) % 1 < duty, 1.0, -1.0)
    env = np.minimum(1, np.minimum(np.arange(n) / 80, (n - np.arange(n)) / 400)); return w * env * vol

def add(sig, at):
    i = int(at * SR); n = min(len(sig), N - i)
    if n > 0 and i >= 0: out[i:i + n] += sig[:n]

BPM = 104; beat = 60 / BPM; e8 = beat / 2
bass = ['A2', 'A2', 'C3', 'A2', 'G2', 'G2', 'E2', 'G2', 'F2', 'F2', 'A2', 'F2', 'E2', 'E2', 'G#2', 'E2']
arp = [['A4', 'C5', 'E5'], ['G4', 'B4', 'D5'], ['F4', 'A4', 'C5'], ['E4', 'G#4', 'B4']]
start = 2.0; t = start; i = 0
while t < TOT - 3.6:
    add(square(hz(bass[i % 16]), e8 * .9, .5, .16), t)
    if t > S["terreno"]["start"]:  # arpejo entra depois do gancho
        chord = arp[(i // 4) % 4]
        for k in range(2): add(square(hz(chord[(i * 2 + k) % 3]), e8 / 2 * .8, .25, .05), t + k * e8 / 2)
    if i % 2 == 1:  # chimbal de ruído
        n = int(.03 * SR); add(rng.standard_normal(n) * np.exp(-np.arange(n) / 300) * .05, t)
    t += e8; i += 1

# efeitos
for k in range(18): add(square(1200, .02, .5, .08), .1 + k * .045)           # máquina de escrever
def blip(at, f0=440, f1=880): add(np.concatenate([square(f0, .05, .5, .12), square(f1, .07, .5, .12)]), at)
for sid in ["terreno", "fachada", "tunel", "esgoto", "laje", "cofre", "fecho"]: blip(S[sid]["start"])
def alert(at):
    sig = np.concatenate([square(f, .035, .5, .14) for f in (660, 880, 1320, 1760)]); add(sig, at)
es = S["esgoto"]; ed = es["end"] - es["start"]; alert(es["start"] + .1 * ed)
fe = S["fecho"]; fd = TOT - fe["start"]; alert(fe["start"] + .25 * fd)
la = S["laje"]; ld = la["end"] - la["start"]
s0, s1 = la["start"] + .3 * ld, la["start"] + .85 * ld; n = int((s1 - s0) * SR); x = np.arange(n) / SR
saw = np.where((x * 95) % 1 < .5, 1., -1.) * (.6 + .4 * np.sin(2 * np.pi * 9 * x)) * .07
add(saw, s0)
n = int(.6 * SR); add(rng.standard_normal(n) * np.exp(-np.arange(n) / 6000) * .35, la["start"] + .86 * ld)  # explosão 8-bit
co = S["cofre"]; tt = co["start"] + .3
while tt < co["end"] - .3: add(square(1800, .015, .5, .05), tt); tt += .5      # relógio
end = TOT - 3.6
for k, nt in enumerate(['A4', 'C5', 'E5', 'A5', 'E5', 'A5']): add(square(hz(nt), .12, .5, .12), end + k * .12)

out = np.clip(out / max(1e-9, np.abs(out).max()) * .9, -1, 1)
st = np.stack([out, out], 1); pcm = (st * 32767).astype('<i2')
with wave.open(str(B / "audio" / "trilha_pixel.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
subprocess.check_call([
    "ffmpeg", "-y", "-v", "error", "-i", str(B / "video_mudo_px.mp4"), "-i", str(B / "audio" / "narracao.wav"), "-i", str(B / "audio" / "trilha_pixel.wav"),
    "-filter_complex",
    "[1:a]highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,asplit=2[v][vsc];"
    "[2:a]volume=0.32[m];[m][vsc]sidechaincompress=threshold=0.05:ratio=5:attack=20:release=300[md];"
    "[v][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
    str(B / "piloto-01-pixel.mp4")])
print("ok")
