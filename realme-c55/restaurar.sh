#!/usr/bin/env bash
# Desfaz o otimizar.sh: reinstala os apps removidos e volta animações para 1x.
set -u
cd "$(dirname "$0")"
adb get-state >/dev/null 2>&1 || { echo "Nenhum celular conectado."; exit 1; }
sed 's/^\s*#\s*//' pacotes.txt | awk '{print $1}' | grep -E '^[a-z]+\.[a-zA-Z.]+$' | while read -r p; do
  out=$(adb shell cmd package install-existing "$p" 2>&1 | tr -d '\r')
  echo "  $p -> $out"
done
for k in window_animation_scale transition_animation_scale animator_duration_scale; do
  adb shell settings put global "$k" 1.0
done
echo "Restaurado."
