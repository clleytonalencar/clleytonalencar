#!/usr/bin/env bash
# Executado no servidor pelo deploy.sh, com sudo. Não rode direto.
set -euo pipefail
TMP="$1"; PORTA="$2"; D=/opt/realme-monitor
mkdir -p "$D"
cp "$TMP/servidor.py" "$D/"
rm -rf "$D/publico.novo" && cp -r "$TMP/publico" "$D/publico.novo"
# mantém a lista de pacotes que você já tiver subido no servidor
[ -f "$D/publico/pacotes.txt" ] && cp "$D/publico/pacotes.txt" "$D/publico.novo/pacotes.txt"
rm -rf "$D/publico" && mv "$D/publico.novo" "$D/publico"
chmod -R a+rX "$D"
if [ ! -f "$D/.env" ]; then
  umask 077
  cat > "$D/.env" <<ENV
MONITOR_TOKEN=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
MONITOR_PORT=$PORTA
ALERTA_WEBHOOK=https://ntfy.sh/realme-$(python3 -c 'import secrets; print(secrets.token_hex(8))')
SEM_RELATORIO_HORAS=3
ENV
  echo ".env criado"
else
  echo ".env existente mantido"
fi
chmod 600 "$D/.env"
cp "$TMP/realme-monitor.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now realme-monitor >/dev/null
systemctl restart realme-monitor
sleep 2
PORTA=$(grep ^MONITOR_PORT= "$D/.env" | cut -d= -f2)
curl -fsS "http://127.0.0.1:$PORTA/realme/saude" >/dev/null && echo "servidor respondendo na porta $PORTA" \
  || { journalctl -u realme-monitor -n 20 --no-pager; exit 1; }
# entrega uma cópia do .env ao usuário do SSH para o deploy.sh trazer ao Mac
U="${SUDO_USER:-root}"
H=$(getent passwd "$U" | cut -d: -f6)
install -m 600 -o "$U" "$D/.env" "$H/.realme-monitor.env"
rm -rf "$TMP"
