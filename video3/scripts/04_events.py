"""Per-frame screen activity (changed px count at 1/4 res + centroid in source coords) -> work/activity.npz"""
import cv2, numpy as np, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cap = cv2.VideoCapture(os.path.join(ROOT, "source.mp4")); prev = None; cnt = []; cx = []; cy = []
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.resize(cv2.cvtColor(f[105:893], cv2.COLOR_BGR2GRAY), (270, 197), interpolation=cv2.INTER_AREA).astype(np.int16)
    if prev is None: prev = g
    d = np.abs(g - prev) > 18; ys, xs = np.nonzero(d)
    cnt.append(len(xs)); cx.append(xs.mean() * 4 if len(xs) else -1); cy.append(ys.mean() * 4 + 105 if len(xs) else -1); prev = g
np.savez(os.path.join(ROOT, "work", "activity.npz"), cnt=np.array(cnt), cx=np.array(cx), cy=np.array(cy)); print(len(cnt))
