"""Canais, rotação de predefinições e controle de unicidade entre vídeos.

Um canal é uma pasta com `canal.json`:
  - identidade fixa (formato, fontes, marca, paleta de cores);
  - um conjunto de predefinições que se revezam a cada vídeo;
  - biblioteca de trilhas que também se revezam;
  - regras de unicidade: cada vídeo novo é comparado com os últimos N do canal e,
    se a "assinatura de edição" ficar parecida demais, o sorteio é refeito.

O histórico fica em `historico.jsonl` dentro da pasta do canal.
"""
import copy
import datetime
import glob
import json
import os
import random

from .auto import gerar_projeto
from .util import ErroEditor, hash_dados

EXT_AUDIO = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")


class Canal:
    def __init__(self, pasta):
        self.pasta = os.path.abspath(pasta)
        arq = os.path.join(self.pasta, "canal.json")
        if not os.path.exists(arq):
            raise ErroEditor(f"Não achei {arq}")
        with open(arq, encoding="utf-8") as f:
            self.cfg = json.load(f)
        self.nome = self.cfg.get("nome", os.path.basename(self.pasta))
        self.historico_arq = os.path.join(self.pasta, "historico.jsonl")
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pastas_pre = [self.pasta, os.path.join(raiz, "predefinicoes")]

    # ---------------------------------------------------------------- arquivos
    def _abs(self, p):
        return p if (not p or os.path.isabs(p) or p.startswith("cor:")) else os.path.normpath(os.path.join(self.pasta, p))

    def predefinicoes(self):
        nomes = self.cfg.get("predefinicoes") or []
        if not nomes:
            raise ErroEditor(f"Canal {self.nome}: lista 'predefinicoes' vazia.")
        saida = []
        for n in nomes:
            for base in self.pastas_pre:
                p = os.path.join(base, n)
                if os.path.exists(p):
                    saida.append(p)
                    break
            else:
                raise ErroEditor(f"Canal {self.nome}: predefinição '{n}' não encontrada.")
        return saida

    def trilhas(self):
        itens = []
        for t in self.cfg.get("trilhas", []):
            p = self._abs(t)
            if os.path.isdir(p):
                itens += sorted(x for x in glob.glob(os.path.join(p, "*")) if x.lower().endswith(EXT_AUDIO))
            elif any(ch in p for ch in "*?"):
                itens += sorted(glob.glob(p))
            elif os.path.exists(p):
                itens.append(p)
        return itens

    def historico(self):
        if not os.path.exists(self.historico_arq):
            return []
        with open(self.historico_arq, encoding="utf-8") as f:
            return [json.loads(x) for x in f if x.strip()]

    def registrar(self, registro):
        with open(self.historico_arq, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------- rotação
    @staticmethod
    def _rodizio(opcoes, usados, rng):
        """Sorteia entre as opções que não apareceram nos últimos usos (metade da lista).

        Cada item (predefinição, cor, fundo, trilha) gira de forma independente, então
        as combinações não se repetem em ciclo fixo. `usados` = do mais antigo ao mais recente.
        """
        if not opcoes:
            return None
        bloqueio = len(opcoes) // 2
        recentes = set(usados[-bloqueio:]) if bloqueio else set()
        livres = [o for o in opcoes if o not in recentes] or list(opcoes)
        nunca = [o for o in livres if o not in usados]
        return rng.choice(nunca or livres)

    def planejar(self, roteiro, video_id=None):
        """Escolhe predefinição, trilha, cor e semente; gera o projeto mais 'diferente' possível."""
        hist = self.historico()
        uni = self.cfg.get("unicidade", {})
        janela = int(uni.get("janela", 10))
        limite = float(uni.get("similaridade_max", 0.55))
        tentativas = int(uni.get("tentativas", 40))
        recentes = hist[-janela:]

        vid = video_id or hash_dados(roteiro)
        rng = random.Random(f"{self.nome}|{vid}")
        pres = self.predefinicoes()
        pre_path = self._rodizio(pres, [h.get("predefinicao") for h in hist], rng)
        with open(pre_path, encoding="utf-8") as f:
            pre_base = json.load(f)

        ident = self.cfg.get("identidade", {})
        paleta = ident.get("paleta") or [pre_base.get("cor", "#E2A900")]
        cor = self._rodizio(paleta, [h.get("cor") for h in hist], rng)
        fundos = ident.get("fundos") or [pre_base.get("fundo", "#0d0f14")]
        fundo = self._rodizio(fundos, [h.get("fundo") for h in hist], rng)
        trilhas = self.trilhas()
        trilha = self._rodizio(trilhas, [h.get("trilha") for h in hist], rng)

        variacao = float(pre_base.get("variacao_pct", self.cfg.get("variacao_pct", 10)))

        melhor = None
        for _ in range(tentativas):
            pre = copy.deepcopy(pre_base)
            pre["semente"] = rng.randrange(1, 10**9)
            # pequena oscilação dos % de cada eixo: dois vídeos do mesmo canal nunca têm a mesma dosagem
            for eixo in pre.get("eixos", {}).values():
                if isinstance(eixo, dict) and "pct" in eixo:
                    eixo["pct"] = max(0, min(100, eixo["pct"] + rng.uniform(-variacao, variacao)))
            for k in ("formato", "fps", "fonte", "fonte_regular"):
                if ident.get(k):
                    pre[k] = self._abs(ident[k]) if k.startswith("fonte") else ident[k]
            pre["cor"], pre["fundo"] = cor, fundo
            if ident.get("marca"):
                pre["marca"] = dict(ident["marca"], logo=self._abs(ident["marca"].get("logo")))
            if trilha:
                pre["trilha"] = dict(pre.get("trilha") or {}, **ident.get("trilha", {}), arquivo=trilha)
            proj = gerar_projeto(roteiro, pre)
            ass = assinatura(proj)
            sim = max((similaridade(ass, h["assinatura"]) for h in recentes if h.get("assinatura")), default=0.0)
            if melhor is None or sim < melhor[0]:
                melhor = (sim, proj, pre["semente"], ass)
            if sim <= limite:
                break

        sim, proj, semente, ass = melhor
        registro = {
            "video_id": vid, "data": datetime.datetime.now().isoformat(timespec="seconds"),
            "predefinicao": pre_path, "semente": semente, "cor": cor, "fundo": fundo, "trilha": trilha,
            "similaridade": round(sim, 3), "assinatura": ass,
        }
        return proj, registro, sim <= limite


# -------------------------------------------------------------------- assinatura e similaridade
def assinatura(proj):
    """Resumo da edição de um vídeo: o que o espectador (e um classificador) percebe como 'formato'."""
    cenas = proj["cenas"]
    mods = [c["modelo"] for c in cenas]
    return {
        "modelos": mods,
        "pares": [f"{a}>{b}" for a, b in zip(mods, mods[1:])],
        "transicoes": [c.get("transicao", "corte") for c in cenas[:-1]],
        "movimentos": [c.get("movimento", "-") for c in cenas],
        "filtros": [c.get("filtro", "-") for c in cenas],
        "cor": proj.get("cor"),
        "trilha": (proj.get("trilha") or {}).get("arquivo"),
    }


def _jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _posicional(a, b):
    """Fração de posições iguais (mesmo modelo na mesma ordem)."""
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(1 for x, y in zip(a, b) if x == y) / max(len(a), len(b))


def similaridade(x, y):
    """0 = nada em comum, 1 = edição idêntica."""
    pesos = [
        (0.30, _posicional(x["modelos"], y["modelos"])),
        (0.20, _jaccard(x["pares"], y["pares"])),
        (0.15, _posicional(x["transicoes"], y["transicoes"])),
        (0.10, _posicional(x["movimentos"], y["movimentos"])),
        (0.10, _posicional(x["filtros"], y["filtros"])),
        (0.08, 1.0 if x.get("trilha") and x.get("trilha") == y.get("trilha") else 0.0),
        (0.07, 1.0 if x.get("cor") == y.get("cor") else 0.0),
    ]
    return sum(p * v for p, v in pesos)
