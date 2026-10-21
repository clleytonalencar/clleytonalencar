# Editor da Fábrica — guia de instalação e integração no PC Xeon

> **Para quem é:** o Claude Code (Opus 5.5) que roda no PC Xeon da fábrica de vídeos.
> **O que é:** um editor de vídeo por linha de comando (Python + ffmpeg), feito em outra sessão, que monta
> vídeos a partir de **modelos de cena**, **predefinições com eixos em %** e **canais com rotação**.
> **Sua missão:** instalar só o editor, validar, e integrar à fábrica para **todos os canais**, criando uma
> identidade e um conjunto de predefinições para cada canal, com rodízio e unicidade vídeo a vídeo.

---

## 1. Resumo do que já existe (estado atual)

| Parte | Situação |
|---|---|
| 21 modelos de cena (Moldura, Janela, Placa, Frente & Fundo, Vidro e Texto, Painel D/E, Retrato, Perfil, Nome, Dossiê, Confronto VS, Antes & Depois, Lado a Lado, Três Evidências, Pilha, Mosaico, Linha do Tempo, Citação, Abertura, Tela Cheia) | pronto e testado |
| 14 transições (shutter, whoosh, zoom… com som de whoosh sintetizado) · 5 movimentos (zoom/pan) · 6 filtros (cinema, pb, arquivo…) | pronto |
| Destaque (palavra que "estoura"), avatar em círculo (vídeo do DreamFace), legenda automática, marca d'água, trilha com *ducking* | pronto |
| Formatos 16:9, 9:16, 1:1, 4:5 | pronto (9:16 testado em 3 modelos) |
| Modo `auto`: roteiro + predefinição → projeto | pronto |
| Modo `produzir`: **canal** → rodízio de predefinição/cor/fundo/trilha + **checagem de unicidade** contra os últimos vídeos + histórico | pronto e testado |
| Render paralelo por cena + cache (só refaz a cena que mudou) | pronto |
| Testado em | Linux, Python 3.13, ffmpeg 6.1.1. **Windows não foi testado** (já tem correção de caminhos `C:\` e do limite de linha de comando, mas valide) |
| Desempenho medido | 40 s de vídeo 1080p ≈ 1,6–2 min numa máquina de 4 núcleos. No Xeon deve ser bem mais rápido (ajuste `FABRICA_JOBS`) |

Nada da fábrica atual (Notion, TTS, DreamFace, geração de imagens) foi integrado ainda. **Isso é seu trabalho.**

---

## 2. Como trazer SÓ o editor para o Xeon

Escolha uma das opções.

### Opção A — arquivo .zip (mais simples)
O dono recebeu `editor-video.zip`. Copie para o Xeon (pendrive, rede, Drive) e extraia, por exemplo em
`C:\fabrica\editor-video` (Windows) ou `~/fabrica/editor-video` (Linux).

### Opção B — git só com a pasta do editor (recomendado se for atualizar depois)
Repositório: `https://github.com/clleytonalencar/clleytonalencar`, branch `claude/eager-lovelace-lnk71x`, pasta `editor-video/`.

```bash
# Windows (PowerShell) ou Linux: precisa de git 2.25+ e acesso ao repositório (gh auth login se for privado)
git clone --depth 1 --filter=blob:none --sparse --branch claude/eager-lovelace-lnk71x https://github.com/clleytonalencar/clleytonalencar.git fabrica-editor
cd fabrica-editor
git sparse-checkout set editor-video
```
Para atualizar depois: `git pull`.

### Opção C — copiar a pasta para dentro do repositório da fábrica
Se a fábrica já tem um repositório, copie `editor-video/` para dentro dele (ex.: `ferramentas/editor-video/`)
e faça commit. Assim o editor e os canais ficam versionados junto com a fábrica.

---

## 3. Instalação e validação

### 3.1 Dependências
| Item | Windows | Linux (Ubuntu/Debian) |
|---|---|---|
| Python 3.9+ | `winget install Python.Python.3.12` | já vem; senão `sudo apt install python3` |
| ffmpeg 6 ou 7 (com drawtext) | `winget install Gyan.FFmpeg` e reabra o terminal | `sudo apt install ffmpeg` |
| Fonte Inter (recomendado) | baixe em fonts.google.com/specimen/Inter e instale | `sudo apt install fonts-inter` |

Sem bibliotecas Python extras. Sem a Inter, o editor usa Arial (Windows) ou DejaVu (Linux). Para fixar
uma fonte, use `"fonte": "C:/fabrica/fontes/Inter-Bold.otf"` no `canal.json`.

### 3.2 Validar (rode nesta ordem, dentro de `editor-video/`)
```bash
python fabrica.py modelos                 # lista modelos/transições/movimentos/filtros
python fabrica.py demo --preview          # gera mídias de teste e exemplos/demo.preview.mp4
python fabrica.py catalogo -o catalogo.png
python fabrica.py produzir exemplos/roteiro-exemplo.json --canal canais/exemplo-true-crime --id teste-1 --preview
```
Critério de aceite: os 4 comandos terminam sem `ERRO`, o vídeo abre e as cenas mostram textos.
Se der erro, veja a seção 9 (problemas comuns) e rode com `FABRICA_DEBUG=1` para salvar o filtro de cada cena.

---

## 4. Arquitetura

```
editor-video/
├── fabrica.py                 CLI: modelos | catalogo | auto | render | produzir | canal | demo
├── motor/
│   ├── cena.py                "caneta": cartões, sombras, círculos, textos, etiquetas, entrada animada
│   ├── modelos.py             catálogo de modelos (@modelo(...)); crie novos aqui
│   ├── render.py              render por cena (paralelo + cache), transições, filtros, marca, trilha
│   ├── auto.py                roteiro + predefinição -> projeto (distribui os eixos por %)
│   ├── rotacao.py             canais: rodízio, variação de %, assinatura e similaridade, histórico
│   └── util.py                ffprobe, fontes, escape de caminhos, chamada do ffmpeg
├── predefinicoes/             predefinições compartilhadas (documentario-classico, arquivo-sombrio, editorial-rapido)
├── canais/exemplo-true-crime/ canal de exemplo (canal.json; historico.jsonl é criado sozinho)
└── exemplos/roteiro-exemplo.json
```

Fluxo:
```
tarefa da fábrica ──(adaptador que VOCÊ vai criar)──▶ roteiro.json
roteiro.json + canais/<canal>/canal.json ── produzir ──▶ projeto.json ──▶ cenas em cache ──▶ video.mp4
                                                     └──▶ historico.jsonl (assinatura do vídeo)
```

---

## 5. Formatos de arquivo

### 5.1 `roteiro.json` (um por vídeo; caminhos relativos à pasta do roteiro ou absolutos)
```json
{
  "formato": "16:9",
  "avatar": "audio/apresentador_dreamface.mp4",
  "blocos": [
    { "modelo": "abertura", "texto": "O CASO X", "subtexto": "a execução que deu errado",
      "narracao": "audio/01.mp3", "midias": ["img/01.jpg"] },
    { "narracao": "audio/02.mp3", "texto_narracao": "Texto falado neste bloco...",
      "midias": ["img/02.jpg", "img/03.jpg"], "rotulos": ["acusada", "vítima"], "destaque": "1995" },
    { "modelo": "placa", "narracao": "audio/09.mp3", "texto": "E SE FOSSE NO BRASIL?" }
  ]
}
```
Campos por bloco: `narracao` (áudio; define a duração "Auto"), `texto_narracao` (legenda), `midias`
(a quantidade decide os modelos possíveis), `texto`, `subtexto`, `rotulos`, `etiqueta`, `destaque`,
`avatar`, e opcionalmente `modelo`/`transicao`/`movimento`/`filtro` para **forçar** uma escolha.

### 5.2 Predefinição (`predefinicoes/*.json` ou dentro da pasta do canal)
```json
{
  "nome": "Arquivo sombrio",
  "variacao_pct": 10,
  "eixos": {
    "templates":  { "pct": 60, "modo": "escolher", "lista": ["moldura", "dossie", "pilha", "evidencias"] },
    "avatar":     { "pct": 20 },
    "destaques":  { "pct": 40 },
    "transicoes": { "pct": 40, "modo": "escolher", "lista": ["preto", "desfoque", "persiana", "fade"] },
    "movimento":  { "pct": 85, "modo": "escolher", "lista": ["zoom_in", "zoom_out", "pan_cima"] },
    "filtros":    { "pct": 60, "modo": "escolher", "lista": ["arquivo", "pb", "cinema"] },
    "legenda":    { "ativo": true, "estilo": "rodape", "palavras": 6 }
  }
}
```
- `pct` = % das cenas que recebem o eixo; o resto fica "limpo" (Templates fora do % viram `tela_cheia`).
- `modo`: `todos` (catálogo inteiro, com `excluir` opcional) ou `escolher` + `lista`.
- `variacao_pct`: a cada vídeo, cada `pct` oscila ± esse valor.

### 5.3 Canal (`canais/<slug>/canal.json`)
```json
{
  "nome": "True Crime BR",
  "identidade": {
    "formato": "16:9", "fps": 30,
    "paleta": ["#E2A900", "#E5484D", "#3DA5D9"],
    "fundos": ["#0d0f14", "#120d0d", "#0b1016"],
    "fonte": "fontes/Inter-ExtraBold.otf",
    "marca":  { "logo": "marca/logo.png", "posicao": "sup-dir", "opacidade": 0.7, "altura": 0.06 },
    "trilha": { "volume": 0.12, "abaixar_na_fala": true }
  },
  "predefinicoes": ["documentario-classico.json", "arquivo-sombrio.json", "editorial-rapido.json"],
  "trilhas": ["trilhas/"],
  "variacao_pct": 10,
  "unicidade": { "janela": 10, "similaridade_max": 0.5, "tentativas": 40 }
}
```
Caminhos relativos à pasta do canal. `predefinicoes` procura primeiro na pasta do canal e depois em
`predefinicoes/`. `trilhas` aceita pasta, arquivo ou padrão (`trilhas/*.mp3`).

### 5.4 `historico.jsonl` (gerado; **não apague, faça backup**)
Uma linha por vídeo final: `video_id`, data, predefinição, semente, cor, fundo, trilha, similaridade e a
**assinatura** (sequência de modelos, pares de modelos, transições, movimentos, filtros, cor, trilha).
Renders com `--preview` não entram no histórico.

---

## 6. Como funciona a rotação e a unicidade (`fabrica.py produzir`)

A cada vídeo, o comando:
1. **Sorteia, cada um de forma independente,** a predefinição, a cor da paleta, o fundo e a trilha, entre
   as opções que não apareceram nos últimos usos (metade da lista fica bloqueada). As combinações não
   se repetem em ciclo fixo.
2. Gera uma **semente** a partir de `canal + video_id`. O mesmo vídeo sempre sai igual (reprodutível).
3. Faz cada `pct` dos eixos oscilar ± `variacao_pct`.
4. Gera o projeto e calcula a **similaridade** (0 a 1) com cada um dos últimos `janela` vídeos do canal. Pesos:
   ordem dos modelos 30%, pares de modelos 20%, transições 15%, movimentos 10%, filtros 10%, trilha 8%, cor 7%.
5. Se passar de `similaridade_max`, sorteia de novo, até `tentativas` vezes, e fica com o mais diferente.
   Se nem o melhor passar, avisa **"ACIMA do limite"**. Isso significa que o canal tem pouca variedade:
   adicione predefinições, trilhas ou cores.
6. Renderiza e grava no histórico.

Resultado medido no canal de exemplo (8 vídeos simulados): similaridade entre 0,24 e 0,44, com
predefinição, cor, fundo e trilha variando de forma independente.

```bash
python fabrica.py produzir caminho/roteiro.json --canal canais/true-crime-br --id <id-da-tarefa>
python fabrica.py produzir ... --preview       # rascunho, não grava histórico
python fabrica.py produzir ... --so-projeto    # só gera o projeto.json
python fabrica.py canal canais/true-crime-br   # rodízio e últimos vídeos
```

---

## 7. Política do YouTube: o que a rotação resolve e o que NÃO resolve

Leia isto antes de prometer qualquer coisa ao dono.

O YouTube **desmonetiza canais inteiros** no Programa de Parcerias por **conteúdo inautêntico**
(antes chamado "conteúdo repetitivo": vídeos produzidos em massa a partir de um molde, que só mudam
detalhes) e por **conteúdo reutilizado** (material de terceiros sem contribuição original relevante).
A análise é feita por **pessoas olhando o canal como um todo**, não só por um algoritmo de imagem.

- **O que a rotação deste editor resolve:** o canal não fica com cara de "mesmo template com fotos
  trocadas". Cada vídeo tem edição, ritmo, cores e trilha diferentes, o que melhora a experiência e a
  retenção e tira a impressão de produção em massa.
- **O que ela NÃO resolve, e não deve ser usada para disfarçar:** roteiro igual com nomes trocados,
  narração reaproveitada, material de terceiros sem transformação, vídeos sem valor próprio. Variar a
  edição de um conteúdo repetitivo **não o torna original**, e um revisor percebe.

Regras que a fábrica precisa cumprir **em todo vídeo** (implemente como checagens, seção 8, tarefa T7):
1. **Roteiro original por vídeo:** pesquisa, estrutura e texto próprios. Nada de "mesmo roteiro, outro caso".
2. **Narração própria:** TTS ou voz, com comentário, análise e contexto (ex.: o bloco "E se fosse no Brasil?").
3. **Mídia própria ou transformada:** imagens geradas, mapas, linhas do tempo, documentos públicos
   comentados. Trechos de TV/bodycam só curtos e com comentário por cima.
4. **Variedade entre vídeos do mesmo canal:** temas, estruturas de roteiro, títulos e thumbs diferentes.
5. **Divulgação de conteúdo alterado ou sintético** quando realista (a caixa do YouTube Studio), conforme a regra vigente.
6. **Ritmo humano de publicação:** não publicar dezenas de vídeos quase iguais por dia.

---

## 8. Suas tarefas no Xeon (em ordem)

Marque cada tarefa ao concluir e **mostre o resultado ao dono antes de passar para a próxima**.

- [ ] **T1 — Instalar e validar** (seção 3). Anote o sistema, a versão do ffmpeg e o tempo de render da demo.
      Ajuste `FABRICA_JOBS` (variável de ambiente) para ~metade dos núcleos físicos do Xeon e meça de novo.
- [ ] **T2 — Mapear a fábrica atual. Não suponha nada.** Descubra e documente em `editor-video/FABRICA.md`:
      onde ficam os roteiros, os áudios de narração (TTS), os vídeos do DreamFace, as imagens geradas e as
      thumbs; como as tarefas são controladas (o Notion usa o banco "Gestão de tarefas" com os campos
      `TITULO ORIGINAL`, `TITULO`, `TEXTO DA THUMB`, `VIDEO` e o status `ROTEIRO/DREAMFACE`); quais canais existem.
- [ ] **T3 — Adaptador "tarefa → roteiro.json".** Um script (ex.: `adaptador_fabrica.py`) que pega uma
      tarefa pronta e gera o `roteiro.json`: um bloco por trecho de narração, com o áudio daquele trecho, o
      texto falado (`texto_narracao`) e as imagens do trecho. Se a narração vier num arquivo único, corte
      por pausas (`silencedetect` do ffmpeg) ou por marcações do roteiro. Escolha `modelo` fixo só para
      abertura, placa final e citações; o resto fica para o sorteio.
- [ ] **T4 — Um canal por canal real.** Para cada canal da fábrica, crie `canais/<slug>/` com:
      `canal.json`, `marca/logo.png` (PNG transparente), `trilhas/` (**só música com licença de uso**),
      paleta de 3–4 cores da marca, fundos e **3 a 5 predefinições próprias**, diferentes entre si no
      ritmo, nos modelos permitidos, nas transições e nos filtros. Siga o nicho:
      - *true crime / mistério:* dossiê, evidências, linha do tempo, citação, filtros arquivo/pb, transições preto/desfoque;
      - *pesca / tutorial:* moldura, painel, antes & depois, grade, nome, transições empurrar/whoosh, filtro quente;
      - *Shorts:* `"formato": "9:16"`, cenas curtas, legenda `destaque`, mais destaques.
      Use `python fabrica.py catalogo` e `--preview` para mostrar cada predefinição ao dono antes de aprovar.
- [ ] **T5 — Ligar ao pipeline.** Quando a tarefa chegar ao status de edição: gerar o roteiro (T3), rodar
      `produzir --canal <canal> --id <id da tarefa>`, salvar o MP4 na pasta de saída da fábrica, gravar o
      caminho do vídeo na tarefa e mudar o status. Use o `id` da tarefa como `--id`: assim, refazer a
      mesma tarefa gera o mesmo vídeo.
- [ ] **T6 — Fila e lote.** Processar várias tarefas em sequência (um vídeo por vez; as cenas já rodam em
      paralelo), com log por vídeo, tentar de novo em caso de erro e **não travar a fila** por causa de um
      vídeo com problema. Fazer backup do `historico.jsonl` de cada canal.
- [ ] **T7 — Checagens de conformidade (seção 7), antes do render:**
      - **similaridade de roteiro:** compare o texto do roteiro novo com os últimos ~30 do mesmo canal
        (Jaccard de *shingles* de 5 palavras); acima de ~0,3, **bloqueie** e avise;
      - **reuso de mídia:** a mesma imagem (hash do arquivo) não pode aparecer em mais de N vídeos do canal;
      - **título e texto da thumb** diferentes dos últimos vídeos;
      - registre os resultados no histórico do canal.
- [ ] **T8 — Melhorias opcionais (pergunte antes):** legenda sincronizada palavra a palavra com Whisper;
      modelos novos com fotos reais (estilo "Cinema50": portal, trilho lateral, galeria, panorama, díptico);
      vinheta de abertura e encerramento por canal; geração da thumb a partir do mesmo projeto.

### Como criar um modelo novo
Em `motor/modelos.py`:
```python
@modelo("diptico", "CINEMA", "Díptico", (2, 2), 5.0, "duas fotos verticais lado a lado", texto_embaixo=True)
def diptico(c, cena):
    base = c.fundo()
    for i, cx in enumerate((0.33, 0.67)):
        card = c.cartao(i, c.W * 0.28, c.H * 0.70, borda=6, rot=(-2, 2)[i])
        base = c.colocar(base, card, c.W * cx, c.H * 0.47, atraso=0.1 + 0.3 * i, entrada=("esquerda", "direita")[i])
    return c.texto(base, cena.get("texto"), "(w-text_w)/2", f"h-{int(120 * c.u)}", tam=44, atraso=0.7, largura=c.W * 0.8)
```
Depois rode `python fabrica.py catalogo` para ver a miniatura. Mudar o código de um modelo invalida o cache sozinho.

---

## 9. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `ffmpeg não encontrado` | instale e **reabra o terminal** (PATH). Teste `ffmpeg -version` |
| `No such filter: 'drawtext'` | build do ffmpeg sem freetype. No Windows use a build "full" do gyan.dev |
| erro de fonte / texto não aparece | fixe `"fonte"` no `canal.json` com caminho absoluto usando `/` |
| erro com caminho `C:\...` dentro do filtro | os caminhos já passam por `cam()` em `motor/util.py`. Se aparecer algum novo, use `cam()` nele também |
| `Option not found` com `-/filter_complex` | ffmpeg antigo com número de versão estranho: force 6 em `versao_ffmpeg()` |
| render lento | use `--preview` para revisar e ajuste `FABRICA_JOBS`. Sombras e `zoompan` são as partes pesadas |
| "ACIMA do limite" de similaridade | o canal precisa de mais predefinições, trilhas ou cores; ou suba `similaridade_max` com cuidado |
| cena com mídias demais ou de menos | cada modelo tem mínimo e máximo (`fabrica.py modelos`). O `auto` corta o excesso; um modelo forçado não |

---

## 10. Prompt para colar no Claude do Xeon

```
Você está no PC Xeon da minha fábrica de vídeos. Copiei para cá a pasta editor-video (editor de vídeo
por linha de comando em Python + ffmpeg). Leia editor-video/INSTRUCOES-XEON.md inteiro antes de começar.
Faça as tarefas da seção 8 em ordem, começando pela T1 (instalar e validar) e pela T2 (mapear a fábrica
atual sem supor nada). Pare e me mostre o resultado ao fim de cada tarefa antes de seguir.
Regras: não publique nada no YouTube, não apague historico.jsonl, use só trilhas com licença,
e respeite a seção 7 (a rotação é para dar variedade, não para disfarçar conteúdo repetido).
```
