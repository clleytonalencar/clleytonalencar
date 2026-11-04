#!/usr/bin/env python3
"""QA visual: tira quadros do vídeo e monta uma folha em TAMANHO DE CELULAR.
Se você não consegue ler a legenda/etiquetas nesta folha, o espectador também não vai.

Uso: python3 qa_quadros.py video.mp4 [--cada 4] [--largura 480] [--out folha.jpg]
"""
import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--cada", type=float, default=4)
    ap.add_argument("--largura", type=int, default=480, help="largura de cada quadro (480 ≈ vídeo deitado num celular)")
    ap.add_argument("--out"); a = ap.parse_args()
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video]).decode())
    tmp = Path(tempfile.mkdtemp()); frames = []
    t = 1.0
    while t < dur - .2:
        f = tmp / f"f{t:06.1f}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", a.video, "-frames:v", "1", "-vf", f"scale={a.largura}:-2", str(f)], check=True)
        frames.append(f); t += a.cada
    w, h = Image.open(frames[0]).size; cols = 4; rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "black")
    for i, f in enumerate(frames): sheet.paste(Image.open(f), ((i % cols) * w, (i // cols) * h))
    out = a.out or str(Path(a.video).with_suffix("")) + "_qa.jpg"; sheet.save(out, quality=88); print(out, f"({len(frames)} quadros)")


if __name__ == "__main__":
    main()
