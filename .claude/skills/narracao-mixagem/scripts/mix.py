#!/usr/bin/env python3
"""Mixagem com níveis MEDIDOS: voz sempre bem acima da trilha.

Cadeia:
  voz    -> passa-alta 80 Hz, presença +3 dB em 3 kHz, compressor 3:1 -> ganho até VOZ_LUFS (−16)
  trilha -> passa-alta 40 Hz, buraco −6 dB em 1–4 kHz (espaço da voz) -> ganho até VOZ_LUFS − GAP (−30)
            -> ducking: abaixa mais ~8 dB enquanto a voz fala (sidechain)
  sfx    -> pico normalizado em −12 dBFS (impactos não brigam com a voz)
  mix    -> soma -> limitador −1 dBTP -> ganho até FINAL_LUFS (−14, padrão YouTube) -> limitador

No fim imprime um relatório e FALHA (exit 2) se a voz não ficar ≥ MIN_DIFF LU acima da trilha.

Uso:
  python3 mix.py --voz narracao.wav --trilha trilha.wav [--sfx sfx.wav] [--video video_mudo.mp4] --out final.mp4
  python3 mix.py ... --out final.wav            (só áudio)
Opções: --voz-lufs -16  --gap 14  --final-lufs -14  --min-diff 15
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def lufs(path):
    """loudness integrada (LUFS) e true peak (dBTP) via ebur128."""
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", r)
    p = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", r)
    val = lambda s: float("-inf") if s == "-inf" else float(s)
    return val(i[-1]) if i else float("-inf"), val(p[-1]) if p else float("-inf")


def peak(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s+(-?[\d.]+) dB", r)
    return float(m.group(1)) if m else 0.0


def gain_to(src, dst, target, pre=""):
    cur, _ = lufs(src)
    g = target - cur
    ff("-i", str(src), "-af", (pre + "," if pre else "") + f"volume={g:.2f}dB", "-ar", "48000", "-ac", "2", str(dst))
    return cur, g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voz", required=True); ap.add_argument("--trilha", required=True); ap.add_argument("--sfx")
    ap.add_argument("--video"); ap.add_argument("--out", required=True)
    ap.add_argument("--voz-lufs", type=float, default=-16); ap.add_argument("--gap", type=float, default=14)
    ap.add_argument("--final-lufs", type=float, default=-14); ap.add_argument("--min-diff", type=float, default=15)
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="mix_"))

    # 1) voz
    vproc = tmp / "voz_proc.wav"
    ff("-i", a.voz, "-af", "highpass=f=80,equalizer=f=3000:t=q:w=1.2:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2", "-ar", "48000", "-ac", "2", str(vproc))
    voz = tmp / "voz.wav"; v_in, _ = gain_to(vproc, voz, a.voz_lufs)

    # 2) trilha: EQ abre espaço para a voz, nível base, depois ducking
    tbase = tmp / "trilha_base.wav"
    t_in, _ = gain_to(a.trilha, tbase, a.voz_lufs - a.gap, "highpass=f=40,equalizer=f=2200:t=q:w=1.0:g=-6")
    tduck = tmp / "trilha_duck.wav"
    ff("-i", str(tbase), "-i", str(voz), "-filter_complex",
       "[0:a][1:a]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=350:makeup=1[d]", "-map", "[d]", str(tduck))

    # 3) efeitos
    inputs, labels = ["-i", str(voz), "-i", str(tduck)], ["[0:a]", "[1:a]"]
    if a.sfx:
        sfx = tmp / "sfx.wav"; pk = peak(a.sfx)
        ff("-i", a.sfx, "-af", f"volume={-12 - pk:.2f}dB", "-ar", "48000", "-ac", "2", str(sfx))
        inputs += ["-i", str(sfx)]; labels.append("[2:a]")

    # 4) soma -> limitador -> ganho final -> limitador
    raw = tmp / "mix_raw.wav"
    ff(*inputs, "-filter_complex", f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.89:level=false[m]", "-map", "[m]", str(raw))
    final_wav = tmp / "mix.wav"
    gain_to(raw, final_wav, a.final_lufs, "")
    final2 = tmp / "mix_lim.wav"; ff("-i", str(final_wav), "-af", "alimiter=limit=0.89:level=false", str(final2))

    out = Path(a.out)
    if a.video:
        ff("-i", a.video, "-i", str(final2), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out))
    else:
        ff("-i", str(final2), str(out))

    # 5) relatório
    v_l, _ = lufs(voz); t_l, _ = lufs(tduck); f_l, f_p = lufs(final2)
    diff = v_l - t_l
    rep = {"voz_entrada_LUFS": v_in, "trilha_entrada_LUFS": t_in, "voz_LUFS": round(v_l, 1), "trilha_ducked_LUFS": round(t_l, 1),
           "voz_acima_da_trilha_LU": round(diff, 1), "final_LUFS": round(f_l, 1), "final_true_peak_dBFS": f_p, "saida": str(out)}
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    (out.parent / (out.stem + "_mix.json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    if diff < a.min_diff:
        print(f"REPROVADO: voz só {diff:.1f} LU acima da trilha (mínimo {a.min_diff}). Aumente --gap.", file=sys.stderr); sys.exit(2)
    print(f"APROVADO: voz {diff:.1f} LU acima da trilha; final {f_l:.1f} LUFS.")


if __name__ == "__main__":
    main()
