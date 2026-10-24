"""Glass UI elements (BGR frames, t in output seconds)."""
from common import *

def _adv(txt, weight, size, track=0.0, mono=False): return text_width(txt, weight, size, track, mono)
_masks = {}
def rr(w, h, r):
    k = (w, h, r)
    if k not in _masks:
        m = rrect(h, w, r); e = np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1); _masks[k] = (m[..., None], e[..., None])
    return _masks[k]
def rrect(h, w, r):
    m = np.zeros((h * 3, w * 3), np.uint8); R = int(r * 3)
    cv2.rectangle(m, (R, 0), (w * 3 - R, h * 3), 255, -1); cv2.rectangle(m, (0, R), (w * 3, h * 3 - R), 255, -1)
    for cx, cy in ((R, R), (w * 3 - R, R), (R, h * 3 - R), (w * 3 - R, h * 3 - R)): cv2.circle(m, (cx, cy), R, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

def glass(fr, x, y, w, h, r, p=1.0, tint=0.14, dark=0.22):
    """frosted glass rectangle composited onto the (smooth) gradient backdrop."""
    x, y = int(x), int(y)
    if p <= 0.01 or w < 4 or h < 4: return
    m, e = rr(w, h, r); x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    m = m[y0 - y:y1 - y, x0 - x:x1 - x] * p; e = e[y0 - y:y1 - y, x0 - x:x1 - x] * p
    reg = fr[y0:y1, x0:x1].astype(np.float32)
    grad = np.linspace(1.0, 0.45, y1 - y0, dtype=np.float32)[:, None, None]
    reg = reg * (1 - m * dark) + 255 * tint * grad * m + 255 * 0.30 * e * grad
    fr[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)

class Caption:
    """Full-sentence karaoke caption inside the glass pill: every word of the chunk is shown; the spoken word lights up."""
    kind = "caption"
    SIZE = 46
    def __init__(self, words):
        self.words = words; self.t0 = words[0][1] - 0.05; self.t1 = words[-1][2] + 0.10
        zone = CAP_PILL; maxw = zone[2] - zone[0] - 90; size = self.SIZE; sp = int(size * 0.30); lines = [[]]; w = 0
        for i, (tx, a, b) in enumerate(words):
            ww = _adv(tx, 700, size, -0.01)
            if lines[-1] and w + sp + ww > maxw: lines.append([]); w = 0
            lines[-1].append(i); w += (sp if len(lines[-1]) > 1 else 0) + ww
        self.pos = {}; lh = int(size * 1.28); zc = (zone[1] + zone[3]) / 2; base0 = zc + size * 0.34 - (len(lines) - 1) * lh / 2
        for li, ln in enumerate(lines):
            tot = sum(_adv(words[i][0], 700, size, -0.01) for i in ln) + sp * (len(ln) - 1); x = (zone[0] + zone[2]) / 2 - tot / 2
            for i in ln: self.pos[i] = (x, base0 + li * lh); x += _adv(words[i][0], 700, size, -0.01) + sp
    def active(self, t): return self.t0 <= t <= self.t1
    def draw(self, fr, t):
        a_in = ease_out_cubic((t - self.t0) / 0.14); size = self.SIZE
        for i, (tx, a, b) in enumerate(self.words):
            x, base = self.pos[i]
            if t < a: col, al = OFFWHITE, 0.50
            elif t <= b: col, al = AMBER, 1.0
            else: col, al = OFFWHITE, 1.0
            spr, ox, oy = sprite(tx, 700, size, col, -0.01)
            pop = 1 + 0.07 * math.sin(math.pi * clamp01((t - a) / 0.22)) if a <= t <= b + 0.1 else 1.0
            if pop > 1.004:
                s2 = cv2.resize(spr, None, fx=pop, fy=pop, interpolation=cv2.INTER_LINEAR)
                cx_ = x + _adv(tx, 700, size, -0.01) / 2; cy_ = base - 0.35 * size
                blit(fr, s2, int(cx_ - spr.shape[1] / 2 * pop), int(cy_ - (oy - 0.35 * size) * pop), a=al * a_in)
            else:
                blit(fr, spr, int(x) - ox, int(base) - oy, a=al * a_in)

class SectionChip:
    """Top-left glass chip with the current section; text slides up on change."""
    kind = "chip"
    def __init__(self, text, t0, t1): self.text, self.t0, self.t1 = text, t0, t1
    def active(self, t): return self.t0 - 0.05 <= t <= self.t1 + 0.35
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.3); p = ease_out_expo(lt / 0.55); a = (1 - ease_in_cubic(out)) * min(1, p * 2)
        spr, ox, oy = sprite(self.text, 700, 30, OFFWHITE, 0.10); w_ = spr.shape[1] - 2 * ox
        win = (44, 62, 44 + int(w_) + 60, 124)
        blit(fr, spr, 74 - ox, 106 - oy + int((1 - p) * 34) - int(ease_in_cubic(out) * 34), a=a, clip=win)

class ChipBase:
    """Persistent chips (brand + timer) drawn each frame."""
    kind = "chrome"
    def __init__(self, total): self.total = total; self.t0 = 0; self.t1 = 1e9
    def active(self, t): return True
    def draw(self, fr, t):
        txt = "PAYFLOW PRO"; w_ = int(_adv(txt, 700, 26, 0.16)) + 56; x = W - 44 - w_
        glass(fr, x, 62, w_, 62, 31, 1.0, tint=0.12)
        spr, ox, oy = sprite(txt, 700, 26, OFFWHITE, 0.16); blit(fr, spr, x + 28 - ox, 104 - oy, a=0.95)
        # progress bar under the screen panel
        glass(fr, 40, 924, 1000, 10, 5, 1.0, tint=0.10, dark=0.1)
        pw = int(1000 * clamp01(t / self.total))
        if pw > 8:
            m, e = rr(pw, 10, 5); reg = fr[924:934, 40:40 + pw].astype(np.float32); c = np.array(AMBER[::-1], np.float32)
            reg[:] = reg * (1 - m * 0.95) + c * m * 0.95; fr[924:934, 40:40 + pw] = reg.astype(np.uint8)
        # footer chip with elapsed / total
        mm, ss = int(t) // 60, int(t) % 60; tm, ts_ = int(self.total) // 60, int(self.total) % 60
        txt = f"{mm}:{ss:02d} / {tm}:{ts_:02d}"; w2 = int(_adv(txt, 600, 26, 0.12)) + 56; x2 = (W - w2) // 2
        glass(fr, x2, 1806, w2, 58, 29, 1.0, tint=0.10)
        spr, ox, oy = sprite(txt, 600, 26, SOFT, 0.12); blit(fr, spr, x2 + 28 - ox, 1844 - oy, a=0.9)

class Ring:
    """UI callout: ice-blue outline around a source-screen rect + glass label chip (tracks the zoom)."""
    kind = "ring"
    def __init__(self, rect, t0, t1, label=None, dim=0.0, place="below"):
        self.rect, self.t0, self.t1, self.label, self.dim, self.place = rect, t0, t1, label, dim, place
    def active(self, t): return self.t0 <= t <= self.t1 + 0.3
    def draw(self, fr, t, ctx=None):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.25); p = ease_out_expo(lt / 0.5); a = 1 - ease_in_cubic(out)
        x0, y0 = ctx["map"](self.rect[0], self.rect[1]); x1, y1 = ctx["map"](self.rect[2], self.rect[3])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hw, hh = (x1 - x0) / 2 * p + 8, (y1 - y0) / 2 * p + 6
        cl_, ct_, cr_, cb_ = SCR_IN[0] + 4, SCR_IN[1] + 4, SCR_IN[2] - 4, SCR_IN[3] - 4
        x0i, y0i, x1i, y1i = int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh); pad = 8; w_, h_ = x1i - x0i + 2 * pad, y1i - y0i + 2 * pad
        if w_ > 4 and h_ > 4:
            m = np.zeros((h_ * 2, w_ * 2), np.uint8); cv2.rectangle(m, (pad * 2, pad * 2), (w_ * 2 - pad * 2, h_ * 2 - pad * 2), 255, 5, cv2.LINE_AA)
            m = cv2.resize(m, (w_, h_), interpolation=cv2.INTER_AREA); sp = np.zeros((h_, w_, 4), np.uint8); sp[..., 0], sp[..., 1], sp[..., 2] = AMBER; sp[..., 3] = m
            blit(fr, sp, x0i - pad, y0i - pad, a=a, clip=(cl_, ct_, cr_, cb_))
        if self.label:
            tw = _adv(self.label, 800, 24, 0.12); cw_, ch_ = int(tw + 40), 46
            bx = int(min(max(cx - cw_ / 2, cl_ + 4), cr_ - cw_ - 4)); by = int(y1i + 12 if self.place == "below" else y0i - 12 - ch_); by = min(max(by, ct_ + 4), cb_ - ch_ - 4)
            pp = ease_out_expo((lt - 0.12) / 0.45)
            glass(fr, bx, by + int((1 - pp) * 12), cw_, ch_, 23, pp * a, tint=0.30, dark=0.35)
            sp2, ox, oy = sprite(self.label, 800, 24, OFFWHITE, 0.12); blit(fr, sp2, bx + 20 - ox, by + 31 - oy + int((1 - pp) * 12), a=a * pp)

class Stat:
    """Glass stat card in the free area of the webcam panel (never over the face)."""
    kind = "stat"
    def __init__(self, text, caption, t0, t1): self.text, self.caption, self.t0, self.t1 = text, caption, t0, t1; self.m = __import__("re").match(r"^(\D*)([\d,\.]+)(\D*)$", text)
    def active(self, t): return self.t0 <= t <= self.t1 + 0.35
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.3); p = ease_out_expo(lt / 0.6); a = (1 - ease_in_cubic(out)) * min(1, p * 1.5)
        txt = self.text
        if self.m:
            pre, num, suf = self.m.groups(); target = float(num.replace(",", "")); v = target * ease_out_cubic(lt / 0.9); txt = pre + "{:,.0f}".format(v) + suf
        sz = 70 if len(self.text) < 7 else 46
        wcard = 380; x = 1040 - wcard - 10; y = 1176 + int((1 - p) * 30)
        glass(fr, x, y, wcard, 150, 32, a, tint=0.16, dark=0.55)
        spr, ox, oy = sprite(txt, 800, sz, OFFWHITE, -0.02); w_ = spr.shape[1] - 2 * ox
        blit(fr, spr, int(x + wcard / 2 - w_ / 2) - ox, y + 82 - oy + 0, a=a)
        s2, o2x, o2y = sprite(self.caption, 700, 20, AMBER, 0.14); w2 = s2.shape[1] - 2 * o2x
        blit(fr, s2, int(x + wcard / 2 - w2 / 2) - o2x, y + 128 - o2y, a=a)

class Card:
    """Centred glass title/closing card over the screen panel."""
    kind = "card"
    def __init__(self, title, sub, t0, t1, y=420): self.title, self.sub, self.t0, self.t1, self.y = title, sub, t0, t1, y
    def active(self, t): return self.t0 <= t <= self.t1 + 0.5
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.45); p = ease_out_expo(lt / 0.7); a = (1 - ease_in_cubic(out)) * min(1, p * 1.5)
        w_, h_ = 880, 360; x = (W - w_) // 2; y = int(self.y + (1 - p) * 70 - ease_in_cubic(out) * 40)
        glass(fr, x, y, w_, h_, 56, a, tint=0.22, dark=0.45)
        win = (x + 20, y + 60, x + w_ - 20, y + h_ - 40)
        for i, line in enumerate(self.title):
            s, ox, oy = sprite(line, 800, 104, OFFWHITE, -0.03); pp = ease_out_expo((lt - 0.12 - i * 0.12) / 0.7)
            blit(fr, s, int(W / 2 - (s.shape[1] - 2 * ox) / 2) - ox, y + 160 + i * 112 - oy + int((1 - pp) * 80), a=a * min(1, pp * 2), clip=win if False else None)
        pp = ease_out_expo((lt - 0.5) / 0.7); s, ox, oy = sprite(self.sub, 700, 28, AMBER, 0.2)
        blit(fr, s, int(W / 2 - (s.shape[1] - 2 * ox) / 2) - ox, y + h_ - 70 - oy, a=a * pp)
