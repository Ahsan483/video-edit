"""Voice chain for the review: assemble the cut (with the sped-up action segments), gentle denoise/EQ/compression, loudnorm -14 LUFS -> work/audio.wav"""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, SRC
segs = json.load(open(os.path.join(WORK, "edl.json")))["segments"]
fc = []; ins = ""
for i, s in enumerate(segs):
    d = (s["s1"] - s["s0"]) / s["speed"]
    f = f"[0:a]atrim={s['s0']:.4f}:{s['s1']:.4f},asetpts=PTS-STARTPTS"
    if s["speed"] > 1.0:
        f += f",atempo={s['speed']:.3f},volume=0.7"
    f += f",afade=t=in:d=0.008,afade=t=out:st={max(d - 0.008, 0):.4f}:d=0.008[a{i}]"
    fc.append(f); ins += f"[a{i}]"
chain = ("highpass=f=70,afftdn=nr=10:nf=-50:tn=1,equalizer=f=250:t=q:w=1.0:g=-1.8,equalizer=f=3000:t=q:w=0.9:g=2.2,"
         "equalizer=f=8500:t=h:w=0.7:g=1.4,acompressor=threshold=-22dB:ratio=2.6:attack=10:release=180:makeup=3,alimiter=limit=0.92")
fc.append(f"{ins}concat=n={len(segs)}:v=0:a=1,{chain}[out]")
raw = os.path.join(WORK, "voice.wav")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[out]", "-ar", "48000", "-ac", "1", raw])
LN = "I=-14.2:TP=-1.5:LRA=9"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", f"loudnorm={LN}:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
flt = (f"loudnorm={LN}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
out = os.path.join(WORK, "audio.wav")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "pan=stereo|c0=c0|c1=c0," + flt, "-ar", "48000", out])
print("audio ->", out, "input I", j["input_i"], "TP", j["input_tp"])
