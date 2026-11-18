#!/data/data/com.termux/files/usr/bin/bash
# Instala o monitor no Termux. Uso (dentro do Termux):
#   curl -fsSL -H "Authorization: Bearer TOKEN" https://SEU-SERVIDOR/realme/instalar.sh | bash -s https://SEU-SERVIDOR TOKEN
set -e
URL="${1:?informe a URL do servidor}"; TOKEN="${2:?informe o token}"
URL="${URL%/}"
D="$HOME/.realme-monitor"

echo "== Pacotes do Termux =="
pkg update -y
pkg install -y curl jq coreutils termux-api termux-services

echo "== Arquivos do monitor =="
mkdir -p "$D"
printf 'SERVIDOR_URL=%q\nTOKEN=%q\n' "$URL" "$TOKEN" > "$D/agente.conf"; chmod 600 "$D/agente.conf"
curl -fsS -H "Authorization: Bearer $TOKEN" "$URL/realme/agente.sh" -o "$D/agente.sh"
bash -n "$D/agente.sh"; chmod 700 "$D/agente.sh"

echo "== Serviço que fica sempre rodando (reinicia sozinho se cair) =="
S="$PREFIX/var/service/realme-monitor"
mkdir -p "$S/log"
cat > "$S/run" <<RUN
#!$PREFIX/bin/sh
exec 2>&1
termux-wake-lock
while true; do
  bash "$D/agente.sh"
  sleep "\$(cat "$D/intervalo" 2>/dev/null || echo 900)"
done
RUN
cat > "$S/log/run" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
mkdir -p "$HOME/.realme-monitor/svlog"
exec svlogd -tt "$HOME/.realme-monitor/svlog"
RUN
chmod 755 "$S/run" "$S/log/run"
rm -f "$S/down"

echo "== Início automático quando o celular liga (Termux:Boot) =="
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/00-realme-monitor" <<BOOT
#!$PREFIX/bin/sh
termux-wake-lock
. $PREFIX/etc/profile
BOOT
chmod 755 "$HOME/.termux/boot/00-realme-monitor"

echo "== Teste =="
command -v rish >/dev/null || echo "AVISO: rish não encontrado. Exporte o rish pelo app Shizuku (veja o README) para as correções automáticas funcionarem."
bash "$D/agente.sh" && tail -n 1 "$D/monitor.log"

echo
echo "Pronto. Feche o Termux por completo (Sair na notificação) e abra de novo para o serviço iniciar."
echo "Ver se está rodando: sv status realme-monitor"
