# MAPA DO CRIME — estrutura do canal

> **"O crime visto de cima."** Casos criminais brasileiros reconstituídos em motion graphics 2D: o terreno, as pessoas, o relógio e o momento em que o plano (ou a mentira) desmorona.

Inspiração de formato: o canal *Battle Analysis* (@battleanalysis79), que fez 1,8 milhão de views no primeiro mês narrando batalhas indianas com mapas e peças. Aqui aplicamos a mesma lógica a crimes brasileiros, para o público brasileiro.

**Visual padrão: 3D (Three.js).** Maquete noturna da cidade, subsolo em "raio-X", bonecos low-poly e câmera de drone. Foi escolhido depois de testar motion graphics 2D e pixel art (o pixel ficou difícil de ler no celular). Piloto: `piloto-01-banco-central/entregas/piloto-01-3d.mp4`. Conceito do pixel art: [`ANGULO-JOGO-2D.md`](ANGULO-JOGO-2D.md).

**Como produzir:** as skills ficam em `.claude/skills/` na raiz do repositório:
- `video-true-crime`: o passo a passo completo;
- `roteiro-true-crime`: pesquisa e roteiro;
- `narracao-mixagem`: voz, trilha e mixagem com níveis medidos;
- `cena-3d-threejs`: cenas 3D e render.

**Padrão de áudio:** voz em −16 LUFS, trilha pelo menos 15 LU abaixo da voz e master em −14 LUFS. O `mix.py` reprova o vídeo automaticamente se a voz ficar baixa.

---

## 1. Posicionamento

| Item | Definição |
|---|---|
| Nome | **Mapa do Crime** (alternativas: *Planta do Crime*, *Crime em Planta*) |
| Slogan | O crime visto de cima |
| Promessa | Você vai **entender como** o crime aconteceu, não só **o que** aconteceu |
| Público | Brasileiros de 18 a 45 anos que consomem true crime, documentário e podcast de casos |
| Diferencial | Ninguém no Brasil faz reconstituição de caso em mapa animado. O que existe é TV, gente falando para a câmera ou slideshow de fotos |
| Tom | Sóbrio e investigativo. Sem sensacionalismo, sem sangue, sem piada com vítima |
| Rosto | Canal faceless: só narração e motion graphics |

## 2. Identidade visual (já implementada no piloto)

**Paleta.** Cada cor tem uma função fixa, e isso vira linguagem do canal:

| Cor | Hex | Uso |
|---|---|---|
| Vermelho | `#e5383b` | Criminoso, rota do crime, alvo |
| Âmbar | `#f2a93b` | Dados, números, dinheiro, medidas |
| Branco-azulado | `#d6e2ee` | Instituições, vítimas, polícia |
| Verde-água | `#3fb8a5` | Imprevistos e infraestrutura (esgoto, câmeras, sensores) |
| Fundo | `#0a0e13` / quadras `#121a23` | Mapa noturno |

**Tipografia.** Inter (títulos em caixa alta com espaçamento largo) e DejaVu Sans Mono (relógio).

**Elementos fixos de tela:**
- **HUD superior esquerdo:** marca + "CASO NN · NOME · CIDADE–UF".
- **HUD superior direito:** data e hora do momento narrado (o relógio é personagem).
- **Etiqueta de capítulo** (`01 · O ALVO`).
- **Legenda dinâmica:** blocos de ~5 palavras, números e palavras-chave em âmbar.
- **Tags** com barra lateral colorida, **pino** de local, **retícula** de alvo, **linhas de cota** ("≈ 100 m").
- **Três "mundos" de câmera:** mapa (vista de cima), corte (vista lateral/subsolo) e planta interna (cômodo). A troca entre eles é um wipe com linha vermelha.
- **Selo fixo:** "REPRESENTAÇÃO ILUSTRATIVA · FORA DE ESCALA".

**Arquivos já gerados:** avatar e thumbnail-modelo em `piloto-01-banco-central/entregas/`.

## 3. Formatos

| Formato | Duração | Frequência | Função |
|---|---|---|---|
| **Episódio** (longo, 16:9) | 12 a 18 min | 1 por semana, mesmo dia e horário | Crescimento, retenção, receita |
| **Corte** (Short, 9:16) | 45 a 60 s | 3 por semana | Descoberta. Mostra só "o momento em que tudo cai" e manda para o episódio |
| **Piloto/teaser** (16:9) | 60 s | No lançamento | Testar estética, voz e CTR antes de investir em episódios longos |

### Estrutura padrão do episódio (8 capítulos)

O piloto segue exatamente esta espinha:

1. **O Alvo (gancho, 0–30 s):** começa no momento mais tenso, com data, hora e um número ("a 1,10 m de R$ 164 milhões").
2. **O Terreno:** mapa de cima. Onde fica tudo, distâncias.
3. **Os Personagens / O Disfarce:** quem é quem, cada um com cor e ícone.
4. **O Plano / A Execução:** linha do tempo animada, com contador.
5. **O Imprevisto:** o que deu errado ou o detalhe que ninguém esperava.
6. **O Momento-chave:** a virada (a laje cede, o celular denuncia, a perícia desmente).
7. **O Desfecho:** prisão, julgamento, pena e o que foi recuperado.
8. **O Gancho:** o que ficou sem resposta + chamada para o próximo caso.

## 4. Séries e pautas (primeiros 3 meses)

Comece pelos **casos táticos** (golpes, cercos, fugas). Eles se encaixam no formato de "análise de batalha", são menos gráficos e mais seguros para monetização. Os homicídios clássicos entram depois que o canal tiver tração.

| Semana | Série | Caso | Por que funciona no mapa |
|---|---|---|---|
| 1 | Grandes Golpes | Furto ao Banco Central de Fortaleza (2005) | Túnel, casa de fachada, esgoto, laje: o piloto vira episódio |
| 2 | Cercos e Caçadas | Caçada ao Lázaro Barbosa (2021) | 20 dias de cerco no mapa de Goiás |
| 3 | Grandes Golpes | Roubo do ouro em Cumbica (2019) | Operação de minutos dentro do aeroporto |
| 4 | Cercos e Caçadas | Sequestro do Ônibus 174 (2000) | Cerco ao vivo, posições da polícia |
| 5 | Grandes Golpes | Ataque a Criciúma (2020) — "Novo Cangaço" | Uma cidade inteira como campo de batalha |
| 6 | Fugas | Fuga da Penitenciária Federal de Mossoró (2024) | Rota de fuga e buscas no mapa |
| 7 | Fugas | Túnel da fuga do Carandiru (2001) | Mesma "escola" de túneis do furto ao BC |
| 8 | Reconstituição | Caso Isabella Nardoni (2008) | Apartamento, tela da janela, linha do tempo minuto a minuto |
| 9 | Grandes Golpes | Ataque a Araçatuba (2021) | Drones, explosivos, reféns no mapa urbano |
| 10 | Cercos e Caçadas | Sequestro de Eloá (2008) | 100 horas de cerco e as decisões táticas |
| 11 | Reconstituição | Caso Richthofen (2002) | Planta da casa, versões contraditórias |
| 12 | Erros da Justiça | Caso Escola Base (1994) | Como a versão falsa se espalhou (mapa de notícias) |

**Antes de produzir cada pauta, confirme datas e números em pelo menos 2 fontes primárias** (sentença, inquérito ou reportagem investigativa).

## 5. Rotina semanal de produção (1 episódio + 3 cortes)

| Dia | Etapa | Entregável |
|---|---|---|
| Seg | Pesquisa | Dossiê do caso: linha do tempo, endereços, personagens, fontes com link |
| Ter | Roteiro | ~1.800 a 2.500 palavras em 8 capítulos + marcações de cena (`[MAPA: zoom na casa]`) |
| Qua | Narração + storyboard | Áudio final + lista de cenas com tempos (o `timeline.json`) |
| Qui | Animação | Cenas 1 a 4 |
| Sex | Animação + mix | Cenas 5 a 8, trilha, legendas, revisão |
| Sáb | Embalagem | 3 opções de thumbnail, 3 títulos, descrição, capítulos, 3 cortes verticais |
| Dom | Folga / pauta seguinte | — |
| **Publicação** | Mesmo dia e horário toda semana (teste 18h–20h, horário de Brasília) | Episódio no ar + 1º corte |

## 6. Ferramentas

| Função | Opção usada no piloto | Opção profissional |
|---|---|---|
| Animação | Motor próprio em HTML/canvas renderizado por Playwright + ffmpeg (`piloto-01-banco-central/`) | After Effects, Motion Canvas ou Remotion |
| Narração | `edge-tts` (voz pt-BR-AntonioNeural), só para protótipo | Voz humana gravada ou ElevenLabs com licença comercial |
| Mapas | Geometria ilustrativa desenhada no código | Base do OpenStreetMap (com crédito "© OpenStreetMap contributors") redesenhada no estilo do canal |
| Trilha | Sintetizada no código (drone + impactos) | Biblioteca com licença (Artlist, Epidemic) ou Biblioteca de Áudio do YouTube |
| Thumbnail | Gerada pelo mesmo motor (`render.js thumb`) | Figma / Photoshop sobre um frame do vídeo |

## 7. Embalagem (título + thumbnail)

**Fórmulas de título** (prometa um "como" ou um detalhe que muda tudo):
- `Como [N pessoas] [fizeram X impossível]` → *Como 36 homens cavaram até o cofre do Banco Central*
- `[Personagem] não sabia que [detalhe] contou outra história`
- `O minuto exato em que [a versão] caiu`
- `[Número] metros / horas / dias até [alvo]`

**Thumbnail:** mapa escuro de cima, rota vermelha, 1 pino e 1 retícula. No máximo 3 a 4 palavras grandes e 1 número. **Nunca** sangue, arma apontada, rosto de vítima ou de menor.

**Descrição-modelo:**
```
[1 frase-gancho do caso]

Neste episódio do Mapa do Crime reconstituímos, em mapa, [caso] — do [início] ao [desfecho].

CAPÍTULOS
00:00 O alvo
...

FONTES
- [fonte 1 com link]
- [fonte 2 com link]

Representação ilustrativa baseada em documentos públicos e reportagens. Pessoas não condenadas são tratadas como suspeitas/acusadas.
```

## 8. Regras legais e de monetização (Brasil)

- **Menores de idade:** o ECA (art. 143) proíbe divulgar nome, foto ou qualquer dado que identifique criança ou adolescente envolvido em ato infracional. Vale mesmo para casos famosos.
- **Quem não foi condenado** é sempre "suspeito" ou "acusado". Afirmar crime sem condenação pode configurar calúnia ou difamação (Código Penal, arts. 138 e 139).
- **Vítimas e familiares:** nada de ridicularizar nem de expor detalhes íntimos que não sejam necessários para entender o caso.
- **Direitos autorais:** não usar trechos de telejornal, fotos de agência nem músicas sem licença. O motion graphics próprio é justamente o que protege o canal disso.
- **YouTube:** true crime com contexto educativo é monetizável. Violência explícita, imagens chocantes e thumbnails sensacionalistas limitam ou desmonetizam o vídeo.
- **Voz de protótipo:** o `edge-tts` usa vozes online da Microsoft sem licença comercial clara. Para os vídeos monetizados, use voz própria ou um serviço com licença comercial.

## 9. Métricas e decisões

Faça a leitura a cada 5 episódios e mude **uma** variável por vez.

| Métrica | Onde ver | O que fazer se estiver ruim |
|---|---|---|
| CTR de impressões | YouTube Studio → Alcance | Testar thumbnail ou título (o Studio permite teste A/B de thumbnail) |
| Retenção aos 30 s | Studio → Engajamento | Reescrever o gancho: começar mais perto do clímax |
| Duração média da visualização | Studio → Engajamento | Cortar o "terreno" e a contextualização, acelerar até o imprevisto |
| Views vindas de Shorts | Studio → Origem do tráfego | Testar cortes começando direto no "momento-chave" |

**Monetização:** confira no YouTube Studio os requisitos atuais do Programa de Parcerias. Como o RPM em português é menor que em inglês, a expansão natural é publicar os mesmos mapas com narração em inglês ou espanhol num segundo canal, reaproveitando toda a animação.

---

## Arquivos desta pasta

```
canal-mapa-do-crime/
├── README.md                      ← este documento (estrutura do canal)
├── ANGULO-JOGO-2D.md              ← ângulo "jogo 2D" (pixel art, fases, Game Over)
└── piloto-01-banco-central/
    ├── README.md                  ← roteiro, fontes e como renderizar
    ├── scenes.json                ← texto da narração por cena
    ├── index.html                 ← motor de motion graphics (canvas)
    ├── tools/tts.py               ← narração + timeline + legendas
    ├── tools/render.js            ← render quadro a quadro (Playwright → ffmpeg)
    ├── tools/audio.py             ← trilha sintetizada + mixagem final
    ├── tools/audio_pixel.py       ← trilha chiptune da versão pixel
    ├── versao-pixel/index.html    ← motor da versão jogo 2D (pixel art)
    └── entregas/                  ← vídeos finais, thumbnails, avatar
```
