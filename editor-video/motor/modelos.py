"""Catálogo de modelos de cena (os "cartões" do editor).

Cada modelo recebe o construtor `c` (Cena) e o dicionário da cena e devolve o
rótulo do vídeo final. Campos comuns da cena: texto, subtexto, rotulos (lista).
"""
from dataclasses import dataclass
from typing import Callable


@dataclass
class Modelo:
    chave: str
    categoria: str      # selo exibido no catálogo (MOLDURA, DOSSIE, VERSUS...)
    nome: str           # nome exibido
    slots: tuple        # (mínimo, máximo) de mídias
    dur_padrao: float   # duração quando não há narração nem vídeo
    montar: Callable
    descricao: str = ""
    texto_embaixo: bool = False  # o modelo usa a faixa de baixo -> legenda sobe


MODELOS = {}


def modelo(chave, categoria, nome, slots, dur=4.0, descricao="", texto_embaixo=False):
    def reg(fn):
        MODELOS[chave] = Modelo(chave, categoria, nome, slots, dur, fn, descricao, texto_embaixo)
        return fn
    return reg


def _rotulo(cena, i, padrao=""):
    r = cena.get("rotulos") or []
    return r[i] if i < len(r) and r[i] else padrao


def _vertical(c):
    return c.H > c.W


def _distribuir(c, n, faixa=0.78):
    """Centros de n itens ao longo do eixo principal (horizontal em 16:9, vertical em 9:16)."""
    total = (c.H if _vertical(c) else c.W) * faixa
    ini = ((c.H if _vertical(c) else c.W) - total) / 2
    passo = total / n
    return [ini + passo * (k + 0.5) for k in range(n)]


def _legenda_inferior(c, base, cena, atraso=0.6):
    """Título + subtítulo na parte de baixo (usado por vários modelos)."""
    base = c.texto(base, cena.get("texto"), "(w-text_w)/2", f"h-{int(190 * c.u)}", tam=52, atraso=atraso,
                   largura=c.W * 0.8)
    return c.texto(base, cena.get("subtexto"), "(w-text_w)/2", f"h-{int(110 * c.u)}", tam=30, negrito=False,
                   cor="white@0.8", atraso=atraso + 0.2, largura=c.W * 0.8)


# ---------------------------------------------------------------- CENA (limpa)
@modelo("tela_cheia", "CENA", "Tela Cheia", (1, 6), 4.0, "Mídia em tela cheia; várias mídias viram sequência de cortes.", texto_embaixo=True)
def tela_cheia(c, cena):
    n = len(c.midias)
    fatia = c.dur / n
    base = None
    for i in range(n):
        lab = c.midia(i, c.W, c.H, movimento=c.movimento)
        out = c.rotulo()
        if base is None:
            c.add(f"{lab}format=yuv420p{out}")
        else:
            c.add(f"{base}{lab}overlay=0:0:enable='gte(t,{i * fatia:.3f})'{out}")
        base = out
    if cena.get("texto"):
        g = c.bloco(c.W, int(c.H * 0.32), "#000000", 0.45)
        o = c.rotulo()
        c.add(f"{base}{g}overlay=0:H-h{o}")
        base = _legenda_inferior(c, o, cena)
    return base


@modelo("abertura", "CENA", "Abertura", (0, 1), 4.5, "Título grande com barra de destaque; mídia opcional desfocada ao fundo.")
def abertura(c, cena):
    base = c.fundo_midia(0) if c.midias else c.fundo()
    barra = c.bloco(c.W * 0.12, 10 * c.u, c.cor)
    base = c.colocar(base, barra, c.W / 2, c.H * 0.58, atraso=0.5, entrada="esquerda")
    base = c.texto(base, cena.get("texto", "TÍTULO"), "(w-text_w)/2", f"h*0.58-text_h-{int(40 * c.u)}", tam=96,
                   atraso=0.15, largura=c.W * 0.85)
    return c.texto(base, cena.get("subtexto"), "(w-text_w)/2", f"h*0.58+{int(40 * c.u)}", tam=36, negrito=False,
                   cor="white@0.8", atraso=0.7, largura=c.W * 0.7)


# ---------------------------------------------------------------- MOLDURA
@modelo("moldura", "MOLDURA", "Moldura Editorial", (1, 1), 4.0, "Mídia em moldura branca centralizada, com sombra.", texto_embaixo=True)
def moldura(c, cena):
    base = c.fundo()
    tem_txt = bool(cena.get("texto"))
    w, h = c.W * 0.70, c.H * (0.62 if tem_txt else 0.72)
    card = c.cartao(0, w, h, borda=10, rot=cena.get("rotacao", 0))
    base = c.colocar(base, card, c.W / 2, c.H * (0.44 if tem_txt else 0.5), atraso=0.05)
    return _legenda_inferior(c, base, cena) if tem_txt else base


@modelo("janela", "MOLDURA", "Janela", (1, 1), 4.0, "Mídia dentro de uma janela de sistema (barra com 3 bolinhas).", texto_embaixo=True)
def janela(c, cena):
    base = c.fundo()
    card = c.cartao(0, c.W * 0.66, c.H * 0.60, borda=2, cor_borda="#3a404a", janela=cena.get("titulo_janela", ""))
    base = c.colocar(base, card, c.W / 2, c.H * 0.46, atraso=0.05, entrada="baixo")
    return _legenda_inferior(c, base, cena, atraso=0.5)


@modelo("placa", "MOLDURA", "Placa", (0, 0), 3.5, "Frase curta em placa sólida na cor de destaque.")
def placa(c, cena):
    base = c.fundo()
    w, h = c.W * 0.72, c.H * 0.34
    bloco = c.sombra(c.bloco(w, h, c.cor))
    base = c.colocar(base, bloco, c.W / 2, c.H / 2, atraso=0.05, entrada="baixo")
    return c.texto(base, cena.get("texto", "FRASE DE IMPACTO"), "(w-text_w)/2", "(h-text_h)/2", tam=84, cor="black",
                   atraso=0.35, largura=w * 0.9, sombra=False)


# ---------------------------------------------------------------- FRENTE & FUNDO / FOCO
@modelo("frente_fundo", "FRENTEFUNDO", "Frente & Fundo", (1, 1), 4.0, "A própria mídia desfocada no fundo e nítida na frente.", texto_embaixo=True)
def frente_fundo(c, cena):
    base = c.fundo_midia(0)
    card = c.cartao(0, c.W * 0.58, c.H * 0.58, borda=6, movimento=None)
    base = c.colocar(base, card, c.W / 2, c.H * 0.46, atraso=0.05)
    return _legenda_inferior(c, base, cena, atraso=0.5)


@modelo("foco", "FOCO", "Vidro e Texto", (1, 1), 4.5, "Fundo desfocado com caixa de vidro e texto grande.")
def foco(c, cena):
    base = c.fundo_midia(0, desfoque=36, escurecer=0.8)
    w, h = c.W * 0.70, c.H * 0.42
    vidro = c.bloco(w, h, "#ffffff", 0.12)
    base = c.colocar(base, vidro, c.W / 2, c.H / 2, atraso=0.05, entrada="nenhuma")
    base = c.texto(base, cena.get("texto", "Texto em destaque"), "(w-text_w)/2", f"h/2-text_h/2-{int(20 * c.u)}",
                   tam=64, atraso=0.3, largura=w * 0.88)
    return c.texto(base, cena.get("subtexto"), "(w-text_w)/2", f"h/2+{int(h * 0.28)}", tam=30, negrito=False,
                   cor="white@0.85", atraso=0.6, largura=w * 0.88)


# ---------------------------------------------------------------- PAINEL / RETRATO / PERFIL
def _painel(c, cena, lado):
    base = c.fundo()
    v = _vertical(c)
    w, h = (c.W * 0.80, c.H * 0.42) if v else (c.W * 0.48, c.H * 0.70)
    cx = c.W / 2 if v else (c.W * 0.70 if lado == "direita" else c.W * 0.30)
    cy = c.H * 0.32 if v else c.H / 2
    card = c.cartao(0, w, h, borda=8, rot=1.5 if lado == "direita" else -1.5)
    base = c.colocar(base, card, cx, cy, atraso=0.05, entrada=lado if not v else "baixo")
    tx = c.W * 0.10 if v else (c.W * 0.07 if lado == "direita" else c.W * 0.56)
    ty = c.H * 0.62 if v else c.H * 0.36
    larg = c.W * 0.80 if v else c.W * 0.37
    base = c.etiqueta(base, cena.get("etiqueta", "contexto"), int(tx), int(ty - 70 * c.u), atraso=0.3)
    base = c.texto(base, cena.get("texto", "Título do painel"), int(tx), int(ty), tam=58, atraso=0.4, largura=larg)
    return c.texto(base, cena.get("subtexto"), int(tx), int(ty + 190 * c.u), tam=30, negrito=False, cor="white@0.8",
                   atraso=0.6, largura=larg)


@modelo("painel_direita", "PAINEL", "Painel Direita", (1, 1), 5.0, "Mídia à direita, título e texto à esquerda.")
def painel_direita(c, cena):
    return _painel(c, cena, "direita")


@modelo("painel_esquerda", "PAINEL", "Painel Esquerda", (1, 1), 5.0, "Mídia à esquerda, título e texto à direita.")
def painel_esquerda(c, cena):
    return _painel(c, cena, "esquerda")


@modelo("retrato", "RETRATO", "Retrato", (1, 1), 4.5, "Foto vertical inclinada ao lado de um texto (ideal para pessoas).")
def retrato(c, cena):
    base = c.fundo()
    v = _vertical(c)
    w, h = (c.W * 0.62, c.H * 0.46) if v else (c.W * 0.28, c.H * 0.66)
    cx, cy = (c.W / 2, c.H * 0.34) if v else (c.W * 0.30, c.H / 2)
    card = c.cartao(0, w, h, borda=12, rot=-3)
    base = c.colocar(base, card, cx, cy, atraso=0.05, entrada="baixo")
    tx, ty, larg = (c.W * 0.1, c.H * 0.64, c.W * 0.8) if v else (c.W * 0.50, c.H * 0.38, c.W * 0.42)
    base = c.texto(base, cena.get("texto", "Nome da pessoa"), int(tx), int(ty), tam=64, atraso=0.35, largura=larg)
    return c.texto(base, cena.get("subtexto"), int(tx), int(ty + 170 * c.u), tam=32, negrito=False, cor="white@0.8",
                   atraso=0.55, largura=larg)


@modelo("perfil", "PERFIL", "Perfil com Texto", (1, 1), 4.5, "Foto em círculo com anel colorido, nome e descrição.")
def perfil(c, cena):
    base = c.fundo()
    d = c.H * 0.40 if not _vertical(c) else c.W * 0.60
    circ = c.circulo_midia(0, d)
    base = c.colocar(base, circ, c.W / 2, c.H * 0.40, atraso=0.05, entrada="nenhuma", dur_entrada=0.4)
    base = c.texto(base, cena.get("texto", "Nome"), "(w-text_w)/2", f"h*0.40+{int(d / 2 + 50 * c.u)}", tam=60,
                   atraso=0.35, largura=c.W * 0.8)
    return c.texto(base, cena.get("subtexto"), "(w-text_w)/2", f"h*0.40+{int(d / 2 + 140 * c.u)}", tam=30,
                   negrito=False, cor="white@0.8", atraso=0.55, largura=c.W * 0.8)


@modelo("nome", "ED_PESSOA", "Nome (lower third)", (1, 1), 4.0, "Mídia em tela cheia com tarja de nome no canto inferior.", texto_embaixo=True)
def nome(c, cena):
    lab = c.midia(0, c.W, c.H, movimento=c.movimento)
    base = c.rotulo()
    c.add(f"{lab}format=yuv420p{base}")
    x, y = int(c.W * 0.06), int(c.H * 0.74)
    barra = c.bloco(10 * c.u, 120 * c.u, c.cor)
    base = c.colocar(base, barra, x, y + 60 * c.u, atraso=0.2, entrada="esquerda", dur_entrada=0.4)
    base = c.texto(base, cena.get("texto", "Nome Sobrenome"), x + int(30 * c.u), y, tam=54, caixa="#000000@0.55",
                   atraso=0.35, borda_caixa=14)
    return c.texto(base, cena.get("subtexto"), x + int(30 * c.u), y + int(86 * c.u), tam=30, negrito=False,
                   caixa="#000000@0.55", atraso=0.5, borda_caixa=10)


# ---------------------------------------------------------------- DOSSIÊ / VERSUS / EDITORIAL
@modelo("dossie", "DOSSIE", "Dossiê Duplo", (2, 2), 5.0, "Duas fotos inclinadas e sobrepostas, como fichas de um dossiê.")
def dossie(c, cena):
    base = c.fundo()
    v = _vertical(c)
    w, h = (c.W * 0.72, c.H * 0.30) if v else (c.W * 0.40, c.H * 0.50)
    pos = [(c.W * 0.45, c.H * 0.34), (c.W * 0.55, c.H * 0.62)] if v else [(c.W * 0.37, c.H * 0.52), (c.W * 0.63, c.H * 0.46)]
    rots = (-5, 4)
    for i in range(2):
        card = c.cartao(i, w, h, borda=12, rot=rots[i])
        base = c.colocar(base, card, *pos[i], atraso=0.1 + 0.4 * i, entrada="baixo")
    base = c.etiqueta(base, cena.get("etiqueta", "dossiê"), int(c.W * 0.06), int(c.H * 0.07), atraso=0.2)
    return c.texto(base, cena.get("texto"), int(c.W * 0.06), int(c.H * 0.07 + 60 * c.u), tam=44, atraso=0.3,
                   largura=c.W * 0.5)


def _dois_lados(c, cena, rotulos_padrao, versus=False, cores_tag=None):
    base = c.fundo()
    v = _vertical(c)
    w, h = (c.W * 0.78, c.H * 0.34) if v else (c.W * 0.40, c.H * 0.56)
    centros = _distribuir(c, 2, 0.84)
    entradas = ("cima", "baixo") if v else ("esquerda", "direita")
    for i in range(2):
        card = c.cartao(i, w, h, borda=8)
        cx, cy = (c.W / 2, centros[i]) if v else (centros[i], c.H * 0.48)
        base = c.colocar(base, card, cx, cy, atraso=0.05 + 0.25 * i, entrada=entradas[i])
        tag = _rotulo(cena, i, rotulos_padrao[i])
        if tag:
            tx = int(cx - w / 2) if not v else int(c.W * 0.11)
            ty = int(cy - h / 2 - 60 * c.u) if not v else int(cy - h / 2 + 20 * c.u)
            fundo = (cores_tag or [None, None])[i]
            base = c.etiqueta(base, tag, tx, ty, atraso=0.5 + 0.2 * i, fundo=fundo,
                              cor="white" if fundo else "black")
    if versus:
        d = 150 * c.u
        circ = c.sombra(c.circulo(d, c.cor))
        base = c.colocar(base, circ, c.W / 2, c.H * 0.48 if not v else c.H / 2, atraso=0.6, entrada="nenhuma")
        y = "h*0.48-text_h/2" if not v else "h/2-text_h/2"
        base = c.texto(base, "VS", "(w-text_w)/2", y, tam=64, cor="black", atraso=0.7, sombra=False)
    if cena.get("texto") and not v:
        base = c.texto(base, cena["texto"], "(w-text_w)/2", f"h-{int(130 * c.u)}", tam=44, atraso=0.8, largura=c.W * 0.8)
    return base


@modelo("confronto", "VERSUS", "Confronto", (2, 2), 5.0, "Duas mídias lado a lado com selo VS no meio.", texto_embaixo=True)
def confronto(c, cena):
    return _dois_lados(c, cena, ("", ""), versus=True)


@modelo("antes_depois", "DOSSIE", "Antes & Depois", (2, 2), 5.0, "Comparação com selos ANTES / DEPOIS.", texto_embaixo=True)
def antes_depois(c, cena):
    return _dois_lados(c, cena, ("antes", "depois"), cores_tag=["#b3261e", "#1f7a4d"])


@modelo("lado_a_lado", "EDITORIAL", "Lado a Lado", (2, 2), 5.0, "Duas mídias lado a lado, com rótulos opcionais.", texto_embaixo=True)
def lado_a_lado(c, cena):
    return _dois_lados(c, cena, ("", ""))


# ---------------------------------------------------------------- EVIDÊNCIAS / PILHA / GRADE / LINHA DO TEMPO
@modelo("evidencias", "EVIDENCIAS", "Três Evidências", (3, 3), 5.5, "Três fotos em fila, entrando uma por vez, numeradas.")
def evidencias(c, cena):
    base = c.fundo()
    v = _vertical(c)
    w, h = (c.W * 0.70, c.H * 0.22) if v else (c.W * 0.27, c.H * 0.42)
    centros = [c.H * (0.30 + 0.23 * k) for k in range(3)] if v else _distribuir(c, 3, 0.88)
    rots = (-3, 2, -2)
    for i in range(3):
        card = c.cartao(i, w, h, borda=10, rot=rots[i])
        cx, cy = (c.W / 2, centros[i]) if v else (centros[i], c.H * 0.50)
        a = 0.1 + 0.45 * i
        base = c.colocar(base, card, cx, cy, atraso=a, entrada="baixo")
        tag = _rotulo(cena, i, f"evidência {i + 1}")
        base = c.etiqueta(base, tag, int(cx - w / 2), int(cy + h / 2 + 30 * c.u) if not v else int(cy - h / 2),
                          atraso=a + 0.3, tam=22)
    return c.texto(base, cena.get("texto"), "(w-text_w)/2", int(c.H * 0.10), tam=48, atraso=0.2, largura=c.W * 0.8)


@modelo("pilha", "PILHA", "Pilha", (2, 4), 5.0, "Fotos empilhadas com deslocamento, caindo uma sobre a outra.", texto_embaixo=True)
def pilha(c, cena):
    base = c.fundo()
    n = len(c.midias)
    w, h = c.W * (0.62 if _vertical(c) else 0.46), c.H * (0.36 if _vertical(c) else 0.56)
    desloc = [(-60, -40), (20, 10), (70, 40), (-20, 60)]
    rots = (-6, 3, -2, 5)
    for i in range(n):
        card = c.cartao(i, w, h, borda=12, rot=rots[i])
        dx, dy = desloc[i]
        base = c.colocar(base, card, c.W / 2 + dx * c.u, c.H / 2 + dy * c.u, atraso=0.1 + 0.5 * i, entrada="cima")
    return c.texto(base, cena.get("texto"), "(w-text_w)/2", f"h-{int(120 * c.u)}", tam=44, atraso=0.4 + 0.5 * n,
                   largura=c.W * 0.8)


@modelo("grade", "GRADE", "Mosaico", (2, 4), 5.0, "Grade 2×1, 1+2 ou 2×2 conforme o número de mídias.")
def grade(c, cena):
    base = c.fundo()
    n = len(c.midias)
    W, H, g = c.W, c.H, 24 * c.u
    m = 0.08
    aw, ah = W * (1 - 2 * m), H * (1 - 2 * m)
    if n == 2:
        cel = [(0, 0, 0.5, 1), (0.5, 0, 0.5, 1)] if W >= H else [(0, 0, 1, 0.5), (0, 0.5, 1, 0.5)]
    elif n == 3:
        cel = [(0, 0, 0.6, 1), (0.6, 0, 0.4, 0.5), (0.6, 0.5, 0.4, 0.5)]
    else:
        cel = [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)]
    for i, (x, y, w, h) in enumerate(cel[:n]):
        cw, ch = aw * w - g, ah * h - g
        cx, cy = W * m + aw * (x + w / 2), H * m + ah * (y + h / 2)
        card = c.cartao(i, cw, ch, borda=4, sombra=False)
        base = c.colocar(base, card, cx, cy, atraso=0.08 + 0.18 * i, entrada="baixo", dur_entrada=0.5)
    if cena.get("texto"):
        base = c.etiqueta(base, cena["texto"], int(W * m), int(H * m - 50 * c.u), atraso=0.8)
    return base


@modelo("linha_do_tempo", "ABERTURA", "Linha do Tempo", (2, 5), 6.0, "Mídias sobre uma linha com datas (rotulos) embaixo.")
def linha_do_tempo(c, cena):
    base = c.fundo()
    n = len(c.midias)
    ly = c.H * 0.64
    linha = c.bloco(c.W * 0.86, 6 * c.u, "#ffffff", 0.5)
    base = c.colocar(base, linha, c.W / 2, ly, atraso=0.0, entrada="esquerda", dur_entrada=0.8)
    centros = _distribuir(c, n, 0.86) if not _vertical(c) else [c.W * (0.07 + 0.86 * (k + 0.5) / n) for k in range(n)]
    w = min(c.W * 0.80 / n, c.W * 0.22)
    h = w * 0.72
    for i in range(n):
        cx = centros[i]
        a = 0.3 + 0.4 * i
        card = c.cartao(i, w, h, borda=8, rot=(-2, 2)[i % 2])
        base = c.colocar(base, card, cx, ly - h / 2 - 50 * c.u, atraso=a, entrada="baixo")
        ponto = c.circulo(26 * c.u, c.cor)
        base = c.colocar(base, ponto, cx, ly, atraso=a, entrada="nenhuma", dur_entrada=0.2)
        data = _rotulo(cena, i, "")
        if data:
            base = c.texto(base, data, f"{int(cx)}-text_w/2", int(ly + 40 * c.u), tam=34, atraso=a + 0.2, cor=c.cor)
    return c.texto(base, cena.get("texto"), "(w-text_w)/2", int(c.H * 0.08), tam=50, atraso=0.1, largura=c.W * 0.85)


# ---------------------------------------------------------------- CITAÇÃO
@modelo("citacao", "ED_QUOTE", "Citação", (0, 1), 5.0, "Citação grande com aspas e autor; mídia opcional ao fundo.")
def citacao(c, cena):
    base = c.fundo_midia(0, escurecer=0.9) if c.midias else c.fundo()
    larg = c.W * 0.74
    base = c.texto(base, "“", f"{int(c.W * 0.11)}", f"{int(c.H * 0.16)}", tam=220, cor=c.cor, atraso=0.05, sombra=False)
    base = c.texto(base, cena.get("texto", "Citação"), "(w-text_w)/2", "(h-text_h)/2", tam=58, atraso=0.25,
                   largura=larg)
    return c.texto(base, ("— " + cena["subtexto"]) if cena.get("subtexto") else None, f"w-text_w-{int(c.W * 0.13)}",
                   f"h*0.76", tam=32, negrito=False, cor=c.cor, atraso=0.7)
