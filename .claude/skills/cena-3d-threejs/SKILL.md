---
name: cena-3d-threejs
description: Cria e renderiza cenas 3D em HTML (Three.js/WebGL) para vídeos explicativos de true crime — maquete da cidade, subsolo em raio-X, bonecos low-poly, câmera de drone, etiquetas e legendas legíveis no celular — e exporta MP4 quadro a quadro (Playwright + ffmpeg). Use para "vídeo 3D", "animação 3D em HTML", "Three.js", "reconstituição 3D", "maquete", "câmera de drone", ou como etapas 3 e 4 da skill video-true-crime.
---

# Cenas 3D em HTML (Three.js) → MP4

## Qual método 3D em HTML usar

| Método | Veredito para este canal |
|---|---|
| **Three.js (WebGL) + overlay 2D em canvas** | ✅ **Padrão.** Maduro, leve, roda no Chromium headless (SwiftShader). Texto/HUD no canvas 2D por cima fica nítido e legível. |
| Babylon.js | Bom, mas mais pesado. Não traz nada que falte no Three para este uso. |
| CSS 3D (`transform: perspective`) | Só serve para cartões e planos. Sem luz, sombra ou volume. |
| Pixel art 2D | Testado no piloto: ficou pequeno e difícil de ler no celular. Descartado como padrão. |
| Blender | Visual superior, mas sai do fluxo HTML/código e o render é bem mais lento. Use para um shot especial, não para o episódio todo. |

## Arquitetura

```
engine/engine.js       ← motor compartilhado (NÃO copie; importe como "engine")
scripts/render.mjs     ← servidor HTTP local + Playwright + ffmpeg (preview / still / vídeo)
scripts/qa_quadros.py  ← folha de quadros em tamanho de celular
<episodio>/versao-3d/index.html  ← importmap { three, engine } + <script type=module src=cena.js>
<episodio>/versao-3d/cena.js     ← mundo + câmera + overlay de cada cena
```

**Princípio:** cada quadro é função pura de `t`. O `render.mjs` chama `window.renderFrame(t)`, que roda `draw(t)` (posiciona câmera e objetos), depois `renderer.render` e por fim `overlay(t)` (HUD, legendas e etiquetas no canvas 2D). Não use `requestAnimationFrame`, `Date.now()` nem `Math.random()`. Para aleatoriedade, use `rng(semente)`.

`index.html` mínimo:

```html
<script type="importmap">{ "imports": { "three": "/three/build/three.module.js", "engine": "/engine/engine.js" } }</script>
<script type="module" src="./cena.js"></script>
```

`cena.js` mínimo:

```js
import { THREE, scene, P, sceneAt, camPath, setCam, v3, hud, caption, tag3D, run } from 'engine';
// ...monta o mundo uma vez (meshes, materiais)...
function draw(t) { const { s } = sceneAt(t); const p = P(s.id, t); /* posiciona tudo */ const c = camPath(KEYS[s.id], p); setCam(c.pos, c.look); }
function overlay(t) { hud(t, { caso: 'CASO 02 · ...', chapters: CH, clock }); caption(t, /\d|palavra/i, 66); }
run(draw, overlay);
```

## API do engine (resumo)

- **Tempo:** `TL` (timeline), `sceneAt(t)` → `{s, i, p, local}`, `P(id, t)` → 0..1, `seg(p,a,b)`, `eio`, `eout`, `lerp`, `lerpV`, `rng(seed)`.
- **Câmera:** `camPath([{p, pos, look}, ...], p)` com easing, `setCam(pos, look, shake, t)`, `toScreen(v3)`.
- **Objetos:** `mat(cor, opts)`, `canvasTex(w, h, draw, repeat)`, `signMesh('TEXTO', {w, h})` (o texto se ajusta sozinho à placa), `makeGuy(camisa, pele, cabelo)` + `poseGuy(g, {walk, crouch, arms})`.
- **Overlay:** `hud`, `caption(t, regexDestaque, 64)`, `tag(x, y, título, sub, cor)`, `tag3D(ponto3D, dx, dy, ...)`, `counter(label, valor, x, y)`, `dim3D(a, b, '≈ 100 m', k)`, `brl(v)`, `txt`, `vignette()`.

## Técnicas que funcionaram (piloto 01)

1. **Maquete + raio-X do subsolo.** O solo é um bloco. Tudo com `z > ZC` (o "plano de corte") usa materiais de `fmat()`, que entram numa lista `FADE`. Debaixo da terra, `setFade(0.06)` deixa a parte da frente quase invisível e revela o túnel contra a face cortada (textura de estratos). Divida ruas, calçadas e lajes no plano de corte (`slab()`).
2. **Espaços ocos (túnel, poço) com `side: THREE.BackSide`.** Uma caixa vista por dentro mostra fundo, piso e teto, mas não a parede da frente, então os bonecos lá dentro aparecem. Uma caixa preta sólida escondia tudo.
3. **Crescer coisas com `scale` + `position`.** Túnel cavando, laje sendo cortada, contadores. Repetições (escoras, lâmpadas) usam `InstancedMesh` e `mesh.count` para revelar progressivamente.
4. **Câmera de drone contínua entre cenas.** O último keyframe de uma cena é o primeiro da próxima. Use corte seco com fade preto (0,3 s) só ao trocar de "mundo" (rua → túnel → cofre).
5. **Interior em corte.** Para entrar no cofre, esconda o prédio (`bankG.visible = false`) e mostre o grupo do interior com paredes baixas na frente.
6. **Etiquetas no overlay, presas a pontos 3D** (`tag3D`), em vez de texto 3D: ficam nítidas, grandes e sempre de frente.
7. **Cidade procedural** com `rng(semente)` e uma lista `OCC` de áreas proibidas (onde ficam a casa, o banco e **as posições da câmera**, senão a câmera nasce dentro de um prédio).

## Legibilidade (o motivo nº 1 de "ficou ruim de ver")

- Legenda **≥ 60 px** em 1080p (o engine usa 64–66), 2 linhas no máximo, palavras-chave em âmbar, caixa escura atrás.
- Etiquetas: título **34 px**, subtítulo **24 px**, no máximo **2 na tela** ao mesmo tempo.
- Contadores grandes (84–100 px) num canto fixo, longe da legenda (faixa inferior reservada).
- Janelas de prédio esparsas (grade 4×4, ~30% acesas, intensidade ≈ 0,55). Grade densa vira "chuvisco".
- Exposição 1,25 + luz hemisférica forte. Cena noturna, mas **nunca escura** a ponto de esconder o assunto.
- Objeto principal ocupa ≥ 25% da tela. Se o boneco tem menos de 60 px de altura, aproxime a câmera.
- **Sempre** rode `qa_quadros.py` e leia a folha em tamanho de celular antes do render final.

## Fluxo de trabalho

1. Monte o mundo (sem animação) e faça 6–10 previews espalhados pelo vídeo:

```bash
node scripts/render.mjs --page <ep>/versao-3d/index.html --timeline <ep>/build/timeline.json --preview 3 10 20 30 40 50
```

2. Veja os PNGs (`<ep>/versao-3d/build/preview/`). Corrija enquadramento, oclusão e texto. Repita.
3. Render final em segundo plano (~1 s/quadro em CPU; 60 s ≈ 30 min):

```bash
node scripts/render.mjs --page ... --timeline ... --video <ep>/versao-3d/build/video_mudo.mp4
```

4. Mixagem: skill `narracao-mixagem`. QA visual: `qa_quadros.py`.

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| Página em branco, "Failed to resolve module" | Módulos ES não carregam via `file://`. Use o `render.mjs` (ele serve `/three/` e `/engine/`). |
| `three` não encontrado | `npm install` na pasta `canal-mapa-do-crime/` (o `package.json` fixa three 0.187.0). |
| WebGL indisponível no headless | O `render.mjs` já lança o Chromium com `--use-angle=swiftshader --enable-unsafe-swiftshader`. |
| Quadro capturado preto | O renderer precisa de `preserveDrawingBuffer: true` (o engine já faz). |
| Bonecos invisíveis no túnel | Caixa do túnel opaca por fora → use `BackSide`. |
| Câmera dentro de prédio | Adicione a área ao `OCC`. |
| Texto de placa cortado | `signMesh` reduz a fonte automaticamente; aumente `w` se ficar pequeno. |
| Objetos transparentes "piscando" | Use `depthWrite = false` quando a opacidade for < 1 (o `setFade` faz isso). |
| Lento | Evite sombras e muitas `PointLight`; use `InstancedMesh`; menos de ~300 draw calls. |

## Referência completa

`canal-mapa-do-crime/piloto-01-banco-central/versao-3d/cena.js`: 8 cenas, túnel, esgoto, laje, cofre, cidade, carros, bonecos.
