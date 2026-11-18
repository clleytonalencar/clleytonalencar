# Monitor automático do Realme C55 (Termux + servidor)

O celular verifica a si mesmo de hora em hora, faz uma faxina completa todo dia, corrige o que der sozinho e manda um relatório para o seu servidor.
Os scripts ficam **no servidor**: você muda lá e o celular aplica na rodada seguinte.

```
Celular (Termux, serviço sempre ativo)            Seu servidor
  agente.sh ── baixa monitor.sh/config.env ─────▶  /realme/monitor.sh, config.env, pacotes.txt
  monitor.sh ── mede RAM, disco, bateria, temp
            ── corrige via Shizuku (rish)
            ── envia relatório ────────────────▶  /realme/relatorio  → dados/relatorios.jsonl
                                                   /realme/status    → último relatório
                                                   alerta (ntfy) quando surge problema novo
                                                   alerta se o celular ficar 3h sem reportar
```

## O que ele faz sozinho (padrões em `servidor/publico/config.env`)

| Situação | Ação automática |
| --- | --- |
| RAM disponível < 15% | Fecha apps em segundo plano (`am kill-all`), no máximo 1x a cada 30 min |
| Armazenamento livre < 20% | Limpa caches e alerta |
| Bateria > 42 °C | Alerta e alivia o processamento |
| Animações voltaram para 1x (após atualização) | Reaplica 0.5x |
| Atualização reinstalou app removido | Remove de novo (lista `pacotes.txt`) |
| Todo dia de madrugada (ou na primeira chance, se estava desligado) | Faxina: fecha apps parados e limpa caches; recompila os apps (todo dia se carregando, no mínimo 1x por semana) |
| Faxina diária sem rodar há 2 dias | Alerta |
| Ligado há mais de 7 dias | Alerta; com `REINICIO_AUTO=1` reinicia de madrugada, tela apagada e carregando |
| Shizuku parado | Alerta (as correções ficam pausadas até iniciar de novo) |

Sem root e sem desbloquear nada: os comandos rodam com a mesma permissão do ADB, via Shizuku.

## 1. Servidor (automático, pelo Mac)

```bash
bash realme-c55/monitor/deploy.sh usuario@seu-servidor
```

O `deploy.sh` confere Python 3.9+ e systemd, copia os arquivos para `/opt/realme-monitor`, cria o `.env`
na primeira vez (token e tópico de alerta do ntfy aleatórios), sobe o serviço `realme-monitor` (reinicia sozinho
se cair) e salva o token no Mac em `~/.realme-monitor.env`. Rodar de novo só atualiza os arquivos e mantém o `.env`
e a `pacotes.txt` do servidor. Porta padrão 8787 (`PORTA=8790 bash deploy.sh ...` para trocar).

Falta só publicar com HTTPS no proxy que o servidor já usa. Exemplo nginx, dentro do `server` do domínio:

```nginx
location /realme/ { proxy_pass http://127.0.0.1:8787; }
```

Teste: `curl https://SEU-DOMINIO/realme/saude` deve responder `ok`. Assine no app **ntfy** o tópico que está em
`ALERTA_WEBHOOK` no `~/.realme-monitor.env`. A etapa 8 do `PROMPT-CLAUDE-CODE.md` faz tudo isso pelo Claude Code.

## 2. Celular

1. Instale **Termux**, **Termux:API** e **Termux:Boot** da mesma fonte (todos do F-Droid ou todos do GitHub; misturar não funciona) e o **Shizuku**.
2. Abra o Termux:Boot uma vez.
3. Para Termux, Termux:API, Termux:Boot e Shizuku: Bateria **sem restrição** e **Inicialização automática** permitida. Trave o Termux nos recentes (cadeado).
4. **Shizuku**: inicie pela Depuração sem fio (o app guia) ou pelo Mac com o comando que o próprio app mostra. Se houver a opção "Iniciar na inicialização", ative.
5. **rish** (o Termux usando o Shizuku): no Shizuku, "Usar o Shizuku em apps de terminal" > Exportar arquivos para uma pasta. No Termux:
   ```bash
   termux-setup-storage
   cp /sdcard/PASTA-ESCOLHIDA/rish* $PREFIX/bin/ && chmod +x $PREFIX/bin/rish
   sed -i 's/PKG/com.termux/' $PREFIX/bin/rish
   rish -c id    # aceite o pedido do Shizuku; deve mostrar uid=2000(shell)
   ```
6. Instale o monitor (troque URL e TOKEN):
   ```bash
   curl -fsSL -H "Authorization: Bearer TOKEN" https://SEU-DOMINIO/realme/instalar.sh | bash -s https://SEU-DOMINIO TOKEN
   ```
7. Feche o Termux por completo (Sair, na notificação) e abra de novo. Confira com `sv status realme-monitor`.

## Acompanhar

```bash
curl -H "Authorization: Bearer TOKEN" https://SEU-DOMINIO/realme/status
```
No celular: `tail ~/.realme-monitor/monitor.log`.

## Limites honestos

- Depois que o celular reinicia, o Shizuku pode precisar ser iniciado de novo (depende da versão). O monitor continua medindo e alerta no servidor até você iniciar.
- A Realme pode matar apps em segundo plano: os passos 3 e o cadeado nos recentes são o que mantém o serviço vivo.
- Quem tem o token e o servidor controla o que roda no celular. Use HTTPS, token longo e não compartilhe.
- Testado só com simulação no Linux, ainda não num C55 de verdade.
