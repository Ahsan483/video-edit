"""Typography / zoom spec for the long Glass UI edit (the whole video, voice untouched: source time == output time)."""
import json, os, re
from common import *
from elements5 import *

TOTAL = 398.2
SECTIONS = [("PAYFLOW PRO", 0.0), ("DASHBOARD", 12.6), ("EMPLOYEES", 62.4), ("PROFILE & TOOLS", 93.1), ("ATTENDANCE", 106.8), ("PAYROLL", 158.7), ("MESSAGES", 185.4),
            ("EMAIL", 243.7), ("NOTES", 271.5), ("TICKETS", 296.7), ("AUDIT LOGS", 315.5), ("SETTINGS", 321.6), ("NEW ORGANIZATION", 364.2), ("THANK YOU", 384.9)]

def build():
    words = json.load(open(os.path.join(ROOT, "data", "words.json")))
    E, K = [], []
    E.append(ChipBase(TOTAL))
    for i, (txt, t0) in enumerate(SECTIONS):
        t1 = SECTIONS[i + 1][1] - 0.05 if i + 1 < len(SECTIONS) else TOTAL
        E.append(SectionChip(txt, t0, t1))
    # captions: whole sentences, nothing dropped; chunk at sentence ends / pauses / 9 words
    chunk = []; chars = 0
    def flush():
        nonlocal chunk, chars
        if not chunk: return
        items = []
        for j, (tx, s, e) in enumerate(chunk):
            nxt = chunk[j + 1][1] if j + 1 < len(chunk) else e
            items.append((tx.rstrip(",;:") if not tx.endswith("?") else tx, s, max(min(e, nxt), s + 0.09)))
        E.append(Caption(items)); chunk = []; chars = 0
    for tx, s, e in words:
        if chunk and (chars + len(tx) > 64 or len(chunk) >= 10 or s - chunk[-1][2] > 0.6): flush()
        chunk.append((tx, s, e)); chars += len(tx) + 1
        if tx.endswith((".", "?", "!")) and len(chunk) >= 3: flush()
    flush()
    caps = [e for e in E if e.kind == "caption"]
    for a, b in zip(caps, caps[1:]):
        if a.t1 > b.t0: a.t1 = b.t0
    def zoom(t, cx, cy_abs, z, dur=0.75): K.append((t, cx, cy_abs - SCRSRC[1], z, dur))
    def ov(t, dur=0.7): K.append((t, (SCRSRC[2] - SCRSRC[0]) / 2, (SCRSRC[3] - SCRSRC[1]) / 2, 1.0, dur))
    def ring(rect, a, b, label, **k): E.append(Ring(rect, a, b, label, **k))
    E.append(Card(["PayFlow Pro"], "COMPLETE WALKTHROUGH", 0.25, 3.1))
    E.append(Stat("1+ YEAR", "BUILDING IT", 7.2, 12.0))
    zoom(12.8, 355, 560, 1.5); ring((153, 418, 555, 707), 13.2, 20.5, "LEAVE APPROVALS")
    zoom(20.9, 540, 500, 1.85); ring((428, 362, 652, 635), 21.6, 26.0, "REASON REQUIRED")
    ov(26.3, 0.6); zoom(27.3, 815, 360, 1.6); ring((712, 150, 925, 593), 27.6, 32.8, "NOTIFICATIONS")
    zoom(33.5, 900, 200, 1.9); ring((956, 113, 1034, 143), 33.9, 37.0, "ADD EMPLOYEE")
    zoom(37.8, 815, 520, 1.45); ring((573, 253, 1057, 830), 38.0, 47.0, "PAYROLL ANALYTICS")
    E.append(Stat("PKR 1,630,000", "PAYROLL THIS MONTH", 41.8, 47.0))
    ov(47.8, 0.7); zoom(52.8, 355, 600, 1.35); ov(61.9, 0.6)
    zoom(66.5, 600, 520, 1.25); ring((212, 257, 392, 282), 71.0, 76.5, "SEARCH"); ov(77.0)
    zoom(79.5, 480, 330, 1.35); zoom(88.0, 600, 560, 1.3); ov(93.1, 0.8)
    zoom(99.0, 900, 330, 1.45); ring((928, 150, 1060, 295), 99.4, 102.5, "PROFILE CARD")
    zoom(102.7, 960, 440, 1.6); ring((928, 305, 1060, 590), 103.0, 106.5, "SMALL TOOLS"); ov(106.8, 0.8)
    zoom(118.3, 250, 535, 1.6); ring((162, 515, 340, 555), 118.8, 123.8, "CHECK IN"); ov(124.3)
    E.append(Stat("3", "EMPLOYEES CHECKED IN", 135.0, 142.0))
    ov(158.8, 0.6); zoom(162.7, 920, 330, 1.9); ring((888, 296, 970, 336), 163.0, 168.7, "RUN PAYROLL")
    zoom(169.3, 320, 440, 1.9); ring((230, 402, 404, 487), 169.4, 173.1, "TOTAL PAID"); ov(173.3)
    zoom(185.6, 500, 500, 1.15); zoom(220.3, 540, 450, 1.3)
    zoom(235.2, 540, 500, 1.55); ring((410, 315, 670, 683), 235.4, 239.5, "CREATE A CHANNEL"); ov(240.0)
    zoom(297.6, 960, 205, 1.7); ring((938, 191, 1014, 222), 298.0, 301.2, "NEW TICKET"); ov(301.4)
    zoom(342.2, 730, 450, 1.4); ring((410, 295, 1040, 615), 345.6, 352.2, "ACTIVE SESSIONS"); ov(352.6)
    E.append(Card(["Thank you"], "LIKE  ·  COMMENT  ·  FOLLOW", 395.6, TOTAL + 2))
    K.sort()
    return dict(elements=E, zoom=K)
