"""stills3.py SHORT outdir t... (prefix s = source seconds, otherwise output seconds) -> composited PNGs"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render3 import *
idx = int(sys.argv[1]); d = sys.argv[2]; os.makedirs(d, exist_ok=True)
sh = Short(idx); ctx = make_ctx(sh); O = spec3.build(idx, EDLALL)["o"]; cap = cv2.VideoCapture(SRC)
for a in sys.argv[3:]:
    t = O(float(a[1:])) if a[0] == "s" else float(a)
    cv2.imwrite(os.path.join(d, f"p{idx}_{a}.png"), compose(grab(cap, sh, t), t, sh, ctx))
