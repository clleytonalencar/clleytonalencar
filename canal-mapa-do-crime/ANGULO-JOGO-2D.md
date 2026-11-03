# Ângulo "jogo 2D": o crime contado em fases

> **"Todo plano perfeito tem um Game Over."**

A mesma pesquisa e o mesmo roteiro do Mapa do Crime, mas a animação imita um **jogo 2D em pixel art**:

- **Bonecos** genéricos com uniforme e cores.
- **Cenário em corte**, tipo casa de boneca, onde dá para ver os cômodos, o túnel e o subsolo ao mesmo tempo.
- **HUD de jogo:** fase, relógio, barras de progresso e painel de "inventário".
- **Caixa de diálogo do narrador** com texto datilografado.
- **Balões de "!"** nas viradas e **trilha chiptune (8-bit)**.

Piloto pronto para comparar: `piloto-01-banco-central/entregas/piloto-01-pixel.mp4`. Tem a mesma narração de 61s da versão em motion graphics (`piloto-01-banco-central.mp4`).

## Por que é um ângulo novo

Dados da NexLev (03/11/2026):

| Canal | O que faz | Sinal |
|---|---|---|
| **Crime Paint** (EUA, criado em nov/2025) | Explica true crime com desenhos simples estilo Paint | 42,9 mil inscritos, 7 milhões de views em **20 vídeos**, ~US$4,3 mil/mês estimados, outlier 19,6 |
| **Pixels And Hammers** (criado em 18/10/2026) | Histórias contadas em pixel art animado | 329 mil views nas **primeiras 2 semanas**, outlier 10,3 |
| **Relatos Pintados** (Argentina, jan/2026) | Crimes e golpes em animação 2D, formato "POV", em espanhol | 1,3 milhão de views, ~US$430/mês estimados |

**No Brasil:** buscando caso criminal real contado em estilo jogo ou pixel, só aparece gameplay de jogo de terror. Ninguém conta casos brasileiros assim.

## Por que funciona

1. **Público gamer.** O Brasil tem um público gamer enorme, e pixel art é reconhecido no feed em meio segundo.
2. **Explica bem.** O corte "casa de boneca" mostra causa e efeito: a terra sai do túnel, vira saco atrás da parede falsa e vai para a caminhonete. Tudo numa tela só.
3. **Sem imagem real.** Não precisa de foto, vídeo de TV nem rosto de ninguém, então não há risco de direitos autorais nem de violência explícita.
4. **Personagens genéricos.** Ninguém real é retratado, o que reduz o risco de difamação e de expor a imagem de vítimas.
5. **Produção barata e reaproveitável.** Os blocos de cenário (solo, rua, prédio, túnel) e os bonecos servem para todos os casos. O piloto inteiro tem 4,9 MB.
6. **Fases dão estrutura e retenção.** "FASE 5: O IMPREVISTO" funciona como capítulo e como gancho ao mesmo tempo.

## A regra de ouro: o criminoso não é o "jogador"

O risco desse formato é **glamorizar o crime** e virar um "jogue como ladrão". Para não cair nisso:

- **Todo episódio termina na consequência.** A última fase é a investigação e a prisão, e a tela final diz **"GAME OVER"** com as penas reais. O crime é o jogo que eles perdem.
- **Use para casos sem vítima fatal:** golpes, furtos, fugas, fraudes, cercos sem mortes.
- **Em homicídios, use o "Modo Investigação":** o "jogador" é a perícia ou a polícia, que coleta pistas como itens de inventário. **Nunca** animar a morte. A cena do crime aparece só depois, como local isolado.
- **Nada de pontos, prêmios ou "missão cumprida"** associados ao crime. No piloto, o "objetivo" nunca aparece como meta do jogador. O HUD só mostra fatos: tempo, metros, valores.
- **Público adulto.** Pixel art pode atrair crianças. Marque todos os vídeos como **"Não é conteúdo para crianças"** no YouTube Studio e evite cores e personagens infantilizados.

## Estrutura de fases (modelo)

| Fase | Golpe / fuga ("Modo Plano") | Homicídio ("Modo Investigação") |
|---|---|---|
| 1 | O Alvo (gancho) | A Chamada (o caso chega à polícia) |
| 2 | O Terreno (mapa de cima) | O Local (planta do local, já isolado) |
| 3 | O Disfarce / Os Personagens | Os Personagens (suspeitos como "fichas") |
| 4 | A Execução | As Versões (cada depoimento é uma rota no mapa) |
| 5 | O Imprevisto ("!") | A Pista (o item que muda tudo) |
| 6 | O Momento-chave | A Perícia |
| 7 | O Resultado | O Julgamento |
| 8 | **GAME OVER** (prisão e penas) | **CASO ENCERRADO** (sentença) |

## Identidade da versão pixel (já implementada)

- **Resolução interna 480×270** ampliada 4× sem suavização. Os cenários em corte usam zoom 2×.
- **Fonte bitmap 5×7 própria** com acentos do português (sem dependência de fonte externa).
- **Paleta noturna:** céu azul-marinho, solo marrom, vermelho = alerta, âmbar = dados/dinheiro, verde = a empresa de fachada, verde-água = imprevistos.
- **Bonecos 8×12 (vista lateral) e 8×8 (vista de cima),** com variação de cabelo e tom de pele, uniforme verde da empresa de fachada e o funcionário do banco de branco.
- **Transição de cena:** dissolve em blocos pixelados.
- **Trilha:** baixo em onda quadrada (Lá menor, 104 BPM), arpejo, chimbal de ruído, "blip" a cada fase, alerta "!" e jingle final.

## Ferramentas para escalar

| Etapa | Ferramenta |
|---|---|
| Bonecos e animações | **Aseprite** (padrão do mercado para pixel art) |
| Cenários / tiles | Aseprite + **LDtk** ou **Tiled** |
| Animação e render | O motor deste repositório (canvas → Playwright → ffmpeg) ou um motor de jogo (Godot) gravando as cenas |
| Trilha 8-bit | `tools/audio_pixel.py` (gerada no código), **BeepBox** ou **FamiStudio** |
| Voz | Igual ao canal principal: voz humana ou IA com licença comercial |

## Qual escolher?

| | Motion graphics (mapa) | Jogo 2D (pixel) |
|---|---|---|
| Tom | Documental, sério | Leve, viral, jovem |
| Concorrência no BR | Baixa | Praticamente nenhuma |
| Melhor para | Qualquer caso, inclusive homicídios | Golpes, fugas e cercos; homicídios só no "Modo Investigação" |
| Custo por episódio | Médio | Baixo depois que os blocos de cenário e os bonecos existem |
| Risco | Baixo | Glamorização (mitigado pelas regras acima) |

**Sugestão:** publique os dois pilotos como Shorts/teasers na mesma semana e compare **CTR** e **retenção aos 30s** no YouTube Studio. Quem ganhar vira a identidade do canal. Se o pixel ganhar, nomes possíveis: **"Mapa do Crime"** (mantém a marca), **"Crime em Fases"** ou **"Fase Final"**.
