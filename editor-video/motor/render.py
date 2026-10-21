"""Renderização: cada cena vira um MP4 intermediário; depois tudo é unido com transições."""
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor

from .cena import Cena
from .modelos import MODELOS
from .util import (FORMATOS, ErroEditor, achar_fonte, args_grafo, assinatura_arquivo, cor_ff, duracao, hash_dados,
                   par, rodar, tem_audio, tipo_midia)

# nome amigável -> (tipo do xfade, duração padrão, toca whoosh?)
TRANSICOES = {
    "corte": ("fade", 0.04, False),
    "fade": ("fade", 0.5, False),
    "preto": ("fadeblack", 0.6, False),
    "flash": ("fadewhite", 0.35, False),
    "shutter": ("hlslice", 0.6, True),
    "persiana": ("vuslice", 0.6, True),
    "whoosh": ("slideleft", 0.45, True),
    "empurrar": ("smoothleft", 0.5, True),
    "zoom": ("zoomin", 0.5, True),
    "desfoque": ("hblur", 0.5, False),
    "cortina": ("horzopen", 0.5, False),
    "circulo": ("circleopen", 0.6, False),
    "vento": ("hlwind", 0.6, True),
    "pixel": ("pixelize", 0.5, False),
}

FILTROS = {
    "cinema": "eq=contrast=1.08:saturation=1.12,colorbalance=rs=-0.04:bs=0.08:rh=0.06:bh=-0.06,vignette=PI/4",
    "pb": "hue=s=0,eq=contrast=1.18:brightness=-0.02",
    "arquivo": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,noise=alls=14:allf=t,vignette=PI/4",
    "granulado": "noise=alls=10:allf=t+u",
    "frio": "colorbalance=rs=-0.05:bs=0.1:bm=0.05,eq=saturation=0.9",
    "quente": "colorbalance=rs=0.08:rm=0.05:bs=-0.06,eq=saturation=1.1",
}

POSICOES_MARCA = {
    "sup-dir": ("W-w-{m}", "{m}"), "sup-esq": ("{m}", "{m}"),
    "inf-dir": ("W-w-{m}", "H-h-{m}"), "inf-esq": ("{m}", "H-h-{m}"),
}


def _versao_motor():
    """Hash do código do motor: mudar um modelo invalida o cache das cenas."""
    pasta = os.path.dirname(os.path.abspath(__file__))
    partes = []
    for nome in sorted(os.listdir(pasta)):
        if nome.endswith(".py"):
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                partes.append(f.read())
    return hash_dados(partes)


class Projeto:
    def __init__(self, dados, base_dir, preview=False):
        self.d = dados
        self.base_dir = base_dir
        fmt = dados.get("formato", "16:9")
        if fmt not in FORMATOS:
            raise ErroEditor(f"formato inválido: {fmt} (use {', '.join(FORMATOS)})")
        self.W, self.H = FORMATOS[fmt]
        if preview:
            self.W, self.H = par(self.W / 2), par(self.H / 2)
        self.fps = int(dados.get("fps", 30))
        self.preview = preview
        self.cor = dados.get("cor", "#E2A900")
        self.fundo = dados.get("fundo", "#0d0f14")
        self.fonte_bold = self.caminho(dados["fonte"]) if dados.get("fonte") else achar_fonte("bold")
        self.fonte_regular = self.caminho(dados["fonte_regular"]) if dados.get("fonte_regular") else achar_fonte("regular")
        self.cenas = dados.get("cenas", [])
        if not self.cenas:
            raise ErroEditor("O projeto não tem cenas.")

    def caminho(self, p):
        if not p or p.startswith("cor:") or os.path.isabs(p):
            return p
        return os.path.normpath(os.path.join(self.base_dir, p))

    # ------------------------------------------------------------------ duração "Auto"
    def transicao_de(self, i):
        """Transição que sai da cena i para a i+1."""
        if i >= len(self.cenas) - 1:
            return None
        nome = self.cenas[i].get("transicao", self.d.get("transicao_padrao", "corte"))
        if nome not in TRANSICOES:
            raise ErroEditor(f"Cena {i + 1}: transição desconhecida '{nome}'. Opções: {', '.join(TRANSICOES)}")
        tipo, td, whoosh = TRANSICOES[nome]
        return tipo, float(self.cenas[i].get("duracao_transicao", td)), whoosh

    def duracao_cena(self, i):
        cena = self.cenas[i]
        d = cena.get("duracao", "auto")
        t = self.transicao_de(i)
        td = t[1] if t else 0
        if d != "auto":
            return float(d)
        if cena.get("narracao"):
            return round(duracao(self.caminho(cena["narracao"])) + 0.35 + td, 3)
        if cena.get("avatar"):
            return round(duracao(self.caminho(cena["avatar"])) + td, 3)
        videos = [self.caminho(m) for m in cena.get("midias", []) if tipo_midia(m) == "video"]
        if videos:
            return round(min(max(duracao(v) for v in videos), 12.0) + td, 3)
        return MODELOS[cena["modelo"]].dur_padrao + td

    # ------------------------------------------------------------------ uma cena
    def render_cena(self, i, dur, saida, whoosh_inicio):
        cena = self.cenas[i]
        chave = cena.get("modelo", "tela_cheia")
        if chave not in MODELOS:
            raise ErroEditor(f"Cena {i + 1}: modelo desconhecido '{chave}'. Rode 'fabrica.py modelos'.")
        m = MODELOS[chave]
        midias = [self.caminho(x) for x in cena.get("midias", [])]
        lo, hi = m.slots
        if not lo <= len(midias) <= hi:
            raise ErroEditor(f"Cena {i + 1} ({chave}): precisa de {lo}–{hi} mídias, recebeu {len(midias)}.")
        for x in midias:
            if not x.startswith("cor:") and not os.path.exists(x):
                raise ErroEditor(f"Cena {i + 1}: arquivo não encontrado: {x}")

        tmp = tempfile.mkdtemp(prefix="fabrica_")
        try:
            c = Cena(self.W, self.H, self.fps, dur, self.fonte_bold, self.fonte_regular,
                     cena.get("cor", self.cor), self.fundo, tmp, midias, movimento=cena.get("movimento"))
            v = m.montar(c, cena)
            v = self._eixos_visuais(c, v, cena, dur)
            vout = c.rotulo()
            c.add(f"{v}format=yuv420p{vout}")
            aout = self._audio(c, cena, dur, whoosh_inicio)
            args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
            for e in c.entradas:
                args += e
            args += args_grafo(c.grafo(), tmp) + ["-map", vout, "-map", aout, "-t", f"{dur:.3f}", "-r", str(self.fps),
                     "-c:v", "libx264", "-preset", "ultrafast" if self.preview else "veryfast",
                     "-crf", "26" if self.preview else "18", "-pix_fmt", "yuv420p",
                     "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", saida]
            if os.environ.get("FABRICA_DEBUG"):
                with open(saida + ".filtro.txt", "w", encoding="utf-8") as f:
                    f.write(c.grafo())
            rodar(args, f"na cena {i + 1} ({chave})")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _eixos_visuais(self, c, v, cena, dur):
        # Destaque: palavra/frase grande que "estoura" no meio da cena
        if cena.get("destaque"):
            a = cena.get("destaque_em", round(dur * 0.35, 2))
            v = c.texto(v, str(cena["destaque"]).upper(), "(w-text_w)/2", "(h-text_h)/2", tam=110, cor="black",
                        caixa=c.cor, atraso=a, ate=a + 1.8, borda_caixa=28, largura=c.W * 0.8)
        # Avatar (ex.: vídeo do DreamFace) em círculo no canto
        if cena.get("avatar"):
            d = par(c.H * 0.30 if c.W >= c.H else c.W * 0.42)
            idx = c.nova_entrada(self.caminho(cena["avatar"]), loop=False)
            lab, circ = c.rotulo(), c.rotulo()
            r = d / 2
            c.add(f"[{idx}:v]fps={c.fps},scale={d}:{d}:force_original_aspect_ratio=increase,crop={d}:{d},format=rgba,"
                  f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-{r},Y-{r}),{r - 1}),255,0)'{lab}")
            anel = c.circulo(d + 12 * c.u, c.cor)
            c.add(f"{anel}{lab}overlay={int(6 * c.u)}:{int(6 * c.u)}:format=auto,format=rgba{circ}")
            v = c.colocar(v, circ, c.W - d / 2 - 50 * c.u, c.H - d / 2 - 60 * c.u, atraso=0.1, entrada="direita",
                          dur_entrada=0.5)
        # Legenda automática a partir do texto da narração
        leg = cena.get("legenda")
        if leg and leg.get("texto"):
            v = self._legenda(c, v, leg, cena, dur)
        # Filtro de cor
        if cena.get("filtro"):
            if cena["filtro"] not in FILTROS:
                raise ErroEditor(f"filtro desconhecido '{cena['filtro']}'. Opções: {', '.join(FILTROS)}")
            o = c.rotulo()
            c.add(f"{v}format=yuv420p,{FILTROS[cena['filtro']]}{o}")
            v = o
        # Marca d'água
        marca = self.d.get("marca")
        if marca and marca.get("logo") and cena.get("marca", True):
            idx = c.nova_entrada(self.caminho(marca["logo"]))
            h = par(c.H * marca.get("altura", 0.07))
            mg = int(c.H * 0.04)
            px, py = (e.format(m=mg) for e in POSICOES_MARCA.get(marca.get("posicao", "sup-dir"), POSICOES_MARCA["sup-dir"]))
            lg, o = c.rotulo(), c.rotulo()
            c.add(f"[{idx}:v]scale=-2:{h},format=rgba,colorchannelmixer=aa={marca.get('opacidade', 0.8)}{lg}")
            c.add(f"{v}{lg}overlay={px}:{py}{o}")
            v = o
        return v

    def _legenda(self, c, v, leg, cena, dur):
        palavras = str(leg["texto"]).split()
        por_bloco = int(leg.get("palavras", 7))
        blocos = [" ".join(palavras[k:k + por_bloco]) for k in range(0, len(palavras), por_bloco)]
        fala = duracao(self.caminho(cena["narracao"])) if cena.get("narracao") else dur
        fatia = fala / max(1, len(blocos))
        estilo = leg.get("estilo", "rodape")
        modelo = MODELOS[cena.get("modelo", "tela_cheia")]
        margem = 300 if (modelo.texto_embaixo and cena.get("texto")) else 70
        for k, b in enumerate(blocos):
            ini, fim = k * fatia + 0.05, (k + 1) * fatia
            if estilo == "destaque":
                v = c.texto(v, b.upper(), "(w-text_w)/2", "h*0.72", tam=58, cor="black", caixa=c.cor, atraso=ini,
                            ate=fim, largura=c.W * 0.8, borda_caixa=16)
            else:
                v = c.texto(v, b, "(w-text_w)/2", f"h-text_h-{int(margem * c.u)}", tam=44, caixa="#000000@0.6",
                            atraso=ini, ate=fim, largura=c.W * 0.8, borda_caixa=14)
        return v

    def _audio(self, c, cena, dur, whoosh):
        partes = []
        if cena.get("narracao"):
            idx = len(c.entradas)
            c.entradas.append(["-i", self.caminho(cena["narracao"])])
            partes.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{dur:.3f}")
        elif cena.get("avatar") and tem_audio(self.caminho(cena["avatar"])):
            # o avatar foi adicionado como entrada em _eixos_visuais; reaproveita o áudio dele
            idx = next(k for k, e in enumerate(c.entradas) if e and e[-1] == self.caminho(cena["avatar"]))
            partes.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{dur:.3f}")
        else:
            partes.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{dur:.3f}")
        if whoosh or cena.get("sfx") == "whoosh":
            partes.append("anoisesrc=d=0.7:c=pink:r=48000:a=0.5,bandpass=f=1400:width_type=h:w=2200,"
                          "afade=t=in:d=0.28,afade=t=out:st=0.28:d=0.42,volume=0.55,"
                          f"aformat=sample_rates=48000:channel_layouts=stereo,apad,atrim=0:{dur:.3f}")
        rot = []
        for p in partes:
            r = c.rotulo("a")
            c.add(f"{p}{r}")
            rot.append(r)
        out = c.rotulo("a")
        if len(rot) == 1:
            c.add(f"{rot[0]}anull{out}")
        else:
            c.add(f"{''.join(rot)}amix=inputs={len(rot)}:normalize=0:duration=first{out}")
        return out

    # ------------------------------------------------------------------ projeto inteiro
    def render(self, saida, so=None, paralelo=None, cache_dir=None, log=print):
        cache_dir = cache_dir or os.path.join(self.base_dir, ".render_cache")
        os.makedirs(cache_dir, exist_ok=True)
        indices = list(range(len(self.cenas))) if so is None else [so]
        duracoes = {i: self.duracao_cena(i) for i in range(len(self.cenas))}
        arquivos = {}
        tarefas = []
        for i in indices:
            cena = self.cenas[i]
            whoosh = i > 0 and (self.transicao_de(i - 1) or (None, 0, False))[2]
            arqs = [assinatura_arquivo(self.caminho(x)) for x in
                    cena.get("midias", []) + [cena.get("narracao"), cena.get("avatar"), (self.d.get("marca") or {}).get("logo")]]
            h = hash_dados(cena, arqs, duracoes[i], whoosh, self.W, self.H, self.fps, self.cor, self.fundo,
                           self.d.get("marca"), self.preview, _versao_motor())
            arq = os.path.join(cache_dir, f"cena_{i + 1:03d}_{h}.mp4")
            arquivos[i] = arq
            if os.path.exists(arq):
                log(f"  cena {i + 1:>3} {cena.get('modelo', 'tela_cheia'):<16} {duracoes[i]:5.1f}s  (cache)")
            else:
                tarefas.append((i, arq, whoosh))

        def job(t):
            i, arq, whoosh = t
            self.render_cena(i, duracoes[i], arq + ".tmp.mp4", whoosh)
            os.replace(arq + ".tmp.mp4", arq)
            log(f"  cena {i + 1:>3} {self.cenas[i].get('modelo', 'tela_cheia'):<16} {duracoes[i]:5.1f}s  ok")

        paralelo = paralelo or int(os.environ.get("FABRICA_JOBS", 0)) or max(1, (os.cpu_count() or 2) // 2)
        with ThreadPoolExecutor(paralelo) as ex:
            list(ex.map(job, tarefas))

        if so is not None:
            shutil.copy(arquivos[so], saida)
            return saida
        self._juntar([arquivos[i] for i in indices], [duracoes[i] for i in indices], saida)
        return saida

    def _juntar(self, arquivos, duracoes, saida):
        args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        for a in arquivos:
            args += ["-i", a]
        f = []
        v, a = "[0:v]", "[0:a]"
        atual = duracoes[0]
        for k in range(1, len(arquivos)):
            tipo, td, _ = self.transicao_de(k - 1)
            td = min(td, duracoes[k - 1] / 2, duracoes[k] / 2)
            off = atual - td
            vo, ao = f"[vx{k}]", f"[ax{k}]"
            f.append(f"{v}[{k}:v]xfade=transition={tipo}:duration={td:.3f}:offset={off:.3f}{vo}")
            f.append(f"{a}[{k}:a]acrossfade=d={td:.3f}:c1=tri:c2=tri{ao}")
            v, a = vo, ao
            atual = atual + duracoes[k] - td
        trilha = self.d.get("trilha")
        if trilha and trilha.get("arquivo"):
            idx = len(arquivos)
            args += ["-stream_loop", "-1", "-i", self.caminho(trilha["arquivo"])]
            vol = trilha.get("volume", 0.12)
            f.append(f"[{idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vol},"
                     f"atrim=0:{atual:.3f},afade=t=out:st={max(0, atual - 2):.3f}:d=2[mus]")
            if trilha.get("abaixar_na_fala", True):
                f.append(f"{a}asplit[voz][chave]")
                f.append("[mus][chave]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[musd]")
                f.append("[voz][musd]amix=inputs=2:normalize=0:duration=first[afinal]")
            else:
                f.append(f"{a}[mus]amix=inputs=2:normalize=0:duration=first[afinal]")
            a = "[afinal]"
        tmp = tempfile.mkdtemp(prefix="fabrica_juntar_")
        if f:
            args += args_grafo(";\n".join(f), tmp)
        else:
            v, a = "0:v", "0:a"
        args += ["-map", v, "-map", a, "-c:v", "libx264", "-preset", "ultrafast" if self.preview else "medium",
                 "-crf", "26" if self.preview else "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", saida]
        try:
            rodar(args, "ao juntar as cenas")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
