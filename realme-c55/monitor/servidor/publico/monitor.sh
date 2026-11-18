#!/data/data/com.termux/files/usr/bin/bash
# Verifica o aparelho, corrige o que der e manda um relatório ao servidor.
# Roda via agente.sh (que antes baixa a versão mais nova deste arquivo).
set -u
D="$HOME/.realme-monitor"; cd "$D" || exit 1
. ./agente.conf; [ -f config.env ] && . ./config.env
export RISH_APPLICATION_ID=com.termux
agora=$(date +%s); hora=$(date +%-H)
alertas=(); acoes=()
log() { echo "$(date '+%F %T') $*" >> monitor.log; tail -n 2000 monitor.log > monitor.log.t && mv monitor.log.t monitor.log; }

# ---------- coleta ----------
mem_total=$(awk '/^MemTotal/{print $2}' /proc/meminfo)
mem_disp=$(awk '/^MemAvailable/{print $2}' /proc/meminfo)
ram_pct=$(( mem_disp * 100 / mem_total ))
read -r disco_total disco_livre < <(df -Pk "$HOME" | awk 'END{print $2, $4}')
disco_pct=$(( disco_livre * 100 / disco_total ))
uptime_dias=$(awk '{print int($1/86400)}' /proc/uptime)

bat=$(timeout 15 termux-battery-status 2>/dev/null || echo '{}')
bat_pct=$(echo "$bat" | jq -r '.percentage // -1')
temp=$(echo "$bat" | jq -r '.temperature // -1' | cut -d. -f1)
carregando=$(echo "$bat" | jq -r '.plugged // "UNPLUGGED"')
[ "$carregando" = UNPLUGGED ] && carregando=0 || carregando=1

shizuku=0
command -v rish >/dev/null && timeout 15 rish -c id 2>/dev/null | grep -q 'uid=2000' && shizuku=1
sh_() { [ "$shizuku" = 1 ] && timeout 900 rish -c "$*" 2>&1 | tail -n 3; }

pode() { local f="ultimo_$1"; [ ! -f "$f" ] || [ $(( agora - $(cat "$f") )) -ge "$2" ]; }
marca() { echo "$agora" > "ultimo_$1"; }

# ---------- regras ----------
[ "$shizuku" = 0 ] && alertas+=("Shizuku parado: abra o app Shizuku e toque em Iniciar (as correções automáticas estão pausadas)")

if [ "$ram_pct" -lt "${RAM_MIN_PCT:-15}" ] && pode ram 1800 && [ "$shizuku" = 1 ]; then
  sh_ am kill-all >/dev/null; marca ram; acoes+=("RAM em ${ram_pct}%: fechou apps em segundo plano")
fi

if [ "$disco_pct" -lt "${DISCO_MIN_PCT:-20}" ]; then
  alertas+=("Armazenamento livre em ${disco_pct}%: apague mídias do WhatsApp ou mova fotos para o Google Fotos")
  if pode disco 21600 && [ "$shizuku" = 1 ]; then
    sh_ pm trim-caches 999G >/dev/null; marca disco; acoes+=("limpou caches de apps")
  fi
fi

if [ "$temp" -ge "${TEMP_MAX:-42}" ]; then
  alertas+=("Bateria a ${temp}°C: deixe o celular descansar, sem capa se estiver carregando")
  if pode temp 1800 && [ "$shizuku" = 1 ]; then sh_ am kill-all >/dev/null; marca temp; acoes+=("aliviou o processamento por temperatura"); fi
fi

if [ "$shizuku" = 1 ] && [ -n "${ANIMACAO:-}" ]; then
  for k in window_animation_scale transition_animation_scale animator_duration_scale; do
    v=$(sh_ settings get global $k | tr -d '\r')
    [ "$v" != "$ANIMACAO" ] && sh_ settings put global $k "$ANIMACAO" >/dev/null && acoes+=("reaplicou $k=$ANIMACAO")
  done
fi

if [ "${REAPLICAR_DEBLOAT:-0}" = 1 ] && [ "$shizuku" = 1 ] && [ -f pacotes.txt ] && pode debloat 21600; then
  instalados=$(sh_ pm list packages | tr -d '\r')
  for p in $(grep -v '^\s*#' pacotes.txt | awk '{print $1}' | grep -E '^[a-z]+\.[a-zA-Z0-9_.]+$'); do
    echo "$instalados" | grep -qx "package:$p" && sh_ pm uninstall --user 0 "$p" >/dev/null && acoes+=("removeu de novo $p")
  done
  marca debloat
fi

# Faxina diária: roda de madrugada (02h-06h) ou, se o celular estava desligado, assim que passar de 30h.
ultimo_diario=$(cat ultimo_diario 2>/dev/null || echo 0)
desde_diario=$(( agora - ultimo_diario ))
if [ "${MANUTENCAO_DIARIA:-1}" = 1 ] && [ "$shizuku" = 1 ] && [ "$desde_diario" -ge 72000 ] \
   && { [ "$hora" -ge 2 ] && [ "$hora" -lt 6 ] || [ "$desde_diario" -ge 108000 ]; } \
   && { [ "$carregando" = 1 ] || [ "$bat_pct" -ge "${BATERIA_MIN_MANUTENCAO:-30}" ]; }; then
  sh_ am kill-all >/dev/null
  sh_ pm trim-caches 999G >/dev/null
  acoes+=("faxina diária: fechou apps parados e limpou caches")
  # Recompilação é mais pesada: todo dia se estiver carregando, senão pelo menos 1x por semana.
  if [ "$carregando" = 1 ] || pode dexopt 604800; then
    sh_ cmd package bg-dexopt-job >/dev/null; marca dexopt; acoes+=("faxina diária: recompilou apps")
  fi
  marca diario
fi
[ "$desde_diario" -ge 172800 ] && [ "$ultimo_diario" != 0 ] && alertas+=("Faxina diária não roda há $(( desde_diario / 86400 )) dias (Shizuku parado ou bateria baixa)")

reiniciar=0
if [ "$uptime_dias" -ge "${UPTIME_MAX_DIAS:-7}" ]; then
  if [ "${REINICIO_AUTO:-0}" = 1 ] && [ "$shizuku" = 1 ] && [ "$carregando" = 1 ] \
     && [ "$hora" -ge 3 ] && [ "$hora" -lt 5 ] \
     && sh_ dumpsys power | grep -q 'mWakefulness=Asleep'; then
    reiniciar=1; acoes+=("reinício automático após ${uptime_dias} dias ligado")
  else
    alertas+=("Ligado há ${uptime_dias} dias: reinicie o celular")
  fi
fi

# ---------- relatório ----------
para_json() { if [ $# -eq 0 ]; then echo '[]'; else printf '%s\n' "$@" | jq -R . | jq -s .; fi; }
rel=$(jq -nc \
  --argjson ram "$ram_pct" --argjson disco "$disco_pct" --argjson bat "$bat_pct" \
  --argjson temp "$temp" --argjson carr "$carregando" --argjson up "$uptime_dias" \
  --argjson shz "$shizuku" --arg faxina "$( [ -f ultimo_diario ] && date -d @"$(cat ultimo_diario)" -Iseconds || echo nunca)" --argjson alertas "$(para_json "${alertas[@]}")" \
  --argjson acoes "$(para_json "${acoes[@]}")" --arg quando "$(date -Iseconds)" \
  '{quando:$quando, ram_livre_pct:$ram, disco_livre_pct:$disco, bateria_pct:$bat,
    temperatura_c:$temp, carregando:($carr==1), dias_ligado:$up, shizuku_ativo:($shz==1), ultima_faxina:$faxina,
    alertas:$alertas, acoes:$acoes}')
log "$rel"

echo "$rel" >> pendentes.jsonl; tail -n 200 pendentes.jsonl > p.t && mv p.t pendentes.jsonl
falhou=0; restantes=()
while IFS= read -r linha; do
  if [ "$falhou" = 0 ] && curl -fsS --max-time 20 -X POST -H "Authorization: Bearer $TOKEN" \
       -H 'Content-Type: application/json' --data "$linha" "$SERVIDOR_URL/realme/relatorio" >/dev/null 2>&1; then
    :
  else
    falhou=1; restantes+=("$linha")
  fi
done < pendentes.jsonl
if [ ${#restantes[@]} -gt 0 ]; then printf '%s\n' "${restantes[@]}" > pendentes.jsonl; else : > pendentes.jsonl; fi

[ "$reiniciar" = 1 ] && sh_ svc power reboot
exit 0
