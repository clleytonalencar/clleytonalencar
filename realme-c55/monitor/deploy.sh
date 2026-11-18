#!/usr/bin/env bash
# Instala ou atualiza o servidor do monitor via SSH. Rode no Mac, na pasta realme-c55/monitor:
#   bash deploy.sh usuario@servidor
# Na primeira vez cria o .env no servidor (token e tópico de alerta aleatórios).
# Nas próximas, só atualiza os arquivos e mantém o .env.
# Ao final salva no Mac, em ~/.realme-monitor.env, o token e o tópico de alertas.
set -euo pipefail
ALVO="${1:?uso: bash deploy.sh usuario@servidor}"
PORTA="${PORTA:-8787}"
cd "$(dirname "$0")"

echo "== Conferindo o servidor =="
ssh "$ALVO" 'command -v python3 >/dev/null && command -v systemctl >/dev/null && python3 -c "import sys; assert sys.version_info >= (3,9)"' \
  || { echo "O servidor precisa de Python 3.9+ e systemd."; exit 1; }
ssh "$ALVO" "! (ss -ltn 2>/dev/null || netstat -ltn) | grep -q ':$PORTA ' || systemctl is-active --quiet realme-monitor" \
  || { echo "A porta $PORTA já está em uso por outro serviço. Rode de novo com PORTA=outra bash deploy.sh $ALVO"; exit 1; }

echo "== Enviando arquivos =="
TMP=$(ssh "$ALVO" mktemp -d)
scp -q -r servidor/servidor.py servidor/realme-monitor.service servidor/instalar-remoto.sh servidor/publico "$ALVO:$TMP/"

echo "== Instalando (pode pedir a senha do sudo) =="
ssh -t "$ALVO" "sudo bash $TMP/instalar-remoto.sh $TMP $PORTA"

echo "== Guardando o token no Mac =="
umask 077
scp -q "$ALVO:.realme-monitor.env" "$HOME/.realme-monitor.env" && ssh "$ALVO" 'rm -f ~/.realme-monitor.env'
chmod 600 "$HOME/.realme-monitor.env"
echo "SERVIDOR_SSH=$ALVO" >> "$HOME/.realme-monitor.env"
grep -E '^(MONITOR_PORT|ALERTA_WEBHOOK)=' "$HOME/.realme-monitor.env"
echo "Token salvo em ~/.realme-monitor.env (não compartilhe)."
echo "Falta: publicar /realme/ com HTTPS no proxy do servidor (nginx/Caddy) e assinar o tópico de alertas no app ntfy."
