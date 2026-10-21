"""Cut list: start at first speech, tighten pauses > KEEP*2+0.2 s, end after sign-off. -> work/edl.json"""
import json, os
WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work")
START, END = 30.05, 463.0
KEEP, MINCUT = 0.10, 0.34
sil = json.load(open(os.path.join(WORK, "pauses.json")))["silences"]
cuts = [(a + KEEP, b - KEEP) for a, b in sil if START < a and b < END and b - a >= MINCUT]
segs = []; cur = START
for a, b in cuts:
    a = round(a * 60) / 60; b = round(b * 60) / 60
    if a > cur: segs.append([cur, a])
    cur = b
segs.append([cur, END])
o = 0.0; out = []
for a, b in segs:
    out.append({"s0": a, "s1": b, "o0": round(o, 5)}); o += b - a
json.dump({"segments": out, "total": round(o, 5), "cuts": [(round(a, 2), round(b, 2)) for a, b in cuts]}, open(os.path.join(WORK, "edl.json"), "w"), indent=1)
print(len(out), "segments, total", round(o, 1), "s; removed", round(END - START - o, 1), "s")
