"""Gera a narração cena a cena (edge-tts) e um timeline.json com duração e legendas.
Uso: python3 tools/tts.py [voz] [rate]"""
import asyncio, json, re, subprocess, sys
from pathlib import Path

try:  # o proxy do ambiente re-assina TLS; usa o bundle dele se existir
    import certifi
    if Path("/root/.ccr/ca-bundle.crt").exists():
        certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
except ImportError:
    pass
import edge_tts

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "audio"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "pt-BR-AntonioNeural"
RATE = sys.argv[2] if len(sys.argv) > 2 else "+0%"
GAP = 0.35  # respiro entre cenas (s)


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]).decode())


async def one(scene):
    mp3, srt = OUT / f"{scene['id']}.mp3", OUT / f"{scene['id']}.srt"
    com = edge_tts.Communicate(scene["text"], VOICE, rate=RATE, boundary="SentenceBoundary")
    sub = edge_tts.SubMaker()
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                sub.feed(chunk)
    srt.write_text(sub.get_srt(), encoding="utf-8")
    return mp3, srt


def parse_srt(text):
    def ts(s):
        h, m, rest = s.split(":"); sec, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            a, b = lines[1].split(" --> ")
            cues.append({"start": ts(a), "end": ts(b), "text": " ".join(lines[2:])})
    return cues


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = json.loads((ROOT / "scenes.json").read_text(encoding="utf-8"))
    t, timeline, concat = 0.6, [], []  # 0.6 s de abertura antes da 1a fala
    for sc in scenes:
        mp3, srt = await one(sc)
        d = dur(mp3)
        cues = [{**c, "start": c["start"] + t, "end": c["end"] + t} for c in parse_srt(srt.read_text(encoding="utf-8"))]
        timeline.append({"id": sc["id"], "start": t, "speech": d, "end": t + d + GAP, "cues": cues})
        concat.append((mp3, t))
        t += d + GAP
    total = t + 0.9  # cauda para o card final
    # monta narração única posicionada no tempo
    inputs, filters = [], []
    for i, (mp3, start) in enumerate(concat):
        inputs += ["-i", str(mp3)]
        filters.append(f"[{i}:a]adelay={int(start*1000)}|{int(start*1000)},aresample=48000[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(concat)))
    filters.append(f"{mix}amix=inputs={len(concat)}:normalize=0,apad,atrim=0:{total:.3f}[out]")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filters),
                           "-map", "[out]", "-ac", "2", str(OUT / "narracao.wav")])
    (ROOT / "build" / "timeline.json").write_text(json.dumps({"total": total, "scenes": timeline}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"total {total:.2f}s")
    for s in timeline:
        print(f"  {s['id']:8s} {s['start']:6.2f} -> {s['end']:6.2f}")

asyncio.run(main())
