"""Utilitários: ffprobe, fontes, tipos de mídia, execução do ffmpeg."""
import hashlib
import json
import os
import shutil
import subprocess
import textwrap

EXT_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
EXT_VIDEO = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}

FORMATOS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}


class ErroEditor(Exception):
    pass


def checar_ffmpeg():
    for b in ("ffmpeg", "ffprobe"):
        if not shutil.which(b):
            raise ErroEditor(f"'{b}' não encontrado no PATH. Instale o ffmpeg.")


def tipo_midia(caminho):
    if caminho.startswith("cor:"):
        return "cor"
    ext = os.path.splitext(caminho)[1].lower()
    if ext in EXT_IMAGEM:
        return "imagem"
    if ext in EXT_VIDEO:
        return "video"
    raise ErroEditor(f"Tipo de mídia não suportado: {caminho}")


def duracao(caminho):
    """Duração em segundos de um arquivo de áudio ou vídeo (0 para imagem)."""
    if caminho.startswith("cor:") or tipo_midia_segura(caminho) == "imagem":
        return 0.0
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", caminho],
        capture_output=True, text=True,
    )
    try:
        return float(json.loads(r.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        raise ErroEditor(f"Não consegui ler a duração de {caminho}")


def tipo_midia_segura(caminho):
    try:
        return tipo_midia(caminho)
    except ErroEditor:
        return "audio"


def tem_audio(caminho):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", caminho],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def achar_fonte(peso="bold"):
    nomes = {
        "bold": ["Inter Display:extrabold", "Inter:bold", "DejaVu Sans:bold"],
        "regular": ["Inter:medium", "Inter", "DejaVu Sans"],
    }[peso]
    if shutil.which("fc-match"):
        for n in nomes:
            r = subprocess.run(["fc-match", "-f", "%{file}", n], capture_output=True, text=True)
            if r.stdout and os.path.exists(r.stdout):
                return r.stdout
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        if os.path.exists(p):
            return p
    raise ErroEditor("Nenhuma fonte encontrada. Defina 'fonte' no projeto.")


def cor_ff(cor):
    """'#E2A900' -> '0xE2A900' (aceita também nomes do ffmpeg e sufixo @alpha)."""
    if cor.startswith("#"):
        base, _, alpha = cor[1:].partition("@")
        return "0x" + base + (f"@{alpha}" if alpha else "")
    return cor


def par(n):
    n = int(round(n))
    return n - (n % 2)


def quebrar(texto, largura_px, tam):
    chars = max(8, int(largura_px / (tam * 0.55)))
    linhas = []
    for paragrafo in str(texto).split("\n"):
        linhas += textwrap.wrap(paragrafo, chars) or [""]
    return "\n".join(linhas)


def hash_dados(*partes):
    h = hashlib.sha1()
    for p in partes:
        h.update(json.dumps(p, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def assinatura_arquivo(caminho):
    if not caminho or caminho.startswith("cor:") or not os.path.exists(caminho):
        return caminho
    st = os.stat(caminho)
    return f"{caminho}|{st.st_size}|{int(st.st_mtime)}"


def rodar(args, descricao=""):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        log = os.environ.get("FABRICA_DEBUG") and " ".join(args) or ""
        raise ErroEditor(f"ffmpeg falhou {descricao}:\n{r.stderr[-3000:]}\n{log}")
    return r
