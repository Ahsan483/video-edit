"""Original voice, whole and uncut: only high-pass, light denoise, gentle EQ + compression, loudnorm -14 LUFS -> work/audio.wav"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, SRC
raw = os.path.join(WORK, "voice.wav")
chain = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=70,afftdn=nr=8:nf=-52:tn=1,equalizer=f=250:t=q:w=1.0:g=-1.5,equalizer=f=3000:t=q:w=0.9:g=1.8,"
         "equalizer=f=8500:t=h:w=0.7:g=1.0,acompressor=threshold=-24dB:ratio=2.2:attack=15:release=220:makeup=2,alimiter=limit=0.92")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-af", chain, "-ar", "48000", "-ac", "1", raw])
LN = "I=-14.2:TP=-1.5:LRA=9"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", f"loudnorm={LN}:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
flt = f"loudnorm={LN}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true"
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "pan=stereo|c0=c0|c1=c0," + flt, "-ar", "48000", os.path.join(WORK, "audio.wav")])
print("audio ok, input I", j["input_i"], "TP", j["input_tp"])
