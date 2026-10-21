"""Render single composited frames (output seconds) to PNG for review. usage: render_stills.py outdir t1 t2 ..."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_video import *
d = sys.argv[1]; os.makedirs(d, exist_ok=True)
ctx = make_ctx(); cap = cv2.VideoCapture(SRC60)
O = spec.build(EDL)["o"]
for a in sys.argv[2:]:
    t = O(float(a[1:])) if a[0] == "s" else float(a)
    cv2.imwrite(os.path.join(d, f"t{t:07.2f}.png"), compose(grab(cap, t), t, ctx))
