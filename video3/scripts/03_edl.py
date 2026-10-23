"""Cut list for the three shorts: topic boundaries from the transcript, all non-speaking gaps removed. -> work/edl.json, work/words.json"""
import json, os, re
WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work")
SHORTS = [("Dashboard & Employees", 0.0, 106.7), ("Attendance, Payroll & Messages", 106.7, 243.65), ("Notes, Tickets, Settings & Register", 243.7, 398.0)]
KEEP, MINCUT = 0.055, 0.30
sil = json.load(open(os.path.join(WORK, "pauses.json")))["silences"]
tr = json.load(open(os.path.join(WORK, "transcript_en.json")))
# also treat gaps between spoken words (>0.40 s) as non-speaking clips
_w = [(w["s"], w["e"]) for sg in tr for w in sg["words"]]
sil = sorted(sil + [[_w[i][1] + 0.02, _w[i + 1][0] - 0.02] for i in range(len(_w) - 1) if _w[i + 1][0] - _w[i][1] > 0.40])
m_ = []
for a, b in sil:
    if m_ and a <= m_[-1][1]: m_[-1][1] = max(m_[-1][1], b)
    else: m_.append([a, b])
sil = m_
snap = lambda x: round(x * 60) / 60
out = []
for name, a0, a1 in SHORTS:
    segs = []; cur = a0
    for a, b in sil:
        if b <= a0 or a >= a1 or b - a < MINCUT: continue
        ca, cb = max(a, a0) + (KEEP if a > a0 else 0.0), min(b, a1) - (KEEP if b < a1 else 0.0)
        if a <= a0: ca = a0; cb = b - KEEP          # leading silence: start just before first speech
        if b >= a1: ca = a + KEEP; cb = a1          # trailing silence
        if cb - ca < 0.08: continue
        ca, cb = snap(ca), snap(cb)
        if ca > cur: segs.append([cur, ca])
        cur = cb
    if a1 > cur: segs.append([cur, snap(a1)])
    o = 0.0; ss = []
    for s0, s1 in segs:
        if s1 - s0 < 0.05: continue
        ss.append({"s0": s0, "s1": s1, "o0": round(o, 5)}); o += s1 - s0
    out.append({"name": name, "src": [a0, a1], "segments": ss, "total": round(o, 5)})
    print(name, len(ss), "segments", round(o, 1), "s (raw", round(a1 - a0, 1), ")")
json.dump({"shorts": out}, open(os.path.join(WORK, "edl.json"), "w"), indent=1)
# word list for captions (source time) with light text fixes
FIX = {"payflow": "PayFlow", "purity": "priority", "detection": "deduction", "detections": "deductions"}
OVR = {76.8: "I search for an employee", 79.3: "and I can see their profile", 256.2: "so you can message on this domain"}
words = []
for s in tr:
    if round(s["start"], 1) in OVR:
        ws = OVR[round(s["start"], 1)].split(); n = len(ws); d = (s["end"] - s["start"]) / n
        words += [[w, s["start"] + i * d, s["start"] + (i + 1) * d] for i, w in enumerate(ws)]
        continue
    for w in s["words"]:
        t = w["w"].strip()
        if not t: continue
        core = re.sub(r"[^\w']", "", t).lower()
        if core in FIX: t = t.lower().replace(core, FIX[core]) if False else re.sub(core, FIX[core], t, flags=re.I)
        words.append([t, w["s"], w["e"]])
json.dump(words, open(os.path.join(WORK, "words.json"), "w"))
print(len(words), "words")
