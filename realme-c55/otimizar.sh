#!/usr/bin/env bash
# Otimização da ROM original do Realme C55 (RMX3710) via ADB, sem root.
# Uso: ligue a Depuração USB (ou sem fio), conecte e rode:  bash otimizar.sh
set -u
cd "$(dirname "$0")"

command -v adb >/dev/null || { echo "ADB não encontrado. Veja o README.md."; exit 1; }
adb get-state >/dev/null 2>&1 || { echo "Nenhum celular conectado (rode 'adb devices')."; exit 1; }

modelo=$(adb shell getprop ro.product.model | tr -d '\r')
echo "Aparelho: $modelo"
case "$modelo" in *RMX3710*) ;; *) read -rp "Não é um RMX3710. Continuar mesmo assim? [s/N] " r; [ "$r" = s ] || exit 1;; esac

echo; echo "== 1/5 Removendo apps desnecessários (reversível) =="
grep -v '^\s*#' pacotes.txt | awk '{print $1}' | grep . | while read -r p; do
  out=$(adb shell pm uninstall --user 0 "$p" 2>&1 | tr -d '\r')
  echo "  $p -> $out"
done

echo; echo "== 2/5 Animações em 0.5x =="
adb shell settings put global window_animation_scale 0.5
adb shell settings put global transition_animation_scale 0.5
adb shell settings put global animator_duration_scale 0.5

echo; echo "== 2b Congelar apps em cache e desligar buscas de Wi-Fi/Bluetooth em segundo plano =="
[ -f ajustes-originais.txt ] || for k in cached_apps_freezer wifi_scan_always_enabled ble_scan_always_enabled; do
  echo "$k=$(adb shell settings get global $k | tr -d '\r')" >> ajustes-originais.txt
done
adb shell settings put global cached_apps_freezer enabled
adb shell settings put global wifi_scan_always_enabled 0
adb shell settings put global ble_scan_always_enabled 0

echo; echo "== 2c Notificações garantidas para WhatsApp e WhatsApp Business =="
for p in com.whatsapp com.whatsapp.w4b; do adb shell cmd deviceidle whitelist +$p; done

echo; echo "== 3/5 Limpando cache de todos os apps =="
adb shell pm trim-caches 999G

echo; echo "== 4/5 Compilando apps para rodarem mais rápido (pode levar 10-30 min) =="
echo "   Deixe o celular conectado e na tomada."
for p in com.whatsapp com.whatsapp.w4b com.instagram.android br.gov.meugovbr; do
  adb shell pm path "$p" >/dev/null 2>&1 && adb shell cmd package compile -m speed -f "$p"
done
adb shell cmd package compile -m speed-profile -a
adb shell cmd package bg-dexopt-job

echo; echo "== 5/5 Concluído =="
echo "Agora faça manualmente (veja README.md):"
echo "  - Ativar o Modo de alto desempenho (Bateria > Mais configurações)"
echo "  - Desligar a 'Expansão de RAM' em Configurações > Sobre o telefone > RAM"
echo "  - Reiniciar o celular"
read -rp "Reiniciar agora? [s/N] " r; [ "$r" = s ] && adb reboot
