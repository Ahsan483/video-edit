#!/bin/sh
# full pipeline: 120 fps picture -> mux with the cleaned voice (H.264 CRF 15, AAC 192k, yuv420p, +faststart)
cd "$(dirname "$0")/.."
rm -rf work/chunks
python3 -I scripts/render.py --out work/silent.mp4 -j 4 --crf 15 || exit 1
ffmpeg -v error -y -i work/silent.mp4 -i work/audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart output/perfume_review_120fps.mp4 || exit 1
echo ALLDONE
