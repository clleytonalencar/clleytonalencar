#!/bin/bash
# Builds 10 s vertical motions from finished status images (e.g. exported from Canva).
# 0-7 s: slow zoom on the image (date visible from frame 1); 7-10 s: closing calendar card.
# Usage: motion_canva.sh <images_dir> <endcard.png> <out_dir> <prefix>
set -e
IMG_DIR=$1; END=$2; OUT=$3; PREFIX=$4
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
i=0
for img in "$IMG_DIR"/*.jpg; do
  i=$((i+1))
  name=$(basename "$img" .jpg)
  # each video gets its own soundtrack variation
  TRS=(0 2 -2 3 0 2 -2 3 0)
  PROGS=("A,F,C,G,A" "C,G,A,F,C" "F,G,A,A,F" "A,G,F,G,A" "C,F,G,A,C" "A,F,C,G,A" "C,G,A,F,C" "F,G,A,A,F" "A,G,F,G,A")
  FLAT=1 TR=${TRS[$(( (i-1) % 9 ))]} PROG=${PROGS[$(( (i-1) % 9 ))]} SEED=$((60+i)) python3 "$HERE/trilha.py" "$OUT/_raw.wav" >/dev/null
  # even loudness: compress + level, then two-pass linear loudnorm to -14 LUFS (no pumping, no swells)
  ffmpeg -y -loglevel error -i "$OUT/_raw.wav" -af "acompressor=threshold=-26dB:ratio=8:attack=3:release=80:makeup=6,dynaudnorm=f=100:g=9:p=0.9,alimiter=limit=0.7:level=false" "$OUT/_comp.wav"
  M=$(ffmpeg -hide_banner -i "$OUT/_comp.wav" -af loudnorm=I=-14:TP=-2:LRA=4:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
  g(){ echo "$M" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
  ffmpeg -y -loglevel error -i "$OUT/_comp.wav" -af "loudnorm=I=-14:TP=-2:LRA=4:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" "$OUT/_trilha.wav"
  ffmpeg -y -loglevel error \
    -loop 1 -t 7.5 -i "$img" \
    -loop 1 -t 3 -i "$END" \
    -i "$OUT/_trilha.wav" \
    -filter_complex "\
[0:v]scale=2160:3840,zoompan=z='min(1+0.0004*on,1.09)':x='iw/2-(iw/zoom/2)':y='ih*0.42-(ih/zoom*0.42)':d=225:s=1080x1920:fps=30,setsar=1,format=yuv420p[a];\
[1:v]scale=2160:3840,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=90:s=1080x1920:fps=30,setsar=1,format=yuv420p[b];\
[a][b]xfade=transition=slideup:duration=0.5:offset=7[v]" \
    -map "[v]" -map 2:a -t 10 -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -movflags +faststart \
    "$OUT/${PREFIX}_${name}.mp4"
  echo "ok $name"
done
rm -f "$OUT/_trilha.wav" "$OUT/_raw.wav" "$OUT/_comp.wav"
