"""Typography + camera spec (source seconds -> output seconds through the EDL)."""
import bisect, json, os
from common import *
from elements import *

def build(edl):
    segs = edl["segments"]; S0 = [s["s0"] for s in segs]; TOTAL = edl["total"]
    def o(ts):
        i = max(0, bisect.bisect_right(S0, ts) - 1); s = segs[i]
        if ts <= s["s1"]: return s["o0"] + max(ts - s["s0"], 0) / s["speed"]
        return segs[i + 1]["o0"] if i + 1 < len(segs) else s["o0"] + (s["s1"] - s["s0"]) / s["speed"]
    E = []
    E.append(TopLabel("PRISTINE AROMA  ·  FRAGRANCE REVIEW", o(0.5), TOTAL - 0.3))
    E.append(Placard("TESTER REVIEW", "Two New Scents", "KING KHAN  ·  OPPENHEIMER", o(0.6), o(7.4)))
    E.append(Placard("N° 01", "King Khan", "FRESH  ·  CITRUSY  ·  OFFICE WEAR", o(26.0), o(45.6)))
    E.append(Placard("N° 02", "Oppenheimer", "BR540-STYLE  ·  HEAVY  ·  WINTER", o(46.0), o(69.0)))
    E.append(Placard("THE VERDICT", "Best for Winter", "BUY IT BLIND", o(84.4), o(93.4)))
    # camera close-ups: (t0, t1, cx, cy, zoom) in normalised footage coordinates
    K = [(o(36.4), o(40.6), 0.74, 0.72, 1.5), (o(56.4), o(62.6), 0.70, 0.60, 1.45), (o(62.8), o(66.4), 0.68, 0.56, 1.38)]
    return dict(elements=E, keys=K, segs=segs, o=o)
