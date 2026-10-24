#!/bin/sh
# one long Glass UI edit: 120 fps picture -> mux with the untouched original voice
cd "$(dirname "$0")/.."
rm -rf work/chunks
python3 -I scripts/render5.py --out work/silent.mp4 -j 4 --crf 16 || exit 1
ffmpeg -v error -y -i work/silent.mp4 -i work/audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 224k -movflags +faststart output/payflow_pro_glass_120fps.mp4 || exit 1
echo ALLDONE
