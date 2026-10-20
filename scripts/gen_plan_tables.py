"""Print the timestamped plan tables (markdown) from spec.py so EDIT_PLAN.md always matches what is rendered."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spec
def ts(t): return f"{int(t // 60)}:{t % 60:05.2f}"
rows = []
for t0, t1, text, acc in spec.BEHIND: rows.append((t0, t1, "behind head (matte)", text))
for t0, t1, text, acc in spec.TOP: rows.append((t0, t1, "top band", text))
for t0, t1, text, acc in spec.BOTTOM: rows.append((t0, t1, "bottom band", text))
for t0, t1, side, lines in spec.SIDE: rows.append((t0, t1, "left of face" if side == "l" else "right of face", " / ".join(l[1] for l in lines)))
for t0, t1, text in spec.TYPED: rows.append((t0, t1, "typing animation", text))
for t0, t1, text in spec.EYEBROW: rows.append((t0, t1, "label", text))
print("| source time | layout | text |\n|---|---|---|")
for t0, t1, kind, text in sorted(rows): print(f"| {ts(t0)} – {ts(t1)} | {kind} | {text} |")
print("\n| source time | UI zoom (centre x,y in screen band · scale) |\n|---|---|")
for t0, t1, cx, cy, s in spec.ZOOMS: print(f"| {ts(t0)} – {ts(t1)} | ({cx}, {cy}) · ×{s} |")
print("\nClick SFX (source time): " + ", ".join(ts(c) for c in spec.CLICKS))
