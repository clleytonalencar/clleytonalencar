#!/usr/bin/env python3
"""Narração cena a cena + timeline.json (tempos de cada cena e legendas por frase).

Uso:
  python3 tts.py --scenes scenes.json --out-dir build [--voice pt-BR-AntonioNeural] [--rate +18%] [--gap .35]

scenes.json: [{"id": "gancho", "text": "..."}, ...]
Saídas: <out-dir>/audio/<id>.mp3, <out-dir>/audio/narracao.wav, <out-dir>/timeline.json

Voz de protótipo: edge-tts (vozes online da Microsoft, licença comercial não garantida).
Para vídeo monetizado, grave voz humana ou use serviço com licença e substitua narracao.wav
(mantendo os tempos — ou regenere o timeline a partir do áudio novo com --from-audio).
"""
import argparse, asyncio, json, re, subprocess
from pathlib import Path

try:  # proxy de ambientes corporativos/cloud que re-assinam TLS
    import certifi
    if Path("/root/.ccr/ca-bundle.crt").exists():
        certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
except ImportError:
    pass
import edge_tts


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).decode())


def parse_srt(text):
    def ts(s):
        h, m, r = s.split(":"); sec, ms = r.split(","); return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
    out = []
    for b in re.split(r"\n\s*\n", text.strip()):
        L = b.strip().splitlines()
        if len(L) >= 3:
            x, y = L[1].split(" --> "); out.append({"start": ts(x), "end": ts(y), "text": " ".join(L[2:])})
    return out


async def speak(text, voice, rate, mp3, srt):
    com = edge_tts.Communicate(text, voice, rate=rate, boundary="SentenceBoundary"); sub = edge_tts.SubMaker()
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] in ("WordBoundary", "SentenceBoundary"): sub.feed(ch)
    Path(srt).write_text(sub.get_srt(), encoding="utf-8")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--voice", default="pt-BR-AntonioNeural"); ap.add_argument("--rate", default="+15%")
    ap.add_argument("--gap", type=float, default=.35); ap.add_argument("--lead", type=float, default=.6); ap.add_argument("--tail", type=float, default=.9)
    a = ap.parse_args()
    out = Path(a.out_dir); aud = out / "audio"; aud.mkdir(parents=True, exist_ok=True)
    scenes = json.loads(Path(a.scenes).read_text(encoding="utf-8"))
    t, tl, parts = a.lead, [], []
    for sc in scenes:
        mp3, srt = aud / f"{sc['id']}.mp3", aud / f"{sc['id']}.srt"
        await speak(sc["text"], a.voice, a.rate, mp3, srt)
        d = dur(mp3)
        cues = [{**c, "start": c["start"] + t, "end": c["end"] + t} for c in parse_srt(srt.read_text(encoding="utf-8"))]
        tl.append({"id": sc["id"], "start": t, "speech": d, "end": t + d + a.gap, "cues": cues}); parts.append((mp3, t)); t += d + a.gap
    total = t + a.tail
    ins, fl = [], []
    for i, (mp3, st) in enumerate(parts):
        ins += ["-i", str(mp3)]; fl.append(f"[{i}:a]adelay={int(st*1000)}|{int(st*1000)},aresample=48000[a{i}]")
    fl.append("".join(f"[a{i}]" for i in range(len(parts))) + f"amix=inputs={len(parts)}:normalize=0,apad,atrim=0:{total:.3f}[o]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[o]", "-ac", "2", str(aud / "narracao.wav")], check=True)
    (out / "timeline.json").write_text(json.dumps({"total": total, "scenes": tl}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"total {total:.2f}s"); [print(f"  {s['id']:10s} {s['start']:6.2f} -> {s['end']:6.2f}") for s in tl]

asyncio.run(main())
