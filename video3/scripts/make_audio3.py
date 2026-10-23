"""Voice chain + procedural SFX + loudnorm per short -> work/audio_sN.wav.  usage: make_audio3.py N"""
import sys, os, json, subprocess, wave, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WORK, SRC
import spec3, sfx
N = int(sys.argv[1]); EDLALL = json.load(open(os.path.join(WORK, "edl.json"))); segs = EDLALL["shorts"][N - 1]["segments"]
SR = 48000
fc = []; ins = ""
for i, s in enumerate(segs):
    d = s["s1"] - s["s0"]
    fc.append(f"[0:a]pan=mono|c0=0.5*c0+0.5*c1,atrim={s['s0']:.4f}:{s['s1']:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,afade=t=out:st={d-0.006:.4f}:d=0.006[a{i}]"); ins += f"[a{i}]"
chain = ("highpass=f=75,afftdn=nr=14:nf=-48:tn=1,equalizer=f=280:t=q:w=1.0:g=-2.2,equalizer=f=3200:t=q:w=0.9:g=2.4,"
         "equalizer=f=9000:t=h:w=0.7:g=1.6,acompressor=threshold=-24dB:ratio=2.8:attack=10:release=180:makeup=3,alimiter=limit=0.9")
fc.append(f"{ins}concat=n={len(segs)}:v=0:a=1,{chain}[out]")
voice = os.path.join(WORK, f"voice_s{N}.wav")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", ";".join(fc), "-map", "[out]", "-ar", str(SR), "-ac", "1", voice])
w = wave.open(voice); v = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
rng = np.random.RandomState(11 + N); bed = np.zeros(len(v) + SR, np.float32)
kinds = {"whoosh": lambda: sfx.whoosh(rng), "whoosh_s": lambda: sfx.whoosh(rng, dur=0.26, f0=700, f1=3200, gain=0.8), "click": lambda: sfx.click(rng),
         "key": lambda: sfx.key(rng), "swish": lambda: sfx.swish(rng), "tick": lambda: sfx.tick(rng)}
for t, kind, db in spec3.build(N, EDLALL)["sfx"]: sfx.place(bed, kinds[kind](), t, db + 14)
mix = v + bed[:len(v)]
raw = os.path.join(WORK, f"mix_s{N}.wav")
with wave.open(raw, "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
LN = "I=-14.6:TP=-1.5:LRA=9"
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", f"loudnorm={LN}:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
flt = (f"loudnorm={LN}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aformat=channel_layouts=stereo")
out = os.path.join(WORK, f"audio_s{N}.wav")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "pan=stereo|c0=c0|c1=c0," + flt, "-ar", str(SR), out])
print("audio ->", out, "dur", round(len(v) / SR, 1))
