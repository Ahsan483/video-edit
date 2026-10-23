#!/bin/sh
# render all three shorts: audio -> picture (120 fps) -> mux (H.264 CRF 17, AAC 192k, yuv420p, +faststart)
cd "$(dirname "$0")/.."
for n in 1 2 3; do
  python3 -I scripts/make_audio3.py $n || exit 1
  rm -rf work/chunks$n
  python3 -I scripts/render3.py --short $n --out work/s${n}_silent.mp4 -j 4 --crf 17 || exit 1
  ffmpeg -v error -y -i work/s${n}_silent.mp4 -i work/audio_s${n}.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart output/short_${n}.mp4 || exit 1
  echo "DONE short $n"
done
echo ALLDONE
