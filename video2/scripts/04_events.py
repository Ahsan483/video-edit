"""Per-frame screen activity on the 60 fps proxy -> work/activity.npz (count of changed px at 1/4 res, centroid)."""
import cv2, numpy as np, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cap = cv2.VideoCapture(os.path.join(ROOT, "work", "src60.mp4"))
prev = None; cnt = []; cx = []; cy = []; cam = []
while True:
    ok, f = cap.read()
    if not ok: break
    g = cv2.resize(cv2.cvtColor(f[:875], cv2.COLOR_BGR2GRAY), (360, 219), interpolation=cv2.INTER_AREA).astype(np.int16)
    if prev is None: prev = g
    d = np.abs(g - prev) > 18; d[185:, :140] = False   # ignore webcam rect
    ys, xs = np.nonzero(d)
    cnt.append(len(xs)); cx.append(xs.mean() * 4 if len(xs) else -1); cy.append(ys.mean() * 4 if len(ys) else -1)
    prev = g
np.savez(os.path.join(ROOT, "work", "activity.npz"), cnt=np.array(cnt), cx=np.array(cx), cy=np.array(cy))
print(len(cnt))
