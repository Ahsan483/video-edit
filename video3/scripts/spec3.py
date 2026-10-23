"""Typography / zoom / SFX spec for the three shorts. Times in the helper calls are SOURCE seconds; build() maps them to output seconds."""
import bisect, json, os, re
from common import *
from elements3 import *

WORDS = json.load(open(os.path.join(WORK, "words.json"))) if os.path.exists(os.path.join(WORK, "words.json")) else []
# page-change events found by frame differencing (04_events.py); used for sweeps/swishes
NAV = [21.4, 25.8, 49.3, 62.3, 79.3, 85.3, 96.0, 111.6, 126.3, 143.8, 156.0, 160.0, 174.6, 181.1, 256.2, 297.1, 373.6, 376.4]
CLICKS = [21.1, 25.5, 33.8, 62.1, 118.9, 156.6, 162.9, 297.4, 372.9]

def build(idx, edl):
    sh = edl["shorts"][idx - 1]; segs = sh["segments"]; a0, a1 = sh["src"]
    S0 = [s["s0"] for s in segs]
    def o(ts):
        i = max(0, bisect.bisect_right(S0, ts) - 1); s = segs[i]
        if ts <= s["s1"]: return s["o0"] + max(ts - s["s0"], 0)
        return segs[i + 1]["o0"] if i + 1 < len(segs) else s["o0"] + s["s1"] - s["s0"]
    E, K, SFX = [], [], []; TOTAL = sh["total"]
    def ins(a): return a0 - 0.01 <= a <= a1 + 0.01

    # ---- helpers -------------------------------------------------------------------------------------------------
    def behind(lines, a, b, size=150, base=1330, lh=None, right=1048, sfx=True):
        wmax = max(text_width(tx, 800, size, -0.035) for tx in lines)
        if right - wmax < 670: size = int(size * (right - 670) / wmax)        # keep letters clear of the head so they stay legible
        lh = lh or int(size * 1.08)
        for i, tx in enumerate(lines):
            e = Behind(tx, o(a) + i * 0.07, o(b), right=right, base=base + i * lh, size=size, underline=(i == len(lines) - 1))
            E.append(e)
        if sfx: SFX.append((o(a) + 0.02, "whoosh", -21))
    def tag(text, a, b):
        e = SectionTag(text, o(a), o(b)); E.append(e); SFX.append((e.t0 + 0.05, "tick", -23))
    def ring(rect, a, b, label=None, dim=0.0, place="below"): E.append(Ring(rect, o(a), o(b), label, dim, place))
    def stat(text, cap, a, b, **k): E.append(Stat(text, cap, o(a), o(b), **k)); SFX.append((o(a) + 0.02, "tick", -22))
    def zoom(t, cx, cy_abs, z, dur=0.75): K.append((o(t), cx, cy_abs - SCRSRC[1], z, dur))
    def overview(t, dur=0.7): K.append((o(t), (SCRSRC[2] - SCRSRC[0]) / 2, (SCRSRC[3] - SCRSRC[1]) / 2, 1.0, dur))
    def hook(lines, a, b, sub=None, dim=0.72, size=112):
        E.append(Hook(lines, o(a), o(b), size=size, base=640, dim=dim, sub=sub)); SFX.append((o(a) + 0.03, "whoosh", -19))
    W_ = lambda *ws: [(w, 0) for w in ws]
    A_ = lambda *ws: [(w, 1) for w in ws]

    # ---- karaoke captions from the word-level transcript ------------------------------------------------------------
    ws = [w for w in WORDS if a0 - 0.02 <= w[1] < a1]
    chunk = []; chars = 0
    def flush():
        nonlocal chunk, chars
        if not chunk: return
        items = []
        for j, (tx, s, e) in enumerate(chunk):
            nxt = chunk[j + 1][1] if j + 1 < len(chunk) else e
            t0 = o(s); t1 = max(o(min(e, nxt)) , t0 + 0.09)
            items.append((tx.rstrip(",.;:") if not tx.endswith("?") else tx, t0, t1))
        E.append(Caption(items)); chunk = []; chars = 0
    for k, (tx, s, e) in enumerate(ws):
        if chunk and (chars + len(tx) > 28 or len(chunk) >= 5 or s - chunk[-1][2] > 0.30):
            flush()
        chunk.append((tx, s, e)); chars += len(tx) + 1
        if tx.endswith((".", "?", "!")) and len(chunk) >= 2: flush()
    flush()
    # make sure consecutive chunks never overlap on screen
    caps = [e for e in E if e.kind == "caption"]
    for c0, c1 in zip(caps, caps[1:]):
        if c0.t1 > c1.t0: c0.t1 = c1.t0

    # ---- per-short content ---------------------------------------------------------------------------------------
    if idx == 1:
        hook([[("I", 0), ("BUILT", 0)], [("PAYFLOW", 1), ("PRO", 1)]], 0.1, 2.9, sub="A FULL HR + PAYROLL APP")
        tag("PAYFLOW PRO", 3.0, 12.4); tag("DASHBOARD", 12.6, 62.0); tag("EMPLOYEES", 62.4, 93.0); tag("PROFILE & TOOLS", 93.1, 106.6)
        stat("1+ YEAR", "BUILDING IT", 7.2, 12.0)
        behind(["DASH", "BOARD"], 12.7, 17.6, size=150)
        zoom(12.8, 355, 560, 1.5); ring((153, 418, 555, 707), 13.2, 20.5, "LEAVE APPROVALS")
        zoom(20.9, 540, 500, 1.85); ring((428, 362, 652, 635), 21.6, 26.0, "REASON REQUIRED")
        overview(26.3, 0.6); zoom(27.3, 815, 360, 1.6); ring((712, 150, 925, 593), 27.6, 32.8, "NOTIFICATIONS")
        zoom(33.5, 900, 200, 1.9); ring((956, 113, 1034, 143), 33.9, 37.0, "ADD EMPLOYEE", place="below")
        zoom(37.8, 815, 520, 1.45); ring((573, 253, 1057, 830), 38.0, 47.0, "PAYROLL ANALYTICS")
        stat("PKR 1,630,000", "PAYROLL THIS MONTH", 41.8, 47.0, base=1230)
        overview(47.8, 0.7); zoom(52.8, 355, 600, 1.35)
        zoom(61.9, 540, 394, 1.0, 0.6)
        behind(["PEOPLE"], 62.5, 67.5, size=120, base=1340)
        zoom(66.5, 600, 520, 1.25); ring((212, 257, 392, 282), 71.0, 76.5, "SEARCH", place="below")
        overview(77.0, 0.7)
        zoom(79.5, 480, 330, 1.35)
        zoom(88.0, 600, 560, 1.3)
        overview(93.1, 0.8)
        behind(["PROFILE"], 96.2, 102.2, size=100, base=1340)
        zoom(99.0, 900, 330, 1.45); ring((928, 150, 1060, 295), 99.4, 102.5, "PROFILE CARD")
        behind(["TOOLS"], 102.7, 106.6, size=150, base=1340)
        zoom(102.7, 960, 440, 1.6); ring((928, 305, 1060, 590), 103.0, 106.5, "SMALL TOOLS")
    elif idx == 2:
        hook([[("TRACK", 0), ("ATTENDANCE", 1)], [("RUN", 0), ("PAYROLL", 1)]], 106.8, 109.6, sub="PART 2 · PAYFLOW PRO", size=104)
        tag("ATTENDANCE", 109.8, 158.1); tag("PAYROLL", 158.7, 185.2); tag("MESSAGES", 185.4, 243.6)
        behind(["CHECK", "IN"], 118.6, 124.2, size=140, base=1300)
        zoom(118.3, 250, 535, 1.6); ring((162, 515, 340, 555), 118.8, 123.8, "CHECK IN")
        overview(124.3, 0.7)
        behind(["LIVE", "MONITOR"], 124.6, 129.6, size=125, base=1300)
        stat("3", "EMPLOYEES CHECKED IN", 135.0, 142.0, base=1235, size=150)
        behind(["LIVE"], 142.5, 148.3, size=170, base=1360)
        behind(["BREAKS"], 149.0, 154.5, size=105, base=1350)
        zoom(158.8, 600, 380, 1.0, 0.6); behind(["PAY", "ROLL"], 158.9, 163.6, size=150, base=1300)
        zoom(162.7, 920, 330, 1.9); ring((888, 296, 970, 336), 163.0, 168.7, "RUN PAYROLL")
        zoom(169.3, 320, 440, 1.9); ring((230, 402, 404, 487), 169.4, 173.1, "TOTAL PAID")
        behind(["SLIPS"], 173.3, 178.3, size=150, base=1340)
        overview(173.3, 0.7)
        zoom(185.6, 500, 500, 1.15)
        behind(["CHAT"], 185.6, 189.0, size=170, base=1350)
        behind(["REACT"], 195.7, 200.6, size=130, base=1340)
        zoom(220.3, 540, 450, 1.3); behind(["CHANNEL"], 224.2, 228.6, size=100, base=1350)
        zoom(235.2, 540, 500, 1.55); ring((410, 315, 670, 683), 235.4, 239.5, "CREATE A CHANNEL")
        overview(240.0, 0.7)
    else:
        hook([[("EMAIL", 1), ("NOTES", 0)], [("TICKETS", 1), ("& MORE", 0)]], 243.8, 246.6, sub="PART 3 · PAYFLOW PRO", size=104)
        tag("EMAIL", 246.8, 271.0); tag("NOTES", 271.5, 296.6); tag("TICKETS", 296.7, 315.4); tag("AUDIT LOGS", 315.5, 321.5)
        tag("SETTINGS", 321.6, 364.0); tag("NEW ORGANIZATION", 364.2, 384.7); tag("YOUR FEEDBACK", 384.9, 398.0)
        behind(["EMAIL"], 247.4, 252.5, size=140, base=1340)
        behind(["NOTES"], 271.6, 276.4, size=140, base=1340)
        behind(["SHARED"], 286.8, 292.3, size=100, base=1350)
        behind(["TICKET"], 297.0, 301.2, size=125, base=1340)
        zoom(297.6, 960, 205, 1.7); ring((938, 191, 1014, 222), 298.0, 301.2, "NEW TICKET")
        overview(301.4, 0.7)
        behind(["AUDIT", "LOGS"], 315.6, 321.4, size=140, base=1300)
        behind(["THEME"], 321.8, 326.0, size=120, base=1340)
        behind(["PROFILE"], 333.2, 339.0, size=100, base=1340)
        zoom(342.2, 730, 450, 1.4); ring((410, 295, 1040, 615), 345.6, 352.2, "ACTIVE SESSIONS")
        overview(352.6, 0.7)
        behind(["2FA"], 352.9, 355.6, size=185, base=1350)
        behind(["NEW", "ORG"], 372.7, 380.6, size=150, base=1300)
        behind(["LIKE", "FOLLOW"], 385.1, 389.7, size=140, base=1300)
        behind(["FEEDBACK"], 390.0, 395.5, size=88, base=1350)
        E.append(Hook([[("THANK", 0), ("YOU", 1)]], o(396.6), TOTAL + 3, size=130, base=680, dim=0.78, sub="LIKE · COMMENT · FOLLOW")); SFX.append((o(396.7), "whoosh", -22))

    if idx in (1, 2): E.append(Next(f"PART {idx + 1} IN THE NEXT VIDEO", TOTAL - 3.0, TOTAL + 1.0))

    tags = sorted([e for e in E if e.kind == "tag"], key=lambda e: e.t0)
    for a_, b_ in zip(tags, tags[1:]): a_.t1 = min(a_.t1, b_.t0 - 0.30)

    # ---- sweeps / navigation sound ---------------------------------------------------------------------------------
    for tn in NAV:
        if a0 + 0.3 < tn < a1 - 0.3:
            E.append(Sweep(o(tn))); SFX.append((o(tn) - 0.02, "swish", -26))
    for tc in CLICKS:
        if a0 + 0.3 < tc < a1 - 0.3: SFX.append((o(tc), "click", -19))

    # ---- webcam punch-ins on alternate jump cuts ------------------------------------------------------------------
    P = []
    for i, s in enumerate(segs):
        d = s["s1"] - s["s0"]
        if i % 2 == 1 and d > 1.2: P.append((s["o0"], s["o0"] + d, 1.06))
    K.sort()
    return dict(elements=E, zoom=K, punches=P, sfx=SFX, o=o)
