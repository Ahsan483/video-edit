"""Sample face bbox every 2s and detect UI change events (clicks/selection changes)."""
import cv2, numpy as np, json, subprocess, sys
sys.path.insert(0, '/home/user/video-edit/scripts')
from matte import matte
SRC = '/tmp/claude-0/work/src/source.mov'
cap = cv2.VideoCapture(SRC)
boxes = []
for t in range(0, 269, 2):
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read()
    if not ok: break
    m = matte(f, 1) > 0.5
    ys, xs = np.where(m)
    top = np.where(m.any(1))[0]
    # head width at 15%..35% of height from top
    y0 = top.min()
    row = lambda y: np.where(m[y])[0]
    r = row(min(y0 + 150, m.shape[0]-1))
    boxes.append(dict(t=t, top=int(y0) + 838, xmin=int(xs.min()), xmax=int(xs.max()), head_l=int(r.min()) if len(r) else 0, head_r=int(r.max()) if len(r) else 0))
json.dump(boxes, open('/tmp/claude-0/work/face_boxes.json', 'w'))
print('boxes done')
