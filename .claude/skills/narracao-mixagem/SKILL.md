---
name: narracao-mixagem
description: Gera narração (TTS) com timeline e legendas, trilha e efeitos em faixas separadas, e faz a mixagem final com níveis MEDIDOS para a voz nunca ficar baixa (−16 LUFS na voz, trilha ≥15 LU abaixo, final −14 LUFS). Use para "narração", "voz", "áudio baixo", "música alta demais", "mixar", "trilha", "efeitos sonoros" ou como etapas 2 e 5 da skill video-true-crime.
---

# Narração, trilha e mixagem

## Por que a voz ficava baixa (caso real do piloto)

| Faixa | Antes | Problema |
|---|---|---|
| Narração (edge-tts) | −21,2 LUFS | Baixa demais para o YouTube |
| Trilha 8-bit | −18,0 LUFS (só ×0,32 na mix) | Ficava só ~7 LU abaixo da voz, e as ondas quadradas cobrem 1–4 kHz, exatamente a faixa onde a voz é entendida |
| Mix antiga | `volume=0.2` "no olho" + loudnorm no final | O loudnorm final sobe tudo junto e não corrige a proporção voz/música |

**Regra:** nunca ajuste volume no olho. Meça cada faixa (LUFS) e posicione a música em relação à voz.

## Padrões do canal

| Item | Alvo |
|---|---|
| Voz (narração) | **−16 LUFS** integrados, compressão 3:1, presença +3 dB em 3 kHz, passa-alta 80 Hz |
| Trilha sob a voz | **≥ 15 LU abaixo da voz** (padrão: base 14 LU abaixo + ducking de ~8 dB quando a voz fala) |
| EQ da trilha | −6 dB em 1–4 kHz (abre espaço para a voz), passa-alta 40 Hz |
| Efeitos (impactos, serra, alertas) | Pico em −12 dBFS, em faixa separada |
| Master | **−14 LUFS**, true peak ≤ −1 dBTP |

## Scripts

Todos ficam em `scripts/` desta skill. Exemplo de variável de apoio:

```bash
S=/home/user/clleytonalencar/.claude/skills/narracao-mixagem/scripts
```

### 1. `tts.py`: narração + timeline + legendas

```bash
python3 $S/tts.py --scenes scenes.json --out-dir build --voice pt-BR-AntonioNeural --rate +15%
```

- Uma chamada TTS por cena. Mede a duração real e monta `build/timeline.json` com `start`/`end` de cada cena e as legendas por frase (`cues`). O timeline dirige a animação.
- **Ajuste de duração:** se passar do alvo, corte texto primeiro e só depois suba o `--rate` (máximo +20%; acima disso soa robótico).
- **Voz de protótipo:** edge-tts não tem licença comercial clara. Para vídeo monetizado, grave voz humana (ou use um serviço licenciado) cena a cena, com os mesmos ids, e substitua os mp3/`narracao.wav`.
- Em ambiente com proxy que re-assina TLS, o script já aponta o `certifi` para o bundle do proxy.

### 2. `trilha.py`: música e efeitos em faixas SEPARADAS

```bash
python3 $S/trilha.py --timeline build/timeline.json --eventos eventos.json --out-dir build --estilo cinematico
```

- `--estilo cinematico` (drone grave + pulso tipo coração) ou `chiptune` (8-bit, já com passa-baixa para não mascarar a voz).
- `eventos.json` sincroniza os efeitos às cenas (`{"tipo":"serra","cena":"laje","p":0.3,"ate":0.85}`). Tipos disponíveis: `maquina`, `impacto`, `whoosh`, `serra`, `estouro`, `ticks`, `alerta`, `fim`.
- Música licenciada (Artlist, Epidemic, Biblioteca de Áudio do YouTube) entra no lugar do `trilha.wav`, e a mixagem cuida do nível.

### 3. `mix.py`: mixagem medida + relatório + reprovação automática

```bash
python3 $S/mix.py --voz build/audio/narracao.wav --trilha build/trilha.wav --sfx build/sfx.wav --video build/video_mudo.mp4 --out entregas/final.mp4
```

Saída: o vídeo final mais `final_mix.json`, com voz LUFS, trilha LUFS (após ducking), diferença em LU, LUFS final e pico. **Sai com erro (código 2)** se a voz ficar menos de 15 LU acima da trilha. Nesse caso, rode de novo com `--gap 16` ou `--gap 18`.

Exemplos reais:
- Piloto pixel: diferença foi de ~7 LU para **17,7 LU**.
- Piloto motion graphics: a primeira tentativa reprovou com 14,8 LU (a trilha antiga tinha impactos embutidos). Passou com `--gap 17` (17,8 LU).

## Checklist antes de entregar

- [ ] `mix.py` APROVADO e `*_mix.json` salvo junto do vídeo.
- [ ] Ouvir pelo menos o gancho e um trecho com efeito forte (serra, explosão): a frase continua inteligível?
- [ ] Sem silêncio estranho no começo ou no fim, e o card final tem o "hit" de encerramento.
- [ ] Legendas (vindas do `timeline.json`) batem com a fala.
