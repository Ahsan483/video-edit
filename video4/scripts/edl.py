"""Cut list from word timings. Speech is kept; short pauses are tightened; longer silent stretches (spraying / applying) are kept
but sped up so the hero action stays in the film without dead air.  -> work/edl.json"""
import json, os
WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work")
tr = json.load(open(os.path.join(WORK, "tr_en.json")))
words = [(w["s"], w["e"]) for s in tr for w in s["words"]]
END = 95.95
snap = lambda x: round(x * 60) / 60
# speech runs: merge words separated by < 0.55 s
runs = []
for s, e in words:
    if runs and s - runs[-1][1] < 0.55: runs[-1][1] = e
    else: runs.append([s, e])
segs = []   # (s0, s1, speed)
cur = 0.0
PAD = 0.12
for i, (s, e) in enumerate(runs):
    s0 = max(cur, s - PAD); s1 = min(e + PAD, END)
    if s0 > cur + 0.01:                       # gap before this speech run
        gap = s0 - cur
        if gap >= 1.5: segs.append((cur, s0, min(2.0, max(1.5, gap / 3.2))))      # silent action: sped up
        # shorter gaps are simply dropped (jump cut)
    segs.append((s0, s1, 1.0)); cur = s1
if END - cur > 1.5: segs.append((cur, END, 1.0))
else: segs[-1] = (segs[-1][0], END, 1.0)
# also tighten VAD-detected pauses (> 0.45 s) inside normal-speed segments
sil = json.load(open(os.path.join(WORK, "pauses.json")))["silences"]
fin = []
for s0, s1, sp in segs:
    if sp != 1.0: fin.append((s0, s1, sp)); continue
    cur2 = s0
    for a, b in sil:
        if b <= s0 or a >= s1 or b - a < 0.45: continue
        ca, cb = max(a, s0) + 0.11, min(b, s1) - 0.11
        if cb - ca < 0.1: continue
        if ca > cur2: fin.append((cur2, ca, 1.0))
        cur2 = cb
    if s1 > cur2: fin.append((cur2, s1, 1.0))
segs = fin
segs = [x for x in segs if x[2] > 1.0 or x[1] - x[0] >= 0.25]
out = []; o = 0.0
for s0, s1, sp in segs:
    s0, s1 = snap(s0), snap(s1)
    if s1 - s0 < 0.05: continue
    out.append({"s0": s0, "s1": s1, "speed": round(sp, 3), "o0": round(o, 5)}); o += (s1 - s0) / sp
json.dump({"segments": out, "total": round(o, 5)}, open(os.path.join(WORK, "edl.json"), "w"), indent=1)
print(len(out), "segments, output", round(o, 1), "s from", END, "s;", sum(1 for x in out if x["speed"] > 1), "sped-up")
for x in out: print(x)
