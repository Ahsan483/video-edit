"""Voice-activity pauses from 16k mono wav -> work/pauses.json  [(start,end)] of silence >= MINLEN."""
import sys, json, wave, numpy as np
from scipy.signal import butter, sosfilt
wav = sys.argv[1]; out = sys.argv[2]
w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
sos = butter(4, [100, 3800], 'bandpass', fs=16000, output='sos'); y = sosfilt(sos, x)
hop = 160  # 10 ms
n = len(y) // hop
rms = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
db = 20 * np.log10(rms)
floor = np.percentile(db, 8); peak = np.percentile(db, 95)
thr = floor + 0.30 * (peak - floor)
print("floor", floor, "peak", peak, "thr", thr)
sp = db > thr
# smooth: close gaps <80ms, drop blips <60ms
import itertools
runs = []; i = 0
while i < n:
    j = i
    while j < n and sp[j] == sp[i]: j += 1
    runs.append([sp[i], i, j]); i = j
for r in runs:
    if not r[0] and r[2] - r[1] < 8: r[0] = True
for r in runs:
    if r[0] and r[2] - r[1] < 6: r[0] = False
sil = []; cur = None
for v, a, b in runs:
    if not v:
        if sil and abs(sil[-1][1] - a) < 1: sil[-1][1] = b
        else: sil.append([a, b])
    else:
        pass
sil = [(a / 100, b / 100) for a, b in sil]
json.dump({"silences": sil, "db": [round(float(v), 1) for v in db[::5]], "thr": float(thr)}, open(out, "w"))
print(len(sil), "silences; >0.3s:", sum(1 for a, b in sil if b - a > .3), "total", round(sum(b - a for a, b in sil if b - a > .3), 1))
