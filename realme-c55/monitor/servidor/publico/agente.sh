#!/data/data/com.termux/files/usr/bin/bash
# Agente fixo do celular. Baixa a versão mais nova do monitor no servidor e roda.
# Se o servidor estiver fora do ar, usa a última cópia boa.
D="$HOME/.realme-monitor"
. "$D/agente.conf"                       # SERVIDOR_URL e TOKEN
export RISH_APPLICATION_ID=com.termux
cd "$D" || exit 1

baixa() {  # baixa um arquivo e só troca se ele for válido
  curl -fsS --max-time 30 -H "Authorization: Bearer $TOKEN" \
       "$SERVIDOR_URL/realme/$1" -o "$1.novo" 2>/dev/null || { rm -f "$1.novo"; return; }
  case "$1" in *.sh|*.env) bash -n "$1.novo" 2>/dev/null || { rm -f "$1.novo"; return; } ;; esac
  mv -f "$1.novo" "$1"
}
for f in monitor.sh config.env pacotes.txt; do baixa "$f"; done

[ -f config.env ] && . ./config.env
echo "${INTERVALO_SEG:-3600}" > intervalo
[ -f monitor.sh ] && timeout 1800 bash ./monitor.sh
