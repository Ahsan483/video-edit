"""Person mattes (every 3rd 60 fps source frame, native webcam-crop res) for windows where a keyword sits behind the creator."""
import sys, os, json, cv2, numpy as np
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec3
OUTD = os.path.join(WORK, "mattes3"); os.makedirs(OUTD, exist_ok=True)
EDLALL = json.load(open(os.path.join(WORK, "edl.json")))

def src_windows():
    ws = []
    for si, sh in enumerate(EDLALL["shorts"], 1):
        for e in spec3.build(si, EDLALL)["elements"]:
            if e.kind != "behind": continue
            a, b = e.t0 - 0.3, e.t1 + 0.8
            for s in sh["segments"]:
                o0, o1 = s["o0"], s["o0"] + s["s1"] - s["s0"]
                lo, hi = max(a, o0), min(b, o1)
                if hi > lo: ws.append((s["s0"] + lo - o0, s["s0"] + hi - o0))
    # merge overlaps
    ws.sort(); m = []
    for a, b in ws:
        if m and a <= m[-1][1] + 0.1: m[-1] = (m[-1][0], max(m[-1][1], b))
        else: m.append((a, b))
    return m

def work(win):
    from matte import matte
    a, b = win; f0, f1 = int(a * SRC_FPS) // 3 * 3, int(b * SRC_FPS) // 3 * 3 + 6
    cap = cv2.VideoCapture(SRC); cap.set(cv2.CAP_PROP_POS_FRAMES, f0); n = 0
    for f in range(f0, f1 + 1):
        ok, fr = cap.read()
        if not ok: break
        if f % 3: continue
        p = os.path.join(OUTD, f"{f:06d}.png")
        if os.path.exists(p): continue
        cv2.imwrite(p, (matte(fr, 1, CAMSRC) * 255).astype(np.uint8)); n += 1
    return n

if __name__ == "__main__":
    ws = src_windows()
    print(len(ws), "windows", round(sum(b - a for a, b in ws), 1), "s")
    with Pool(4) as p: print(sum(p.map(work, ws, chunksize=1)), "mattes written")
