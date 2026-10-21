"""Modo automático: roteiro (blocos) + predefinição (eixos com %) -> projeto.

Cada eixo funciona como no editor de referência:
  - "pct": quantas cenas recebem o eixo (0–100). Fora disso a cena fica limpa.
  - "modo": "todos" (usa todos os itens do catálogo) ou "escolher" (usa só "lista").
"""
import random

from .modelos import MODELOS
from .render import FILTROS, TRANSICOES
from .cena import MOVIMENTOS
from .util import ErroEditor

CATALOGO_EIXO = {
    "transicoes": list(TRANSICOES),
    "movimento": list(MOVIMENTOS),
    "filtros": list(FILTROS),
}


def _itens(eixo, todos):
    if eixo.get("modo", "todos") == "escolher":
        lista = eixo.get("lista") or []
        desconhecidos = [x for x in lista if x not in todos]
        if desconhecidos:
            raise ErroEditor(f"Itens desconhecidos na predefinição: {', '.join(desconhecidos)}")
        return lista
    return [x for x in todos if x not in eixo.get("excluir", [])]


def _sortear_indices(rng, n, pct, elegiveis=None):
    elegiveis = list(range(n)) if elegiveis is None else list(elegiveis)
    k = round(len(elegiveis) * max(0, min(100, pct)) / 100)
    return set(rng.sample(elegiveis, k)) if k else set()


def _escolher_sem_repetir(rng, opcoes, anterior):
    if not opcoes:
        return None
    pool = [o for o in opcoes if o != anterior] or opcoes
    return rng.choice(pool)


def gerar_projeto(roteiro, pre):
    blocos = roteiro.get("blocos") or []
    if not blocos:
        raise ErroEditor("O roteiro não tem blocos.")
    rng = random.Random(pre.get("semente", 7))
    n = len(blocos)
    eixos = pre.get("eixos", {})

    # Templates
    e_tpl = eixos.get("templates", {"pct": 100})
    modelos_ok = _itens(e_tpl, [k for k in MODELOS if k != "tela_cheia"])
    com_template = _sortear_indices(rng, n, e_tpl.get("pct", 100))
    # blocos sem mídia sempre precisam de modelo de texto
    com_template |= {i for i, b in enumerate(blocos) if not b.get("midias")}

    e_tr = eixos.get("transicoes", {})
    transicoes = _itens(e_tr, CATALOGO_EIXO["transicoes"])
    com_trans = _sortear_indices(rng, n - 1, e_tr.get("pct", 0))
    e_mov = eixos.get("movimento", {})
    movimentos = _itens(e_mov, CATALOGO_EIXO["movimento"])
    com_mov = _sortear_indices(rng, n, e_mov.get("pct", 0))
    e_fil = eixos.get("filtros", {})
    filtros = _itens(e_fil, CATALOGO_EIXO["filtros"])
    com_fil = _sortear_indices(rng, n, e_fil.get("pct", 0))
    e_dest = eixos.get("destaques", {})
    com_dest = _sortear_indices(rng, n, e_dest.get("pct", 0), [i for i, b in enumerate(blocos) if b.get("destaque")])
    e_av = eixos.get("avatar", {})
    avatar_padrao = roteiro.get("avatar")
    com_av = _sortear_indices(rng, n, e_av.get("pct", 0),
                              [i for i, b in enumerate(blocos) if b.get("avatar") or avatar_padrao])
    e_leg = eixos.get("legenda", {})

    cenas, anterior_modelo, anterior_tr = [], None, None
    for i, b in enumerate(blocos):
        midias = b.get("midias", [])
        cena = {k: v for k, v in b.items() if k in ("texto", "subtexto", "rotulos", "etiqueta", "narracao", "duracao")}
        cena["midias"] = midias
        if b.get("modelo"):  # o roteiro pode forçar um modelo
            cena["modelo"] = b["modelo"]
        elif i in com_template:
            cabem = [k for k in modelos_ok if MODELOS[k].slots[0] <= len(midias) <= MODELOS[k].slots[1]]
            if not cabem:
                cabem = [k for k in MODELOS if MODELOS[k].slots[0] <= len(midias) <= MODELOS[k].slots[1] and k != "tela_cheia"]
            cena["modelo"] = _escolher_sem_repetir(rng, cabem, anterior_modelo) or "tela_cheia"
        else:
            cena["modelo"] = "tela_cheia"
        if len(midias) > MODELOS[cena["modelo"]].slots[1]:
            cena["midias"] = midias[: MODELOS[cena["modelo"]].slots[1]]
        anterior_modelo = cena["modelo"]

        if i < n - 1:
            if b.get("transicao"):
                cena["transicao"] = b["transicao"]
            elif i in com_trans and transicoes:
                cena["transicao"] = anterior_tr = _escolher_sem_repetir(rng, transicoes, anterior_tr)
            else:
                cena["transicao"] = "corte"
        if b.get("movimento") or (i in com_mov and movimentos):
            cena["movimento"] = b.get("movimento") or rng.choice(movimentos)
        if b.get("filtro") or (i in com_fil and filtros):
            cena["filtro"] = b.get("filtro") or rng.choice(filtros)
        if i in com_dest:
            cena["destaque"] = b["destaque"]
        if i in com_av:
            cena["avatar"] = b.get("avatar") or avatar_padrao
        if e_leg.get("ativo") and b.get("texto_narracao"):
            cena["legenda"] = {"texto": b["texto_narracao"], "estilo": e_leg.get("estilo", "rodape"),
                               "palavras": e_leg.get("palavras", 7)}
        cenas.append(cena)

    proj = {k: v for k, v in pre.items() if k in ("formato", "fps", "cor", "fundo", "fonte", "fonte_regular", "marca", "trilha")}
    for k in ("formato", "trilha", "marca"):
        if roteiro.get(k):
            proj[k] = roteiro[k]
    proj["cenas"] = cenas
    return proj


def resumo(proj):
    linhas = []
    for i, c in enumerate(proj["cenas"]):
        extras = [c.get(k) for k in ("movimento", "filtro") if c.get(k)]
        if c.get("destaque"):
            extras.append("destaque")
        if c.get("avatar"):
            extras.append("avatar")
        if c.get("legenda"):
            extras.append("legenda")
        tr = c.get("transicao", "")
        linhas.append(f"{i + 1:>3}. {c['modelo']:<16} {len(c['midias'])} mídia(s)  → {tr:<9} {' · '.join(extras)}")
    return "\n".join(linhas)
