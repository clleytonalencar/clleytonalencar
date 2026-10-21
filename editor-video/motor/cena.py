"""Construtor de gráfico de filtros (filter_complex) para uma cena.

Os modelos usam esta classe como "caneta": pedem cartões de mídia, textos,
etiquetas e formas, e posicionam tudo com animação de entrada.
"""
import math
import os

from .util import cor_ff, par, quebrar, tipo_midia

# Movimentos de câmera (Ken Burns). F = total de quadros da cena.
MOVIMENTOS = {
    "zoom_in": ("1+0.12*on/{F}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "zoom_out": ("1.12-0.12*on/{F}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan_esquerda": ("1.12", "(iw-iw/zoom)*(1-on/{F})", "ih/2-(ih/zoom/2)"),
    "pan_direita": ("1.12", "(iw-iw/zoom)*on/{F}", "ih/2-(ih/zoom/2)"),
    "pan_cima": ("1.12", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*(1-on/{F})"),
}

# deslocamento inicial (fração de W/H) de cada tipo de entrada
ENTRADAS = {
    "baixo": (0, 0.45), "cima": (0, -0.45), "esquerda": (-0.6, 0), "direita": (0.6, 0), "nenhuma": (0, 0),
}


class Cena:
    def __init__(self, W, H, fps, dur, fonte_bold, fonte_regular, cor, fundo, tmpdir, midias, movimento=None):
        self.W, self.H, self.fps, self.dur = W, H, fps, dur
        self.u = H / 1080 if W >= H else W / 1080  # unidade relativa
        self.fonte_bold, self.fonte_regular = fonte_bold, fonte_regular
        self.cor = cor
        self.fundo_cor = fundo
        self.tmp = tmpdir
        self.midias = midias
        self.movimento = movimento
        self.filtros = []
        self.entradas = [["-f", "lavfi", "-i", f"color=c={cor_ff(fundo)}:s={W}x{H}:r={fps}:d={dur:.3f}"]]
        self._n = 0
        self._ntxt = 0

    # ---------- infraestrutura ----------
    def rotulo(self, p="v"):
        self._n += 1
        return f"[{p}{self._n}]"

    def add(self, f):
        self.filtros.append(f)

    def nova_entrada(self, caminho, loop=True):
        t = tipo_midia(caminho)
        d = f"{self.dur:.3f}"
        if t == "imagem":
            args = ["-loop", "1", "-framerate", str(self.fps), "-t", d, "-i", caminho]
        elif t == "video":
            args = (["-stream_loop", "-1"] if loop else []) + ["-t", d, "-i", caminho]
        else:  # cor:#RRGGBB  (placeholder, usado no catálogo)
            args = ["-f", "lavfi", "-t", d, "-i", f"color=c={cor_ff(caminho[4:])}:s=1280x720:r={self.fps}"]
        self.entradas.append(args)
        return len(self.entradas) - 1

    def grafo(self):
        return ";\n".join(self.filtros)

    # ---------- fundo ----------
    def fundo(self, grade=True):
        out = self.rotulo()
        g = par(80 * self.u)
        cadeia = f"drawgrid=w={g}:h={g}:t=1:c=white@0.035," if grade else ""
        self.add(f"[0:v]{cadeia}vignette=PI/5,format=yuv420p{out}")
        return out

    def fundo_midia(self, i, desfoque=28, escurecer=0.55):
        """Fundo feito da própria mídia, desfocado e escurecido (frente & fundo)."""
        m = self.midia(i, self.W, self.H, movimento=self.movimento)
        out = self.rotulo()
        self.add(f"{m}boxblur={int(desfoque * self.u)}:2,eq=brightness={-escurecer * 0.4:.2f}:saturation=0.8,format=yuv420p{out}")
        return out

    # ---------- mídia ----------
    def midia(self, i, w, h, movimento=None):
        """Mídia do espaço i, recortada para w×h (rgba), com movimento opcional."""
        w, h = par(w), par(h)
        idx = self.nova_entrada(self.midias[i])
        src = f"[{idx}:v]"
        out = self.rotulo()
        if movimento and movimento in MOVIMENTOS:
            F = max(1, int(self.dur * self.fps))
            z, x, y = (e.format(F=F) for e in MOVIMENTOS[movimento])
            sw, sh = par(w * 1.25), par(h * 1.25)
            self.add(
                f"{src}fps={self.fps},scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},setsar=1,"
                f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={self.fps},format=rgba{out}"
            )
        else:
            self.add(f"{src}fps={self.fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,format=rgba{out}")
        return out

    def cartao(self, i, w, h, borda=10, rot=0.0, sombra=True, cor_borda="white", janela=None, movimento="padrao"):
        """Cartão de mídia com borda, rotação, sombra e (opcional) barra de janela."""
        mov = self.movimento if movimento == "padrao" else movimento
        lab = self.midia(i, w, h, movimento=mov)
        cad = []
        if janela is not None:
            barra = par(46 * self.u)
            r = max(4, int(7 * self.u))
            cad.append(f"pad=iw:ih+{barra}:0:{barra}:color=0x22262d")
            for k, c in enumerate(("0xff5f57", "0xfebc2e", "0x28c840")):
                cad.append(f"drawbox=x={int((20 + k * 26) * self.u)}:y={barra // 2 - r}:w={2 * r}:h={2 * r}:color={c}:t=fill")
            if janela:
                tf = self._arquivo_texto(janela)
                cad.append(
                    f"drawtext=fontfile='{self.fonte_regular}':textfile='{tf}':expansion=none:fontsize={int(20 * self.u)}:"
                    f"fontcolor=white@0.75:x=(w-text_w)/2:y={barra // 2}-text_h/2"
                )
        b = par(borda * self.u)
        if b > 0:
            cad.append(f"pad=iw+{2 * b}:ih+{2 * b}:{b}:{b}:color={cor_ff(cor_borda)}")
        if rot:
            a = math.radians(rot)
            cad.append(f"rotate=a={a:.4f}:c=none:ow='rotw({a:.4f})':oh='roth({a:.4f})'")
        if cad:
            o = self.rotulo()
            self.add(f"{lab}{','.join(cad)},format=rgba{o}")
            lab = o
        if sombra:
            lab = self.sombra(lab)
        return lab

    def sombra(self, lab, margem=40, ox=10, oy=16, opacidade=0.55):
        M = par(margem * self.u)
        ox, oy = int(ox * self.u), int(oy * self.u)
        c1, c2, sh, out = self.rotulo(), self.rotulo(), self.rotulo(), self.rotulo()
        self.add(f"{lab}split{c1}{c2}")
        self.add(
            f"{c2}colorchannelmixer=rr=0:rg=0:rb=0:gr=0:gg=0:gb=0:br=0:bg=0:bb=0:aa={opacidade},"
            f"pad=iw+{2 * M}:ih+{2 * M}:{M}:{M}:color=black@0,boxblur={int(18 * self.u)}:1{sh}"
        )
        self.add(f"{sh}{c1}overlay={M - ox}:{M - oy}:format=auto,format=rgba{out}")
        return out

    def circulo_midia(self, i, d, anel=8, cor_anel=None):
        d = par(d)
        lab = self.midia(i, d, d, movimento=self.movimento)
        out = self.rotulo()
        r = d / 2
        self.add(f"{lab}geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-{r},Y-{r}),{r - 1}),255,0)'{out}")
        if anel:
            a = par(anel * self.u)
            ring = self.circulo(d + 2 * a, cor_anel or self.cor)
            o2 = self.rotulo()
            self.add(f"{ring}{out}overlay={a}:{a}:format=auto,format=rgba{o2}")
            out = o2
        return self.sombra(out)

    # ---------- formas ----------
    def bloco(self, w, h, cor, alpha=1.0):
        out = self.rotulo()
        self.add(f"color=c={cor_ff(cor)}:s={par(w)}x{par(h)}:r={self.fps}:d={self.dur:.3f},format=rgba,"
                 f"colorchannelmixer=aa={alpha}{out}")
        return out

    def circulo(self, d, cor):
        d = par(d)
        r = d / 2
        out = self.rotulo()
        self.add(f"color=c={cor_ff(cor)}:s={d}x{d}:r={self.fps}:d={self.dur:.3f},format=rgba,"
                 f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-{r},Y-{r}),{r - 1}),255,0)'{out}")
        return out

    # ---------- composição ----------
    def colocar(self, base, camada, cx, cy, atraso=0.0, entrada="baixo", dur_entrada=0.6):
        """Sobrepõe a camada centralizada em (cx, cy) com entrada animada (ease-out cúbico) e fade."""
        dx, dy = ENTRADAS.get(entrada, (0, 0.45))
        dx, dy = dx * self.W, dy * self.H
        a, d = atraso, dur_entrada
        E = f"(1-pow(1-clip((t-{a:.3f})/{d:.3f},0,1),3))"
        fd = self.rotulo()
        self.add(f"{camada}fade=t=in:st={a:.3f}:d={min(0.35, d):.3f}:alpha=1{fd}")
        out = self.rotulo()
        self.add(f"{base}{fd}overlay=x='{cx:.1f}-w/2+(1-{E})*{dx:.1f}':y='{cy:.1f}-h/2+(1-{E})*{dy:.1f}':eval=frame{out}")
        return out

    def _arquivo_texto(self, texto):
        self._ntxt += 1
        p = os.path.join(self.tmp, f"txt_{id(self)}_{self._ntxt}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(texto))
        return p

    def texto(self, base, texto, x, y, tam=56, cor="white", negrito=True, caixa=None, atraso=0.0, ate=None,
              largura=None, borda_caixa=18, espaco=0.25, sombra=True):
        """drawtext com fade. x/y aceitam expressões do drawtext (w, h, text_w, text_h)."""
        if not texto:
            return base
        tam = int(tam * self.u)
        if largura:
            texto = quebrar(texto, largura, tam)
        tf = self._arquivo_texto(texto)
        fonte = self.fonte_bold if negrito else self.fonte_regular
        alpha = f"clip((t-{atraso:.3f})/0.3,0,1)"
        if ate is not None:
            alpha = f"min({alpha},clip(({ate:.3f}-t)/0.25,0,1))"
        opts = [
            f"fontfile='{fonte}'", f"textfile='{tf}'", "expansion=none", f"fontsize={tam}",
            f"fontcolor={cor_ff(cor)}", f"x={x}", f"y={y}", f"alpha='{alpha}'", f"line_spacing={int(tam * espaco)}",
        ]
        if caixa:
            opts += ["box=1", f"boxcolor={cor_ff(caixa)}", f"boxborderw={int(borda_caixa * self.u)}"]
        elif sombra:
            opts += ["shadowcolor=black@0.6", f"shadowx={max(1, int(2 * self.u))}", f"shadowy={max(1, int(3 * self.u))}"]
        if ate is not None:
            opts.append(f"enable='between(t,{atraso:.3f},{ate:.3f})'")
        out = self.rotulo()
        self.add(f"{base}drawtext={':'.join(opts)}{out}")
        return out

    def etiqueta(self, base, texto, x, y, tam=26, fundo=None, cor="black", atraso=0.0):
        """Etiqueta em caixa alta com fundo na cor de destaque (estilo 'DOSSIÊ', 'EVIDÊNCIA 1')."""
        return self.texto(base, str(texto).upper(), x, y, tam=tam, cor=cor, caixa=fundo or self.cor,
                          atraso=atraso, borda_caixa=12)
