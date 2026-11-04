---
name: roteiro-true-crime
description: Pesquisa um caso criminal real (Brasil) e escreve o roteiro narrado em capítulos, com fatos checados, fontes e regras legais (ECA, calúnia), gerando o scenes.json usado pela narração. Use quando pedirem roteiro, pesquisa de caso, pauta, "escreve o texto do vídeo", ou como etapa 1 da skill video-true-crime.
---

# Roteiro de true crime — Mapa do Crime

## 1. Pesquisa (antes de escrever qualquer frase)

1. Reúna **pelo menos 2 fontes independentes** por fato. Prioridade:
   - sentença ou acórdão (sites dos tribunais, Jusbrasil);
   - inquérito ou comunicado oficial (PF, polícias civis, MPs);
   - especial investigativo de grande veículo (Estadão, Folha, G1, O Globo);
   - livro-reportagem.
2. Monte um **dossiê** no README do episódio: linha do tempo com data e hora, lugares (endereços aproximados, distâncias), personagens (papel, situação jurídica), números (valores, metros, horas) e cada fonte com link.
3. Para cada número, anote a fonte ao lado. Se as fontes divergirem (ex.: túnel de 75,4 m na PF × "cerca de 80 m" na imprensa), use o dado oficial e arredonde na fala ("setenta e cinco metros").
4. Marque o que é **incerto** e não afirme na narração.

## 2. Estrutura (8 capítulos, ids estáveis)

| id | Capítulo | Função | Peso no tempo |
|---|---|---|---|
| `gancho` | O Alvo | Começa no momento mais tenso: data, hora e um número | 15% |
| `terreno` | O Terreno | Onde fica tudo, vista de cima, distância | 10% |
| `fachada` | O Disfarce / Personagens | Quem é quem, como se esconderam | 10% |
| `tunel` | A Execução | Linha do tempo do plano, com contador | 15% |
| `esgoto` | O Imprevisto | O que deu errado ou o detalhe inesperado | 12% |
| `laje` | O Momento-chave | A virada | 10% |
| `cofre` | O Resultado | O que aconteceu, números | 15% |
| `fecho` | O Gancho / Desfecho | Consequência + chamada para o próximo | 13% |

Os ids podem mudar por caso (ex.: `chamada`, `local`, `versoes`, `pista`, `pericia`, `julgamento` no "Modo Investigação"), mas mantenha 6 a 10 capítulos, e cada id vira uma cena no `cena.js`.

## 3. Escrita para o ouvido

- **Ritmo:** com a voz a +15%, ~2,6 palavras/s. Para 60 s: ~150 palavras. Para 12 min: ~1.900 palavras.
- Frases curtas (≤ 20 palavras). Uma informação nova por frase.
- Números por extenso quando a voz de IA erra ("cento e sessenta e quatro milhões"), mas a legenda destaca o número.
- Presente narrativo ("eles cavam", "o banco percebe") dá tensão.
- Gancho nos primeiros 5 s: **lugar + hora + ameaça + número**.
- Termine cada capítulo puxando o próximo ("…mas havia um problema que não estava na planta").
- Feche com a consequência real (prisão, pena, o que foi recuperado) e, no teaser, com o próximo capítulo.

## 4. Regras legais e éticas (não negociáveis)

- **Menores:** o ECA (art. 143) proíbe nome, foto, apelido ou detalhe que identifique adolescente em ato infracional, mesmo em caso famoso.
- **Presunção de inocência:** quem não foi condenado com trânsito em julgado é "suspeito" ou "acusado". Afirmar crime sem condenação pode ser calúnia ou difamação (Código Penal, arts. 138–139).
- **Vítimas:** nada de detalhe íntimo desnecessário, nada de humor com vítima, nada de descrição gráfica de violência.
- **Glamorização:** o crime nunca é "missão cumprida". O desfecho sempre mostra a consequência.
- **Imagem:** personagens são genéricos. Nenhum rosto ou logo real recriado.
- **Fontes no card final e na descrição.**

## 5. Saída

`scenes.json` na pasta do episódio:

```json
[
  {"id": "gancho", "text": "Cinco de agosto de 2005, nove da noite. Sob o Banco Central de Fortaleza, um grupo está a um metro de concreto de cento e sessenta e quatro milhões de reais."},
  {"id": "terreno", "text": "Visto de cima: o banco. E a cem metros dali, uma casa alugada."}
]
```

E no README do episódio: tabela **Tempo | Capítulo | Narração | Na tela**, a lista de fatos com fonte e as fontes completas.

## Exemplo pronto

`canal-mapa-do-crime/piloto-01-banco-central/` (README + scenes.json). Fonte principal: Estadão, "Os Toupeiras" (2015).
