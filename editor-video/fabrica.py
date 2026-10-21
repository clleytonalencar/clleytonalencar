#!/usr/bin/env python3
"""Fábrica de Vídeos — editor por linha de comando sobre ffmpeg.

Comandos:
  modelos                         lista os modelos de cena
  catalogo [-o catalogo.png]      gera a folha de miniaturas dos modelos (como a grade do editor)
  auto ROTEIRO -p PREDEF [-o projeto.json]
                                  distribui modelos/transições/movimentos/filtros conforme os eixos
  render PROJETO [-o video.mp4] [--preview] [--cena N]
                                  renderiza o projeto (ou só a cena N)
  demo                            gera mídias de teste, monta e renderiza um vídeo de exemplo
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from motor.auto import gerar_projeto, resumo  # noqa: E402
from motor.modelos import MODELOS  # noqa: E402
from motor.render import FILTROS, TRANSICOES, Projeto  # noqa: E402
from motor.cena import MOVIMENTOS  # noqa: E402
from motor.util import ErroEditor, achar_fonte, checar_ffmpeg, rodar  # noqa: E402

CORES_PLACEHOLDER = ["#e5484d", "#30a46c", "#8e4ec6", "#f76b15", "#ffc53d", "#0090ff"]
TEXTOS_EXEMPLO = {
    "texto": "O caso que chocou o mundo", "subtexto": "Tennessee, 1995", "rotulos": ["1995", "2001", "2013", "2026"],
    "titulo_janela": "arquivo_policial.jpg",
}


def ler_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def salvar_json(p, d):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def cmd_modelos(_):
    print(f"{'CHAVE':<17}{'SELO':<13}{'NOME':<22}{'MÍDIAS':<8}DESCRIÇÃO")
    for m in MODELOS.values():
        lo, hi = m.slots
        sl = f"{lo}" if lo == hi else f"{lo}-{hi}"
        print(f"{m.chave:<17}{m.categoria:<13}{m.nome:<22}{sl:<8}{m.descricao}")
    print("\nTransições:", ", ".join(TRANSICOES))
    print("Movimentos:", ", ".join(MOVIMENTOS))
    print("Filtros:   ", ", ".join(FILTROS))


def cmd_catalogo(a):
    checar_ffmpeg()
    tmp = tempfile.mkdtemp(prefix="catalogo_")
    chaves = list(MODELOS)
    fonte = achar_fonte("bold")
    try:
        cenas = []
        k = 0
        for ch in chaves:
            lo, hi = MODELOS[ch].slots
            n = max(lo, min(hi, 3 if ch in ("pilha", "linha_do_tempo") else (4 if ch == "grade" else lo)))
            if ch == "tela_cheia":
                n = 1
            midias = []
            for _ in range(n):
                midias.append("cor:" + CORES_PLACEHOLDER[k % len(CORES_PLACEHOLDER)])
                k += 1
            cena = dict(TEXTOS_EXEMPLO, modelo=ch, midias=midias, duracao=2.6, transicao="corte")
            if ch == "placa":
                cena["texto"] = "17 ANOS NO SÓTÃO"
            cenas.append(cena)
        proj = Projeto({"formato": "16:9", "cenas": cenas}, tmp, preview=True)

        def thumb(i):
            mp4 = os.path.join(tmp, f"c{i:03d}.mp4")
            proj.render_cena(i, 2.6, mp4, False)
            m = MODELOS[chaves[i]]
            lo, hi = m.slots
            sl = str(lo) if lo == hi else f"{lo}-{hi}"
            png = os.path.join(tmp, f"t{i:03d}.png")
            for nome, txt in (("selo", m.categoria), ("nome", m.nome), ("slots", sl)):
                with open(os.path.join(tmp, f"{nome}{i}.txt"), "w", encoding="utf-8") as f:
                    f.write(txt)
            vf = (f"scale=384:216,pad=384:262:0:0:color=0x0d0f14,"
                  f"drawtext=fontfile='{fonte}':textfile='{tmp}/selo{i}.txt':fontsize=17:fontcolor=white:box=1:"
                  f"boxcolor=black@0.7:boxborderw=7:x=12:y=216-text_h-14,"
                  f"drawtext=fontfile='{fonte}':textfile='{tmp}/slots{i}.txt':fontsize=17:fontcolor=white:box=1:"
                  f"boxcolor=0x0b3b66@0.9:boxborderw=7:x=12:y=12,"
                  f"drawtext=fontfile='{fonte}':textfile='{tmp}/nome{i}.txt':fontsize=21:fontcolor=white@0.9:x=4:y=229")
            rodar(["ffmpeg", "-y", "-loglevel", "error", "-ss", "2.4", "-i", mp4, "-frames:v", "1", "-vf", vf, png])
            print(f"  {chaves[i]}")

        with ThreadPoolExecutor(max(1, (os.cpu_count() or 2) // 2)) as ex:
            list(ex.map(thumb, range(len(chaves))))
        colunas = 5
        linhas = -(-len(chaves) // colunas)
        for j in range(len(chaves), colunas * linhas):  # completa a última linha
            rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=0x0d0f14:s=384x262",
                   "-frames:v", "1", os.path.join(tmp, f"t{j:03d}.png")])
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1", "-i", os.path.join(tmp, "t%03d.png"),
               "-vf", f"tile={colunas}x{linhas}:padding=14:margin=18:color=0x0d0f14", "-frames:v", "1", a.saida])
        print(f"Catálogo salvo em {a.saida}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_auto(a):
    roteiro = ler_json(a.roteiro)
    pre = ler_json(a.predefinicao)
    proj = gerar_projeto(roteiro, pre)
    saida = a.saida or os.path.splitext(a.roteiro)[0] + ".projeto.json"
    # caminhos do roteiro continuam relativos à pasta do roteiro
    if os.path.dirname(os.path.abspath(saida)) != os.path.dirname(os.path.abspath(a.roteiro)):
        raise ErroEditor("Salve o projeto na mesma pasta do roteiro (os caminhos das mídias são relativos a ela).")
    salvar_json(saida, proj)
    print(resumo(proj))
    print(f"\nProjeto salvo em {saida}")
    if a.render:
        a.projeto, a.saida = saida, os.path.splitext(saida)[0] + ".mp4"
        a.cena = None
        cmd_render(a)


def cmd_render(a):
    checar_ffmpeg()
    dados = ler_json(a.projeto)
    proj = Projeto(dados, os.path.dirname(os.path.abspath(a.projeto)), preview=a.preview)
    saida = a.saida or os.path.splitext(a.projeto)[0] + (".preview" if a.preview else "") + ".mp4"
    so = None if a.cena is None else a.cena - 1
    print(f"Renderizando {len(proj.cenas)} cena(s) em {proj.W}x{proj.H} @ {proj.fps}fps")
    proj.render(saida, so=so)
    print(f"Vídeo salvo em {saida}")


def cmd_demo(a):
    checar_ffmpeg()
    pasta = os.path.join(AQUI, "exemplos")
    midia = os.path.join(pasta, "demo")
    os.makedirs(midia, exist_ok=True)
    fonte = achar_fonte("bold")
    print("Gerando mídias de teste em exemplos/demo ...")
    pares = [("0x1b2a49", "0x6b8cce"), ("0x4a1c1c", "0xd9822b"), ("0x16302b", "0x5fb49c"), ("0x2d1b4e", "0xb48ead"),
             ("0x3b3b3b", "0xcfcfcf"), ("0x402a10", "0xe2a900"), ("0x102a40", "0x58a6ff"), ("0x40101e", "0xff6b81")]
    for k, (c0, c1) in enumerate(pares, 1):
        with open(os.path.join(midia, f"rot{k}.txt"), "w", encoding="utf-8") as f:
            f.write(f"FOTO {k}")
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
               f"gradients=s=1600x1000:c0={c0}:c1={c1}:x0=0:y0=0:x1=1600:y1=1000:seed={k}",
               "-vf", f"drawtext=fontfile='{fonte}':textfile='{midia}/rot{k}.txt':fontsize=150:fontcolor=white@0.85:"
                      f"x=(w-text_w)/2:y=(h-text_h)/2", "-frames:v", "1", os.path.join(midia, f"foto{k}.jpg")])
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=1280x720:d=6:r=30",
           "-pix_fmt", "yuv420p", os.path.join(midia, "video1.mp4")])
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "mandelbrot=s=720x720:r=30",
           "-t", "8", "-pix_fmt", "yuv420p", os.path.join(midia, "avatar.mp4")])
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
           "color=c=black@0:s=360x140,format=rgba", "-vf",
           f"drawtext=fontfile='{fonte}':text='FÁBRICA':fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
           "-frames:v", "1", os.path.join(midia, "logo.png")])
    for k, d in enumerate([3.5, 4.0, 4.5, 3.8, 4.2, 5.0, 3.6, 4.4, 4.0], 1):
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
               f"sine=f={180 + 20 * k}:d={d},volume=0.04", "-ac", "2", os.path.join(midia, f"narracao{k}.wav")])
    rodar(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
           "aevalsrc='0.2*sin(2*PI*110*t)*(0.6+0.4*sin(2*PI*0.25*t))+0.15*sin(2*PI*165*t)':s=48000:d=40",
           "-ac", "2", os.path.join(midia, "trilha.wav")])

    roteiro_p = os.path.join(pasta, "roteiro-exemplo.json")
    pre_p = os.path.join(AQUI, "predefinicoes", "documentario-classico.json")
    proj = gerar_projeto(ler_json(roteiro_p), ler_json(pre_p))
    proj_p = os.path.join(pasta, "roteiro-exemplo.projeto.json")
    salvar_json(proj_p, proj)
    print(resumo(proj))
    a.projeto, a.cena = proj_p, None
    a.saida = os.path.join(pasta, "demo.preview.mp4" if a.preview else "demo.mp4")
    cmd_render(a)


def main():
    p = argparse.ArgumentParser(description="Fábrica de Vídeos — editor por linha de comando (ffmpeg)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("modelos", help="lista os modelos de cena").set_defaults(fn=cmd_modelos)
    s = sub.add_parser("catalogo", help="gera a folha de miniaturas dos modelos")
    s.add_argument("-o", "--saida", default="catalogo.png")
    s.set_defaults(fn=cmd_catalogo)
    s = sub.add_parser("auto", help="roteiro + predefinição -> projeto")
    s.add_argument("roteiro")
    s.add_argument("-p", "--predefinicao", required=True)
    s.add_argument("-o", "--saida")
    s.add_argument("--render", action="store_true", help="renderiza logo em seguida")
    s.add_argument("--preview", action="store_true")
    s.set_defaults(fn=cmd_auto)
    s = sub.add_parser("render", help="renderiza um projeto")
    s.add_argument("projeto")
    s.add_argument("-o", "--saida")
    s.add_argument("--preview", action="store_true", help="metade da resolução, encode rápido")
    s.add_argument("--cena", type=int, help="renderiza só a cena N (1 = primeira)")
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser("demo", help="gera mídias de teste e renderiza um exemplo")
    s.add_argument("--preview", action="store_true")
    s.set_defaults(fn=cmd_demo)
    a = p.parse_args()
    try:
        a.fn(a)
    except ErroEditor as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
