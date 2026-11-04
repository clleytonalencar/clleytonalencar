#!/usr/bin/env python3
"""Gera DUAS faixas separadas a partir do timeline: trilha.wav (música de fundo) e sfx.wav (efeitos).
Separadas para o mix.py controlar o nível de cada uma (a voz nunca fica abaixo).

Uso:
  python3 trilha.py --timeline build/timeline.json --eventos eventos.json --out-dir build/audio [--estilo cinematico|chiptune]

eventos.json (tempos absolutos "t" ou relativos à cena "cena"+"p" 0..1):
  [ {"tipo": "maquina", "t": 0.1, "n": 18},
    {"tipo": "impacto", "cena": "terreno", "p": 0},
    {"tipo": "whoosh",  "cena": "cofre", "p": 0, "antes": 0.35},
    {"tipo": "serra",   "cena": "laje", "p": 0.3, "ate": 0.85},
    {"tipo": "estouro", "cena": "laje", "p": 0.86},
    {"tipo": "ticks",   "cena": "cofre", "p": 0.05, "ate": 0.95, "passo": 0.5},
    {"tipo": "alerta",  "cena": "fecho", "p": 0.2},
    {"tipo": "fim",     "t": -3.6} ]          # t negativo = a partir do fim
"""
import argparse, json, wave
from pathlib import Path
import numpy as np

SR = 48000


def write(path, x):
    x = np.clip(x / max(1e-9, np.abs(x).max()) * .9, -1, 1)
    pcm = (np.stack([x, x], 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeline", required=True); ap.add_argument("--eventos")
    ap.add_argument("--out-dir", required=True); ap.add_argument("--estilo", default="cinematico")
    a = ap.parse_args()
    TL = json.loads(Path(a.timeline).read_text(encoding="utf-8")); TOT = TL["total"]; N = int(TOT * SR)
    S = {s["id"]: s for i, s in enumerate(TL["scenes"])}
    ids = [s["id"] for s in TL["scenes"]]
    rng = np.random.default_rng(7)
    t = np.arange(N) / SR

    def at(ev):
        if "t" in ev: return ev["t"] if ev["t"] >= 0 else TOT + ev["t"]
        s = S[ev["cena"]]; i = ids.index(ev["cena"]); st = 0 if i == 0 else s["start"]; en = TOT if i == len(ids) - 1 else s["end"]
        return st + ev.get("p", 0) * (en - st) - ev.get("antes", 0)

    def until(ev):
        e2 = dict(ev); e2["p"] = ev["ate"]; e2.pop("antes", None); return at(e2)

    # ---------- música ----------
    mus = np.zeros(N)
    if a.estilo == "chiptune":
        hz = lambda m: 440 * 2 ** ((m - 69) / 12)
        bass = [45, 45, 48, 45, 43, 43, 40, 43, 41, 41, 45, 41, 40, 40, 44, 40]; e8 = 60 / 104 / 2; k = 0; tt = 2.0
        while tt < TOT - 3.6:
            n = int(e8 * .9 * SR); x = np.arange(n) / SR; i0 = int(tt * SR)
            seg_ = np.where((x * hz(bass[k % 16])) % 1 < .5, 1., -1.) * .5
            mus[i0:i0 + n] += seg_[:max(0, min(n, N - i0))]; tt += e8; k += 1
        mus = lowpass(mus, .25)  # tira o brilho que mascara a voz
    else:
        lfo = .6 + .4 * np.sin(2 * np.pi * t / 8)
        mus = (np.sin(2 * np.pi * 55 * t) * .5 + np.sin(2 * np.pi * 82.41 * t) * .3 + np.sin(2 * np.pi * 110 * t) * .15) * lfo
        mus += lowpass(rng.standard_normal(N), .015) * .8
        beat = 60 / 84  # pulso grave tipo "batida de coração"
        for b in np.arange(2.0, TOT - 3.6, beat):
            n = int(.35 * SR); x = np.arange(n) / SR; i0 = int(b * SR)
            p = np.sin(2 * np.pi * 50 * x) * np.exp(-x * 14) * .9; mus[i0:i0 + n] += p[:max(0, min(n, N - i0))]
    mus *= np.clip(t / 2.5, 0, 1) * np.clip((TOT - t) / 2.5, 0, 1)
    write(Path(a.out_dir) / "trilha.wav", mus)

    # ---------- efeitos ----------
    fx = np.zeros(N)
    def add(sig, start):
        i = int(start * SR); n = min(len(sig), N - i)
        if n > 0 and i >= 0: fx[i:i + n] += sig[:n]
    def env(n, dec): return np.exp(-np.arange(n) / SR * dec)
    def tick(f=2400, d=.03): n = int(d * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * f * x) * env(n, 200)
    def impacto(d=1.6, f=46): n = int(d * SR); x = np.arange(n) / SR; return np.sin(2 * np.pi * f * x * (1 - .25 * x)) * env(n, 3.2) + rng.standard_normal(n) * env(n, 60) * .4
    def whoosh(d=.7): n = int(d * SR); x = np.arange(n) / SR; return lowpass(rng.standard_normal(n), .08) * np.sin(np.pi * x / d) ** 2 * 2.5
    for ev in json.loads(Path(a.eventos).read_text(encoding="utf-8")) if a.eventos else []:
        s0, ty = at(ev), ev["tipo"]
        if ty == "maquina": [add(tick() * .6, s0 + i * .045) for i in range(ev.get("n", 18))]
        elif ty == "impacto": add(impacto() * ev.get("vol", .6), s0)
        elif ty == "whoosh": add(whoosh() * .5, s0)
        elif ty == "estouro": add(impacto(2.4, 38), s0)
        elif ty == "fim": add(impacto(3, 36) * .8, s0)
        elif ty == "alerta": [add(tick(f, .05) * .6, s0 + i * .06) for i, f in enumerate((660, 880, 1320))]
        elif ty == "ticks":
            k = s0
            while k < until(ev): add(tick() * .4, k); k += ev.get("passo", .5)
        elif ty == "serra":
            s1 = until(ev); n = int((s1 - s0) * SR); x = np.arange(n) / SR
            sig = ((((x * 180) % 1) - .5) * .5 + lowpass(rng.standard_normal(n), .3) * .4) * np.clip(x / .2, 0, 1) * np.clip((s1 - s0 - x) / .2, 0, 1)
            add(sig * .35, s0)
    write(Path(a.out_dir) / "sfx.wav", fx)
    print("trilha.wav + sfx.wav ->", a.out_dir)


if __name__ == "__main__":
    main()
