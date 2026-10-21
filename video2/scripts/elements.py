"""Kinetic typography elements. Every element draws itself on a BGR frame at output time t (seconds)."""
from common import *

IN_DUR, OUT_DUR = 0.55, 0.28

def _adv(txt, weight, size, track=0.0, mono=False):
    return text_width(txt, weight, size, track, mono)

class Behind:
    """Giant keyword that sits behind the creator (person matte is re-composited over it by the renderer).
    Per-letter mask-rise reveal, then an amber underline sweep."""
    kind = "behind"
    def __init__(self, text, t0, t1, x=250, base=1015, size=225, weight=800, color=OFFWHITE, underline=True,
                 accent_from=None, track=-0.035):
        self.text, self.t0, self.t1, self.x, self.base, self.size = text, t0, t1, x, base, size
        self.weight, self.color, self.underline, self.accent_from, self.track = weight, color, underline, accent_from, track
        self.xs = []; cx = float(x)
        for i, ch in enumerate(text):
            self.xs.append(cx)
            adv = _adv(text[i:i + 2], weight, size, track) - _adv(text[i + 1:i + 2], weight, size, track) if i + 1 < len(text) else _adv(ch, weight, size, track)
            cx += adv
        self.x1 = cx
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_DUR
    def draw(self, fr, t):
        lt = t - self.t0; n = len(self.text)
        out = clamp01((t - self.t1) / OUT_DUR)
        win = (0, int(self.base - self.size * 0.80), W, int(self.base + self.size * 0.26))
        for i, ch in enumerate(self.text):
            if ch == " ": continue
            p = ease_out_expo((lt - i * 0.045) / 0.62)
            if out > 0:
                q = ease_in_cubic((out - (n - 1 - i) * 0.03) / 0.7)
            else: q = 0
            col = AMBER if (self.accent_from is not None and i >= self.accent_from) else self.color
            spr, ox, oy = sprite(ch, self.weight, self.size, col, 0, shadow=0.35)
            dy = int((1 - p) * self.size * 0.95 + q * self.size * 0.35)
            blit(fr, spr, int(self.xs[i]) - ox, self.base - oy + dy, a=min(1, p * 2.2) * (1 - q), clip=win)
        if self.underline:
            u = ease_in_out_cubic((lt - 0.55) / 0.55); ua = 1 - ease_in_cubic((out - 0.1) / 0.6)
            fill_rect(fr, self.x + 4, self.base + 22, self.x + 4 + (self.x1 - self.x - 8) * u, self.base + 28, AMBER, ua)

class Band:
    """Word-by-word staggered statement in the empty band right of the webcam. lines = [[(word, accent), ...], ...]"""
    kind = "band"
    def __init__(self, lines, t0, t1, x=610, base=945, size=62, line_h=None, weight=700, align="left", right=1395,
                 colors=None, sub=False, left=None):
        self.lines, self.t0, self.t1, self.x, self.base, self.size = lines, t0, t1, x, base, size
        self.lh = line_h or int(size * 1.2); self.weight, self.align, self.right = weight, align, right
        self.sub = sub; self.left = BAND[0] + 4 if left is None else left
        self.space = int(size * 0.26)
        self.layout = []
        for li, line in enumerate(lines):
            ws = [_adv(w.lstrip("\b"), weight, size, -0.015) for w, _ in line]
            gaps = [0 if w.startswith("\b") else self.space for w, _ in line]; gaps[0] = 0
            tot = sum(ws) + sum(gaps)
            x0 = x if align == "left" else (right - tot if align == "right" else x + (right - x - tot) / 2)
            xs = []; cx = x0
            for w, g in zip(ws, gaps): cx += g; xs.append(cx); cx += w
            self.layout.append((xs, tot))
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_DUR
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / OUT_DUR)
        a_out = 1 - ease_in_cubic(out); dx = -int(ease_in_cubic(out) * 22)
        k = 0
        for li, line in enumerate(self.lines):
            base = self.base + li * self.lh
            win = (self.left, int(base - self.size * 0.98), W, int(base + self.size * 0.26))
            for wi, (w, acc) in enumerate(line):
                p = ease_out_expo((lt - li * 0.16 - wi * 0.075) / 0.6)
                col = AMBER if acc else (SOFT if self.sub else OFFWHITE)
                spr, ox, oy = sprite(w.lstrip("\b"), self.weight, self.size, col, -0.015, shadow=0)
                dy = int((1 - p) * self.size * 1.05)
                blit(fr, spr, int(self.layout[li][0][wi]) - ox + dx, base - oy + dy, a=min(1, p * 2) * a_out, clip=win)
                k += 1

class Label:
    """Small elegant uppercase feature label: amber square + tracked text, wipe-in, thin amber underline sweep."""
    kind = "label"
    def __init__(self, text, t0, t1, x, y, size=21, color=OFFWHITE, align="left", line=True):
        self.text, self.t0, self.t1, self.x, self.y, self.size, self.color, self.align, self.line = text, t0, t1, x, y, size, color, align, line
        self.track = 0.16
        self.w = _adv(text, 600, size, self.track)
        self.x0 = x if align == "left" else x - (self.w + size * 1.4)
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_DUR
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / OUT_DUR)
        p = ease_out_expo(lt / 0.55); a = 1 - ease_in_cubic(out)
        s = self.size; x0 = int(self.x0)
        sq = int(s * 0.46); pp = ease_out_expo(lt / 0.3)
        fill_rect(fr, x0, self.y - s * 0.62 - sq * pp / 2 + 3, x0 + sq, self.y - s * 0.62 + sq * pp / 2 + 3, AMBER, a)
        spr, ox, oy = sprite(self.text, 600, s, self.color, self.track, shadow=0.0)
        tx = x0 + int(s * 1.1)
        blit(fr, spr, tx - ox - int((1 - p) * 14), self.y - oy, a=a * clamp01(p * 1.6),
             clip=(tx - 2, 0, tx + int(self.w * p) + 6, H))
        if self.line:
            u = ease_in_out_cubic((lt - 0.2) / 0.6)
            fill_rect(fr, tx, self.y + 9, tx + self.w * u, self.y + 11, AMBER, 0.85 * a)

class Typed:
    """Typing animation with amber caret (monospace)."""
    kind = "typed"
    def __init__(self, text, t0, t1, x=610, base=1000, size=44, prefix="$", cps=17.0):
        self.text, self.t0, self.t1, self.x, self.base, self.size, self.prefix, self.cps = text, t0, t1, x, base, size, prefix, cps
        # deterministic key times (slightly irregular)
        self.keys = []; t = 0.25; rnd = np.random.RandomState(abs(hash(text)) % 2 ** 31)
        for ch in text:
            self.keys.append(t); t += (1.0 / cps) * (0.7 + 0.7 * rnd.rand()) * (1.8 if ch == " " else 1.0)
        self.end_type = self.t0 + t
    def key_times(self): return [self.t0 + k for k in self.keys]
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_DUR
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / OUT_DUR); a = 1 - ease_in_cubic(out)
        n = sum(1 for k in self.keys if k <= lt)
        pre = self.prefix + " "
        pw = _adv(pre, 500, self.size, 0, True)
        sp, ox, oy = sprite(pre, 500, self.size, AMBER, 0, mono=True)
        blit(fr, sp, self.x - ox, self.base - oy, a=a * clamp01(lt / 0.2))
        if n:
            s2, ox2, oy2 = sprite(self.text[:n], 500, self.size, OFFWHITE, 0, mono=True)
            blit(fr, s2, int(self.x + pw) - ox2, self.base - oy2, a=a)
        cw = _adv(self.text[:n], 500, self.size, 0, True)
        blink = (int(t * 2.2) % 2 == 0) or n < len(self.text) and lt - (self.keys[n - 1] if n else 0) < 0.25
        if blink and lt > 0.1:
            fill_rect(fr, self.x + pw + cw + 3, self.base - self.size * 0.78, self.x + pw + cw + 3 + self.size * 0.5, self.base + 4, AMBER, 0.9 * a)

class Card:
    """Centered title/closing card: dims the whole frame, staggered line reveal."""
    kind = "card"
    def __init__(self, lines, t0, t1, size=84, base=None, dim=0.80, weight=800, sub=None):
        self.lines, self.t0, self.t1, self.size, self.dim, self.weight, self.sub = lines, t0, t1, size, dim, weight, sub
        self.base = base or (H // 2 - 10)
    def active(self, t): return self.t0 <= t <= self.t1 + 0.5
    def amount(self, t):
        return ease_out_cubic((t - self.t0) / 0.5) * (1 - ease_in_cubic((t - self.t1) / 0.5))
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.5); am = self.amount(t)
        if am > 0:
            fr[:] = (fr.astype(np.float32) * (1 - self.dim * am) + np.array(NAVY[::-1], np.float32) * self.dim * am).astype(np.uint8)
        nl = len(self.lines)
        for li, line in enumerate(self.lines):
            base = int(self.base + (li - (nl - 1) / 2) * self.size * 1.22)
            ws = [_adv(w, self.weight, self.size, -0.025) for w, _ in line]
            sp_ = int(self.size * 0.26); tot = sum(ws) + sp_ * (len(ws) - 1); cx = (W - tot) / 2
            win = (0, int(base - self.size * 0.95), W, int(base + self.size * 0.28))
            for wi, (w, acc) in enumerate(line):
                p = ease_out_expo((lt - 0.1 - li * 0.18 - wi * 0.09) / 0.7)
                spr, ox, oy = sprite(w, self.weight, self.size, AMBER if acc else OFFWHITE, -0.025, shadow=0)
                blit(fr, spr, int(cx) - ox, base - oy + int((1 - p) * self.size * 1.1), a=min(1, p * 2) * (1 - ease_in_cubic(out)), clip=win)
                cx += ws[wi] + sp_
        if self.sub:
            p = ease_out_expo((lt - 0.7) / 0.6)
            spr, ox, oy = sprite(self.sub, 600, 24, SOFT, 0.18)
            w_ = _adv(self.sub, 600, 24, 0.18)
            blit(fr, spr, int((W - w_) / 2) - ox, int(self.base + nl * self.size * 0.75 + 30) - oy, a=p * (1 - ease_in_cubic(out)))
