"""Mux silent video + processed audio (AAC 256k) -> final mp4. usage: mux.py --mode sample|final OUT"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK
mode, out = sys.argv[2], sys.argv[3]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, f"video_{mode}.mp4"), "-i", os.path.join(WORK, f"audio_{mode}.wav"),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
print("wrote", out)
