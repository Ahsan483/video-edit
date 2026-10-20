"""Voice cleanup + silence-aware assembly + procedural SFX + loudness -> WAV.  usage: make_audio.py --mode sample|final"""
import sys, os, json, argparse, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True); args = ap.parse_args()
SR = 48000
TL = json.load(open(os.path.join(WORK, f"timeline_{args.mode}.json")))
kept = np.array(TL["kept"]); N = TL["frames"]
rng = np.random.default_rng(11)

def run(cmd): subprocess.run(cmd, check=True)

# 1) clean voice (full source, mono)
clean = os.path.join(WORK, "voice_clean.f32")
if not os.path.exists(clean):
    af = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nr=14:nf=-34:tn=1,"
          "equalizer=f=230:t=q:w=1.0:g=-2.5,equalizer=f=3200:t=q:w=0.9:g=2.5,equalizer=f=9500:t=h:w=0.7:g=1.2,"
          "acompressor=threshold=-27dB:ratio=3:attack=15:release=160:makeup=3,alimiter=limit=0.89")
    run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ar", str(SR), "-af", af, "-f", "f32le", clean])
voice_full = np.fromfile(clean, np.float32)

# 2) assemble along the cut map (frame-exact), 6 ms dip at every join
SPF = SR // FPS            # 800 samples per frame
out = np.zeros(N * SPF, np.float32)
i = 0
while i < N:
    j = i
    while j + 1 < N and kept[j + 1] == kept[j] + 1: j += 1
    seg = voice_full[kept[i] * SPF:(kept[j] + 1) * SPF].copy()
    f = int(0.006 * SR)
    if i > 0: seg[:f] *= np.linspace(0, 1, f)
    if j < N - 1: seg[-f:] *= np.linspace(1, 0, f)
    out[i * SPF:i * SPF + len(seg)] = seg
    i = j + 1
voice = out

def lufs(x):
    p = os.path.join(WORK, "_tmp_l.f32"); x.astype(np.float32).tofile(p)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(r.split("Integrated loudness:")[-1].split("I:")[1].split("LUFS")[0])
cur = lufs(voice)
voice *= 10 ** ((-17.0 - cur) / 20)      # voice at -17 LUFS before SFX / final -14 pass
print("voice LUFS", round(cur, 1), "->-17")

# 3) SFX synthesis
def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.clip((f - lo) / (lo * 0.25 + 1), 0, 1) * np.clip((hi - f) / (hi * 0.25 + 1), 0, 1)
    return np.fft.irfft(X * m, len(x))
def env_exp(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def click_sound():
    n = int(0.16 * SR); y = np.zeros(n)
    for off, amp, tau in ((0, 1.0, 0.0011), (int(0.082 * SR), 0.5, 0.0009)):
        m = int(0.02 * SR)
        nz = bp(rng.standard_normal(m), 1800, 6500) * env_exp(m, tau)
        th = np.sin(2 * np.pi * (340 if off == 0 else 420) * np.arange(m) / SR) * env_exp(m, 0.004) * 0.35
        y[off:off + m] += (nz * 1.4 + th) * amp
    return y / np.abs(y).max() * 0.10      # peak ~ -20 dBFS
def key_sound():
    m = int(0.045 * SR)
    nz = bp(rng.standard_normal(m), 1500, 5500) * env_exp(m, 0.0026)
    f0 = rng.uniform(260, 380)
    th = np.sin(2 * np.pi * f0 * np.arange(m) / SR) * env_exp(m, 0.006) * 0.45
    y = nz + th
    return y / np.abs(y).max() * 0.055 * rng.uniform(0.7, 1.0)    # ~ -25 dBFS
def whoosh(dur=0.5, level=0.075):
    n = int(dur * SR); t = np.arange(n) / n
    outs = []
    for _ in range(2):
        z = rng.standard_normal(n)
        lo, hi = bp(z, 350, 1400), bp(z, 1600, 6500)
        e_lo = np.sin(np.pi * np.clip(t / 0.75, 0, 1)) ** 2
        e_hi = np.sin(np.pi * np.clip((t - 0.15) / 0.85, 0, 1)) ** 2
        outs.append(lo * e_lo * 0.8 + hi * e_hi)
    y = np.stack(outs, 1)
    y *= np.hanning(n * 2)[:n][:, None] ** 0.3 if False else 1
    y *= np.minimum(1, np.arange(n)[:, None] / (0.06 * SR))     # soft attack
    y *= np.minimum(1, (n - np.arange(n))[:, None] / (0.25 * SR))
    return y / np.abs(y).max() * level
def swish(): return whoosh(0.28, 0.04)

mix = np.zeros((N * SPF + SR, 2), np.float32)
def put(sig, t, pan=0.0):
    s = int(round(t * SR))
    if s < 0 or s >= len(mix) - 10: return
    if sig.ndim == 1:
        l, r = np.sqrt((1 - pan) / 2) * 1.414, np.sqrt((1 + pan) / 2) * 1.414
        sig = np.stack([sig * l, sig * r], 1)
    e = min(len(sig), len(mix) - s)
    mix[s:s + e] += sig[:e]
cnt = {}
for ev in TL["sfx"]:
    k = ev["kind"]; cnt[k] = cnt.get(k, 0) + 1
    g = ev.get("gain", 1.0)
    if k == "click": put(click_sound() * g, ev["t"], rng.uniform(-0.1, 0.1))
    elif k == "key": put(key_sound() * g, ev["t"], rng.uniform(-0.15, 0.15))
    elif k == "whoosh": put(whoosh(0.5, 0.075) * g, ev["t"])
    elif k == "swish": put(swish() * g, ev["t"])
print("sfx:", cnt)
# keep SFX out of the bass: gentle 140 Hz high-pass on the SFX bus only
sfx_bus = np.stack([bp(mix[:, c], 140, 20000) for c in (0, 1)], 1).astype(np.float32)
final = sfx_bus.copy()
final[:N * SPF, 0] += voice; final[:N * SPF, 1] += voice
final = final[:N * SPF]
# head/tail fade
f = int(0.08 * SR); final[:f] *= np.linspace(0, 1, f)[:, None]
f = int(0.5 * SR); final[-f:] *= np.linspace(1, 0, f)[:, None]
raw = os.path.join(WORK, f"mix_{args.mode}.f32"); final.astype(np.float32).tofile(raw)

# 4) loudness: two-pass loudnorm to -14 LUFS, TP -1.0
def ln(extra):
    return ["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw, "-af", extra]
meas = subprocess.run(ln("loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json") + ["-f", "null", "-"], capture_output=True, text=True).stderr
j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
flt = (f"loudnorm=I=-14:TP=-1.0:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
       f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
wav = os.path.join(WORK, f"audio_{args.mode}.wav")
run(ln(flt)[:-2] + ["-af", flt + ",aresample=48000", "-c:a", "pcm_s16le", wav, "-y"])
print("wrote", wav, "measured input", j["input_i"], "LUFS")
