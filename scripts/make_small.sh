#!/bin/sh
# 2-pass x264 re-encode of output/final.mp4 to fit under GitHub's 100 MB file limit (target ~89 MB). Same 1080x1920, 60 fps; audio copied.
set -e
cd "$(dirname "$0")/.."
LOG=/tmp/claude-0/work/x264pass
ffmpeg -v error -y -i output/final.mp4 -an -c:v libx264 -preset slow -b:v 2550k -maxrate 6000k -bufsize 9000k -pass 1 -passlogfile $LOG -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -f null /dev/null
ffmpeg -v error -y -i output/final.mp4 -i output/final.mp4 -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 2550k -maxrate 6000k -bufsize 9000k -pass 2 -passlogfile $LOG -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:a copy -movflags +faststart output/final_1080p_smaller.mp4
ls -la output/final_1080p_smaller.mp4
