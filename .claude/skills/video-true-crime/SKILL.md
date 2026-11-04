---
name: video-true-crime
description: Produz um vídeo completo de true crime (caso real brasileiro) para o canal Mapa do Crime — da pesquisa ao MP4 final com narração, legenda, animação 3D (Three.js) e mixagem com voz sempre audível. Use quando pedirem "fazer um vídeo/episódio/short/teaser sobre o caso X", "refazer o piloto", "novo episódio do Mapa do Crime" ou qualquer produção de vídeo do canal.
---

# Vídeo true crime — pipeline completo (Mapa do Crime)

Orquestra as outras skills. Siga as etapas **na ordem**; cada uma tem um portão de qualidade (QA) que precisa passar antes da próxima.

| Etapa | Skill | Entregável | Portão |
|---|---|---|---|
| 1. Pesquisa + roteiro | `roteiro-true-crime` | `scenes.json` + `README.md` do episódio com fontes | Todo fato tem fonte; nada de menor identificado |
| 2. Narração + timeline | `narracao-mixagem` (tts.py) | `build/audio/narracao.wav`, `build/timeline.json` | Duração no alvo (±5%) |
| 3. Cenas 3D | `cena-3d-threejs` | `versao-3d/cena.js` + previews | Folha de QA legível em tamanho de celular |
| 4. Render | `cena-3d-threejs` (render.mjs) | `build/video_mudo.mp4` | Sem erro de página; 30 fps; duração = timeline |
| 5. Trilha + mix | `narracao-mixagem` (trilha.py + mix.py) | `entregas/<episodio>.mp4` | **Voz ≥ 15 LU acima da trilha**; final −14 LUFS, pico ≤ −1 dBTP |
| 6. Entrega | — | MP4 + thumbnail + README atualizado | Commit/push + arquivos enviados ao usuário |

## Estrutura de pastas do episódio

```
canal-mapa-do-crime/
├── package.json                # three (npm install uma vez)
└── <episodio>/                 # ex.: piloto-01-banco-central
    ├── README.md               # roteiro + fatos + fontes
    ├── scenes.json             # narração por cena (ids estáveis)
    ├── build/                  # gerado (gitignored): audio/, timeline.json, previews
    ├── versao-3d/
    │   ├── index.html          # importmap three/engine + <script type=module src=cena.js>
    │   ├── cena.js             # mundo 3D + câmera + overlay por cena
    │   └── eventos.json        # efeitos sonoros sincronizados às cenas
    └── entregas/               # MP4 final, thumbnail
```

## Comandos (a partir da pasta do episódio)

Variáveis de apoio:

```bash
S=/home/user/clleytonalencar/.claude/skills
```

1. Narração e timeline:

```bash
python3 $S/narracao-mixagem/scripts/tts.py --scenes scenes.json --out-dir build --rate +15%
```

2. Previews (PNG em `versao-3d/build/preview/`):

```bash
node $S/cena-3d-threejs/scripts/render.mjs --page versao-3d/index.html --timeline build/timeline.json --preview 3 12 25 40
```

3. Render completo (~1 s por quadro com WebGL por software; 60 s de vídeo ≈ 30 min). Rode em segundo plano:

```bash
node $S/cena-3d-threejs/scripts/render.mjs --page versao-3d/index.html --timeline build/timeline.json --video versao-3d/build/video_mudo.mp4
```

4. Trilha e efeitos em faixas separadas:

```bash
python3 $S/narracao-mixagem/scripts/trilha.py --timeline build/timeline.json --eventos versao-3d/eventos.json --out-dir versao-3d/build
```

5. Mixagem com relatório (falha se a voz ficar baixa):

```bash
python3 $S/narracao-mixagem/scripts/mix.py --voz build/audio/narracao.wav --trilha versao-3d/build/trilha.wav --sfx versao-3d/build/sfx.wav --video versao-3d/build/video_mudo.mp4 --out entregas/<episodio>.mp4
```

6. QA visual em tamanho de celular:

```bash
python3 $S/cena-3d-threejs/scripts/qa_quadros.py entregas/<episodio>.mp4
```

## Regras que valem para todo vídeo

- **Ouça e veja antes de entregar.** Abra a folha de QA (`*_qa.jpg`) com a ferramenta de leitura de imagem e confira cada quadro. Leia o relatório `*_mix.json`.
- **A voz manda.** Narração em −16 LUFS, trilha pelo menos 15 LU abaixo dela. Efeitos com pico em −12 dBFS. Nunca entregue com o `mix.py` reprovado.
- **Legível no celular.** Legenda ≥ 60 px (em 1080p), etiquetas ≥ 34 px, no máximo 2 etiquetas ao mesmo tempo, uma ideia por tela.
- **Fatos:** só o que tem fonte. Quem não foi condenado é "suspeito". Nenhum menor identificado (ECA, art. 143). Personagens 3D são genéricos (sem rosto de pessoa real).
- **Selo fixo** "REPRESENTAÇÃO ILUSTRATIVA · FORA DE ESCALA" e card final com as fontes.
- **Entrega:** commit na branch de trabalho e push. Envie o MP4 ao usuário (SendUserFile) com um resumo do relatório de mix e do QA.

## Ao trocar de visual (motion graphics, pixel, 3D)

O pipeline é o mesmo: só muda o `cena.js` (ou o `index.html` do estilo). `scenes.json`, `timeline.json`, `narracao.wav`, `mix.py` e o QA são reaproveitados. Assim dá para comparar versões com a mesma narração.
