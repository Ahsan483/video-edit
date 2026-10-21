"""Person mattes (every 3rd 60fps source frame) for the windows where a keyword sits behind the creator.
usage: make_mattes.py [out_t0 out_t1]   (optionally restrict to an output-time range)"""
import sys, os, json, cv2, numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec
OUTD = os.path.join(WORK, "mattes"); os.makedirs(OUTD, exist_ok=True)
EDL = json.load(open(os.path.join(WORK, "edl.json")))

def src_windows(lo=None, hi=None):
    ws = []
    for e in spec.build(EDL)["elements"]:
        if e.kind != "behind": continue
        a, b = e.t0 - 0.5, e.t1 + 0.9
        if lo is not None: a, b = max(a, lo), min(b, hi)
        if b <= a: continue
        # out-time -> source ranges (a window can span cuts)
        for s in EDL["segments"]:
            o0, o1 = s["o0"], s["o0"] + s["s1"] - s["s0"]
            lo_, hi_ = max(a, o0), min(b, o1)
            if hi_ > lo_: ws.append((s["s0"] + lo_ - o0, s["s0"] + hi_ - o0))
    return ws

def work(win):
    from matte import matte
    a, b = win
    f0, f1 = int(a * FPS) // 3 * 3, int(b * FPS) // 3 * 3 + 3
    cap = cv2.VideoCapture(SRC60); cap.set(cv2.CAP_PROP_POS_FRAMES, f0); n = 0
    for f in range(f0, f1 + 1):
        ok, fr = cap.read()
        if not ok: break
        if f % 3: continue
        p = os.path.join(OUTD, f"{f:06d}.png")
        if os.path.exists(p): continue
        cv2.imwrite(p, (matte(fr) * 255).astype(np.uint8)); n += 1
    return n

if __name__ == "__main__":
    lo, hi = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (None, None)
    ws = src_windows(lo, hi)
    with Pool(4) as p: print(sum(p.map(work, ws, chunksize=1)), "mattes written from", len(ws), "windows")
