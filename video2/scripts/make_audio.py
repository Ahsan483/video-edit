"""Voice chain + procedural SFX + loudnorm -> work/audio_{name}.wav (48 kHz stereo).  usage: make_audio.py name [t0 t1]"""
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, SRC
import spec, sfx
name = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
EDL = json.load(open(os.path.join(WORK, "edl.json")))
t1 = float(sys.argv[3]) if len(sys.argv) > 3 else EDL["total"]
SR = 48000
segs = EDL["segments"]
# 1) assemble the cut voice (8 ms fades at every cut) and clean it
fc = []; ins = ""
for i, s in enumerate(segs):
    d = s["s1"] - s["s0"]
    fc.append(f"[0:a]pan=mono|c0=0.5*c0+0.5*c1,atrim={s['s0']:.4f}:{s['s1']:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={d-0.008:.4f}:d=0.008[a{i}]")
    ins += f"[a{i}]"
chain = ("highpass=f=75,afftdn=nr=14:nf=-48:tn=1,equalizer=f=280:t=q:w=1.0:g=-2.2,equalizer=f=3200:t=q:w=0.9:g=2.4,"
         "equalizer=f=9000:t=h:w=0.7:g=1.6,acompressor=threshold=-24dB:ratio=2.6:attack=12:release=200:makeup=3,alimiter=limit=0.9")
fc.append(f"{ins}concat=n={len(segs)}:v=0:a=1,{chain}[out]")
voice = os.path.join(WORK, "voice_clean.wav")
if not os.path.exists(voice):
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[out]", "-ar", str(SR), "-ac", "1", voice])
import wave
w = wave.open(voice); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
# 2) SFX bed
rng = np.random.RandomState(7)
bed = np.zeros(len(v) + SR, np.float32)
kinds = {"whoosh": lambda: sfx.whoosh(rng), "whoosh_s": lambda: sfx.whoosh(rng, dur=0.26, f0=700, f1=3200, gain=0.8),
         "click": lambda: sfx.click(rng), "key": lambda: sfx.key(rng), "swish": lambda: sfx.swish(rng), "tick": lambda: sfx.tick(rng)}
for t, kind, db in spec.build(EDL)["sfx"]:
    sfx.place(bed, kinds[kind](), t, db + 14)       # +14: synth peaks are low, see README for levels
mix = v + bed[:len(v)]
# 3) slice (sample) and normalise
a, b = int(t0 * SR), int(min(t1, len(v) / SR) * SR)
mix = mix[a:b]
raw = os.path.join(WORK, f"mix_{name}.wav")
with wave.open(raw, "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
LN = "I=-14:TP=-1.5:LRA=9"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", f"loudnorm={LN}:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
flt = (f"loudnorm={LN}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
       f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aformat=channel_layouts=stereo")
out = os.path.join(WORK, f"audio_{name}.wav")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "pan=stereo|c0=c0|c1=c0," + flt, "-ar", str(SR), out])
print("audio ->", out, "measured input I", j["input_i"], "TP", j["input_tp"])
