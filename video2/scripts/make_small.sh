#!/bin/sh
# 2-pass x264 re-encode of the full-quality final so it fits GitHub's 100 MB file limit (target ~89 MB)
cd "$(dirname "$0")/.." && P=work/x264pass
ffmpeg -v error -y -i output/final.mp4 -an -c:v libx264 -preset slow -b:v 1500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -pass 1 -passlogfile $P -f null /dev/null
ffmpeg -v error -y -i output/final.mp4 -c:v libx264 -preset slow -b:v 1500k -maxrate 3000k -bufsize 6000k -pix_fmt yuv420p -pass 2 -passlogfile $P -c:a copy -movflags +faststart output/final_smaller.mp4
