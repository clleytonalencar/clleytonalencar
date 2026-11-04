# Piloto 01 — O Furto do Banco Central (60 s)

Teaser de ~61 s em 1920×1080 / 30 fps, feito 100% em motion graphics 2D.

- **Vídeo final:** `entregas/piloto-01-banco-central.mp4`
- **Thumbnail:** `entregas/thumbnail.jpg` (1280×720)
- **Avatar do canal:** `entregas/avatar.png`

**Versão 3D (padrão do canal):** `entregas/piloto-01-3d.mp4` + `entregas/thumbnail-3d.jpg`. Código em `versao-3d/` (`cena.js` + `eventos.json`), usando as skills `cena-3d-threejs` e `narracao-mixagem`.

Todas as versões foram remixadas com a mixagem nova: voz em −16 LUFS e ≥ 15 LU acima da trilha. O relatório de cada uma fica em `entregas/*_mix.json`.

**Versão jogo 2D (pixel art, mesma narração):** `entregas/piloto-01-pixel.mp4` + `entregas/thumbnail-pixel.jpg`. Veja o conceito em `../ANGULO-JOGO-2D.md`. Para regerar:

```bash
PAGE=versao-pixel/index.html TAG=px node tools/render.js video 30
```

```bash
python3 tools/audio_pixel.py
```

## Roteiro

| Tempo | Capítulo | Narração | Na tela |
|---|---|---|---|
| 0:00 | 01 · O Alvo | "Cinco de agosto de 2005, nove da noite. Sob o Banco Central de Fortaleza, um grupo está a um metro de concreto de cento e sessenta e quatro milhões de reais." | Data datilografada → mapa colado na caixa-forte, retícula vermelha, contador de R$ subindo |
| 0:10 | 02 · O Terreno | "Visto de cima: o banco. E a cem metros dali, uma casa alugada." | Câmera abre, banco destacado, pino na casa, cota "≈ 100 m" |
| 0:16 | 03 · O Disfarce | "Na fachada, uma loja de grama sintética. Ninguém estranha uma empresa que tira terra todo dia." | Placa "Grama Sintética", sacos de terra saindo para a caminhonete |
| 0:23 | 04 · O Túnel | "Dos fundos, três metros abaixo do chão, nasce um túnel de setenta e cinco metros. Escorado, iluminado, ventilado." | Wipe para o corte lateral, poço de 3 m, túnel avançando com contador em metros, lâmpadas acendendo |
| 0:31 | 05 · O Imprevisto | "Aos sessenta metros, um esgoto que não estava na planta. Eles sobem o túnel e passam por cima, colados no asfalto." | Zoom no cano de esgoto, túnel sobe ~70 cm, carros passando e tela tremendo |
| 0:39 | 06 · A Laje | "No fim, um metro e dez de concreto. Uma serra com disco de diamante abre caminho." | Close na laje hachurada, serra girando com faíscas, flash quando rompe |
| 0:45 | 07 · O Cofre | "Em oito horas, eles puxam três toneladas e meia de notas de cinquenta. Usadas, sem sequência: impossíveis de rastrear." | Planta do cofre: notas novas intocadas, notas usadas indo para o buraco; relógio 22:00→06:00, contadores de R$ e toneladas |
| 0:53 | 08 · A Fuga | "O banco só percebe na segunda-feira. Mas tirar o dinheiro foi a parte fácil. Isto é o Mapa do Crime." | Rota do túnel no mapa, pontos se espalhando pela cidade, card final da marca |

## Fatos usados e fontes

Todos conferidos no especial **"Os Toupeiras: a história do furto ao Banco Central"** (Estadão, 2015), que se baseia em investigação da PF e em processos da Justiça Federal do Ceará:

- Casa alugada na Rua 25 de Março, a ~100 m do banco (esquina da Av. Dom Manuel com a R. Heráclito Graça), com empresa de fachada de grama sintética registrada em nome falso.
- Túnel de **75,4 m**, começando numa edícula nos fundos, a ~3 m de profundidade, com ~900 tábuas de escoramento, iluminação e ventiladores. Escavação começou entre maio e junho de 2005 e levou menos de três meses.
- Rede de esgoto fora da planta a ~60 m do início do túnel, que obrigou a subir a base em ~70 cm e passar mais perto do asfalto da avenida.
- Laje de concreto de **1,10 m**, cortada com serra circular de disco diamantado.
- Entrada no cofre por volta das 21h de sexta, **5/8/2005**. Retirada das notas das 22h às 6h de 6/8.
- **R$ 164,7 milhões** em notas usadas de R$ 50, não seriadas, somando cerca de **3,5 toneladas**.
- O furto só foi descoberto na segunda-feira, 8/8/2005.

O mapa é **ilustrativo e fora de escala**: posições e formas foram simplificadas e não reproduzem a planta real.

## Como reproduzir / editar

Requisitos: Node com `playwright` (Chromium), Python 3 com `numpy` e `edge-tts`, e `ffmpeg`.

1. Edite o texto em `scenes.json` e gere narração, legendas e timeline:

```bash
python3 tools/tts.py pt-BR-AntonioNeural +18%
```

2. Confira quadros soltos (os PNGs saem em `build/preview/`):

```bash
node tools/render.js preview 5 20 40
```

3. Renderize o vídeo mudo (~2,5 min):

```bash
node tools/render.js video 30
```

4. Gere a trilha e faça a mixagem final (loudness −14 LUFS):

```bash
python3 tools/audio.py --mix
```

5. Thumbnail e avatar:

```bash
node tools/render.js thumb && node tools/render.js avatar
```

Para fazer outro caso, mantenha `tools/` e troque em `index.html` o objeto `WORLD` (geometria), as funções de cena (`sceneMap`, `sceneSection`, `sceneVault`) e o mapa `CHAPTERS`. A identidade visual (paleta `C`, HUD, tags, legendas, wipe) continua igual.

## Próximos passos sugeridos

- Gravar a narração com voz humana ou com uma voz de IA com licença comercial e substituir `build/audio/narracao.wav`.
- Gerar a versão vertical 9:16 para Shorts.
- Expandir para o episódio completo de ~15 min: planejamento em Cumbuco, recrutamento em SP, a fuga e as extorsões, investigação da PF e julgamento.
