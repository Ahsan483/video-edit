"""Typography / zoom / SFX spec. All times below are SOURCE seconds; build() maps them to output seconds via the EDL."""
import bisect, json, os
from common import *
from elements import *

def build(edl):
    segs = edl["segments"]
    S0 = [s["s0"] for s in segs]
    def o(ts):
        i = max(0, bisect.bisect_right(S0, ts) - 1); s = segs[i]
        if ts <= s["s1"]: return s["o0"] + max(ts - s["s0"], 0)
        return segs[i + 1]["o0"] if i + 1 < len(segs) else s["o0"] + s["s1"] - s["s0"]
    E, Z, SFX = [], [], []
    TOTAL = edl["total"]

    def behind(text, a, b, size=None, right=None, base=1020, x=400, **k):
        n = len(text)
        size = size or int(min(200, (1400 - x) / (n * 0.70)))
        e = Behind(text, o(a), o(b), x=x, base=base, size=size, **k)
        if right is not None:
            e = Behind(text, o(a), o(b), x=right - text_width(text, 800, size, -0.035), base=base, size=size, **k)
        E.append(e); SFX.append((e.t0 + 0.02, "whoosh", -21))
    def band(lines, a, b, size=58, align="left", sfx=True, x=610, left=None, right=1395, sub=False):
        n = len(lines); lh = int(size * 1.16); cap = size * 0.72
        base = int(977 + cap / 2 - (n - 1) * lh / 2)
        e = Band([[(w, ac) for w, ac in ln] for ln in lines], o(a), o(b), x=x, base=base, size=size, line_h=lh, align=align,
                 left=left, right=right, sub=sub)
        E.append(e)
        if sfx: SFX.append((e.t0 + 0.03, "whoosh_s", -25))
    def label(text, a, b, x=610, y=966, **k):
        e = Label(text, o(a), o(b), x, y, **k); E.append(e); SFX.append((e.t0 + 0.05, "tick", -22))
    def W(*ws): return [(w, 0) for w in ws]
    def A(*ws): return [(w, 1) for w in ws]

    # ---------------- intro: full-width webcam (30.75 - 45.0) ----------------
    behind("JOB", 31.0, 35.0, size=150, base=300, right=1395, underline=False)
    behind("HUNTER", 31.15, 35.0, size=150, base=470, right=1395)
    band([[("You", 0), ("asked", 0), ("for", 0), ("a", 0), ("guide", 1)]], 31.4, 34.9, size=66, align="center", x=0, left=0, right=1440)
    label("SETUP GUIDE", 37.0, 42.7, x=70, y=330)
    band([[("How", 0), ("to", 0), ("run", 1), ("it", 0), ("and", 0), ("use", 1), ("it", 0)]], 37.2, 42.7, size=66, align="center", x=0, left=0, right=1440)
    t = Typed("git clone Ahsan483/job-hunter", o(43.0), o(50.6), x=610, base=1000, size=38)
    E.append(t)
    for kt in t.key_times(): SFX.append((kt, "key", -27))

    # ---------------- setup ----------------
    band([[("config", 1), ("\b.example.json", 0)], [("profile", 1), ("\b.example.json", 0)]], 51.3, 57.0, size=50)
    band([[("Create", 0), ("profile.json", 1)], [("and", 0), ("config.json", 1)]], 57.5, 63.0, size=54)
    behind("CONFIG", 63.4, 70.4)
    band([[("Your", 0), ("Gmail", 1), ("address", 0)]], 71.4, 74.6, size=62)
    band([[("Emails", 0), ("the", 0), ("recruiter", 1)], [("directly", 0)]], 75.2, 82.0, size=58)
    band([[("Written", 0), ("by", 0), ("AI", 1)], [("Professional", 0), ("drafts", 0)]], 82.6, 94.0, size=56)
    behind("PASSWORD", 100.3, 107.4)
    behind("GEMINI", 108.4, 115.3)
    band([[("3", 1), ("things", 0), ("to", 0), ("add", 0)]], 115.8, 121.8, size=70)
    label("README  /  GMAIL SETUP", 122.6, 129.8)
    band([[("Enable", 0), ("two-step", 1)], [("verification", 0)]], 130.4, 135.5, size=56)
    band([[("Create", 0), ("an", 0), ("app", 1)], [("password", 1)]], 135.9, 141.7, size=56)
    band([[("Create", 0), ("a", 0), ("free", 0)], [("Gemini", 1), ("API", 1), ("key", 1)]], 142.0, 147.0, size=56)
    band([[("Paste", 0), ("it", 0), ("in", 0)], [("config.json", 1)]], 147.5, 153.0, size=56)
    t2 = Typed("python -I gui.py", o(155.4), o(159.8), x=610, base=1000, size=44, cps=11)
    E.append(t2)
    for kt in t2.key_times(): SFX.append((kt, "key", -27))
    label("THE APP OPENS", 160.4, 165.3)
    behind("UPLOAD", 166.0, 171.6)
    band([[("Gemini", 1), ("updates", 0)], [("profile.json", 1)]], 172.0, 177.0, size=58)
    band([[("Experience,", 0), ("jobs,", 0)], [("projects", 1)]], 177.3, 183.0, size=58)
    band([[("A", 0), ("rough", 0), ("draft", 0)], [("prepared", 1)]], 183.4, 187.3, size=58)
    behind("1 CLICK", 188.0, 197.9)
    band([[("Tailored", 1), ("to", 0), ("each", 0), ("job", 0)]], 198.1, 201.5, size=58)
    band([[("Powered", 0), ("by", 0), ("Gemini", 1)]], 202.6, 210.0, size=62)
    band([[("Free", 1), ("model.", 0)], [("Custom", 0), ("prompt.", 0)]], 210.7, 215.7, size=58)
    label("BUILDING PROFILE.JSON", 216.4, 227.4)
    band([[("Done.", 1)]], 235.6, 238.8, size=70)
    band([[("Old", 0), ("profile", 0), ("backed", 0), ("up", 1)]], 239.4, 245.0, size=58)
    band([[("5", 1), ("roles", 0), ("·", 0), ("25", 1), ("bullets", 0)], [("18", 1), ("projects", 0), ("·", 0), ("66", 1), ("skills", 0)]], 245.4, 253.0, size=56)
    label("PROFILE.JSON  UPDATED", 255.9, 261.4)
    behind("FILTER", 268.3, 271.8)
    behind("C++", 272.2, 277.7)
    band([[("Worldwide", 1), ("only", 0)]], 278.6, 283.1, size=62)
    band([[("Pakistan", 1), ("region", 0)]], 283.3, 285.5, size=62)
    band([[("Max", 0), ("age", 0), ("10", 1), ("days", 0)]], 285.9, 289.6, size=62)
    label("SEARCHING", 290.4, 297.2)
    band([[("Search", 0), ("done", 1)]], 298.1, 303.3, size=62)
    behind("7 JOBS", 303.6, 310.8)
    band([[("Remote", 0), ("C", 1), ("/", 0), ("C++", 1)], [("open", 0), ("worldwide", 0)]], 310.9, 315.8, size=56)
    band([[("No", 0), ("email", 0), ("posted", 0)], [("Apply", 0), ("on", 0), ("site", 1)]], 316.0, 322.3, size=56)
    band([[("Full-time", 0), ("·", 0), ("Senior", 1)]], 322.6, 326.7, size=60)
    band([[("Read", 0), ("the", 0), ("overview", 1)]], 326.9, 332.5, size=60)
    band([[("Ready", 0), ("to", 0), ("apply", 1)]], 333.0, 338.4, size=62)
    band([[("Make", 0), ("CV", 1), ("+", 0)], [("Cover", 0), ("Letter", 1)]], 338.7, 341.6, size=56)
    behind("TAILORED", 341.9, 349.7)
    band([[("It", 0), ("worked.", 1)]], 349.8, 352.3, size=66)
    band([[("CV", 1), ("+", 0), ("cover", 0), ("letter", 0)], [("saved", 1)]], 352.6, 359.5, size=56)
    label("TAILORED FOLDER", 362.9, 368.2)
    label("OPEN IN FILE EXPLORER", 369.4, 375.0)
    band([[("Written", 0), ("very", 0), ("well", 1)]], 408.9, 414.0, size=62)
    band([[("Cover", 0), ("letter", 0)], [("for", 0), ("C++", 1)]], 414.7, 420.0, size=58)
    band([[("More", 0), ("features", 1)]], 424.0, 428.0, size=66)
    band([[("Click", 0), ("a", 0), ("job", 1)], [("Apply", 0), ("for", 0), ("this", 0), ("job", 1)]], 430.8, 440.0, size=54)
    band([[("See", 0), ("the", 0), ("job", 0), ("details", 1)], [("and", 0), ("how", 0), ("to", 0), ("apply", 0)]], 441.1, 447.0, size=54)
    band([[("The", 0), ("repo", 0), ("is", 0), ("public", 1)], [("github.com/Ahsan483/job-hunter", 0)]], 447.5, 453.6, size=44, sub=False)
    band([[("Like", 1), ("·", 0), ("Comment", 1), ("·", 0), ("Follow", 1)]], 454.3, 460.2, size=60, align="center", x=610, right=1395)
    E.append(Card([[("Job", 0), ("Hunter", 1)]], o(460.6), TOTAL + 5, size=110, dim=0.86, sub="GITHUB.COM/AHSAN483/JOB-HUNTER"))
    SFX.append((o(460.7), "whoosh", -22))

    # ---------------- sound cues tied to real on-screen events (found by frame differencing, see 04_events.py) ----------------
    for ts in (168.2, 269.4, 278.62, 290.03, 339.43, 436.72):
        SFX.append((o(ts) - 0.01, "click", -19))
    for ts in (160.18, 296.97, 361.03, 414.95, 436.77, 441.87):
        SFX.append((o(ts) - 0.02, "swish", -27))

    # ---------------- feature-focused screen zooms (screen rows only) ----------------
    def zoom(a, b, cx, cy, z, tin=0.7, tout=0.6): Z.append((o(a), o(b), cx, cy, z, tin, tout))
    zoom(245.3, 252.8, 300, 570, 1.85)
    zoom(268.2, 289.8, 520, 190, 1.5, 0.9, 0.7)
    zoom(294.9, 297.0, 480, 600, 1.55, 0.6, 0.5)
    zoom(338.5, 341.8, 880, 225, 1.9, 0.6, 0.5)

    # ---------------- webcam punch-ins on jump cuts (hard cut, subtle) ----------------
    P = []
    for i, s in enumerate(segs):
        dur = s["s1"] - s["s0"]
        if i % 2 == 1 and dur > 1.5: P.append((s["o0"], s["o0"] + dur, 1.05))
    E.sort(key=lambda e: e.t0)
    return dict(elements=E, zooms=Z, punches=P, sfx=SFX, o=o)
