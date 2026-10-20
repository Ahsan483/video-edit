"""Pre-compute person mattes (every 3rd source frame, half-res PNG) only for the windows where text sits behind the head.
usage: make_mattes.py [t_lo t_hi ...]  (optional list of source-time ranges to restrict to; default: all BEHIND windows)"""
import sys, os, cv2, numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec
OUT = os.path.join(WORK, "mattes"); os.makedirs(OUT, exist_ok=True)
PAD = 0.35

def windows(ranges=None):
    ws = []
    for t0, t1, *_ in spec.BEHIND:
        a, b = t0 - PAD, t1 + PAD
        if ranges:
            for lo, hi in ranges:
                a2, b2 = max(a, lo), min(b, hi)
                if b2 > a2: ws.append((a2, b2))
        else:
            ws.append((a, b))
    return ws

def work(win):
    from matte import matte
    a, b = win
    f0, f1 = int(a * FPS) // 3 * 3, int(b * FPS) // 3 * 3 + 3
    cap = cv2.VideoCapture(SRC); cap.set(cv2.CAP_PROP_POS_FRAMES, f0)
    n = 0
    for f in range(f0, f1 + 1):
        ok, fr = cap.read()
        if not ok: break
        if f % 3: continue
        p = os.path.join(OUT, f"{f:06d}.png")
        if os.path.exists(p): continue
        m = matte(fr, 1)
        small = cv2.resize(m, (540, 395), interpolation=cv2.INTER_AREA)
        cv2.imwrite(p, (small * 255).astype(np.uint8)); n += 1
    return n

if __name__ == "__main__":
    args = [float(x) for x in sys.argv[1:]]
    ranges = list(zip(args[0::2], args[1::2])) or None
    ws = windows(ranges)
    with Pool(4) as p:
        print(sum(p.map(work, ws, chunksize=1)), "mattes written")
