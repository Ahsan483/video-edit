"""build.py [stills|render] [ids...] -> out/NN_name.mp4 (5 s, 1080x1920, 120 fps) or work/stills"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import t_a, t_b, t_c
ALL = {1: t_a.T01, 2: t_a.T02, 3: t_a.T03, 4: t_a.T04, 5: t_b.T05, 6: t_b.T06, 7: t_b.T07, 8: t_c.T08, 9: t_c.T09, 10: t_c.T10}
mode = sys.argv[1]; ids = [int(x) for x in sys.argv[2:]] or list(ALL)
for i in ids:
    tp = ALL[i]()
    if mode == "stills":
        for ts in (0.9, 2.0, 3.6):
            cv2.imwrite(os.path.join(ROOT, "work", f"s{i:02d}_{ts}.png"), tp.frame(ts, int(ts * FPS))); 
        print("stills", i, flush=True)
    else:
        render(tp, os.path.join(ROOT, "out", tp.name + ".mp4")); print("rendered", tp.name, flush=True)
