"""Kinetic typography + motion-graphics elements for the 9:16 shorts (draw on BGR 1080x1920 frames, t in output seconds)."""
from common import *

OUT_D = 0.25
def _adv(txt, weight, size, track=0.0, mono=False): return text_width(txt, weight, size, track, mono)
def lerp(a, b, k): return a + (b - a) * k

class Caption:
    """Karaoke caption chunk: words reveal with a mask-rise, the spoken word pops in amber, spoken words stay white, upcoming words dim."""
    kind = "caption"
    def __init__(self, words, size=66, weight=800, zone=CAP_ZONE):
        # words: [(text, t0, t1)]
        self.words = words; self.size = size; self.weight = weight
        self.t0 = words[0][1] - 0.04; self.t1 = words[-1][2] + 0.06
        self.zone = zone; maxw = zone[2] - zone[0]
        sp = int(size * 0.28); lines = [[]]; w = 0
        for i, (tx, a, b) in enumerate(words):
            ww = _adv(tx, weight, size, -0.02)
            if lines[-1] and w + sp + ww > maxw: lines.append([]); w = 0
            lines[-1].append(i); w += (sp if len(lines[-1]) > 1 else 0) + ww
        self.pos = {}; lh = int(size * 1.18); zc = (zone[1] + zone[3]) / 2
        base0 = zc + size * 0.36 - (len(lines) - 1) * lh / 2
        for li, ln in enumerate(lines):
            tot = sum(_adv(words[i][0], weight, size, -0.02) for i in ln) + sp * (len(ln) - 1)
            x = (zone[0] + zone[2]) / 2 - tot / 2
            for i in ln:
                self.pos[i] = (x, base0 + li * lh); x += _adv(words[i][0], weight, size, -0.02) + sp
    def active(self, t): return self.t0 <= t <= self.t1
    def draw(self, fr, t):
        z = self.zone; a_out = 1 - ease_in_cubic((t - (self.t1 - 0.06)) / 0.06)
        for i, (tx, a, b) in enumerate(self.words):
            x, base = self.pos[i]
            p = ease_out_expo((t - (a - 0.05 - 0.0)) / 0.20)
            if t < a - 0.12: col, al = SOFT, 0.0
            elif t < a: col, al = SOFT, 0.55 * p
            elif t <= b: col, al = AMBER, 1.0
            else: col, al = OFFWHITE, 1.0
            if al <= 0: continue
            pop = 1.0
            if a <= t <= b + 0.08: pop = 1 + 0.13 * math.sin(math.pi * clamp01((t - a) / 0.22)) ** 0.8
            spr, ox, oy = sprite(tx, self.weight, self.size, col, -0.02, shadow=0.0)
            if pop > 1.003:
                s2 = cv2.resize(spr, None, fx=pop, fy=pop, interpolation=cv2.INTER_LINEAR)
                cx_ = x + _adv(tx, self.weight, self.size, -0.02) / 2; cy_ = base - 0.35 * self.size
                px, py = spr.shape[1] / 2 * pop, (oy - 0.35 * self.size) * pop
                blit(fr, s2, int(cx_ - px), int(cy_ - py), a=al * a_out)
            else:
                dy = int((1 - p) * self.size * 0.35)
                blit(fr, spr, int(x) - ox, int(base) - oy + dy, a=al * a_out * min(1, p * 1.6),
                     clip=(0, int(base - self.size * 1.05), W, int(base + self.size * 0.3)) if p < 0.99 else None)

class Behind:
    """Giant keyword behind the creator (per-letter mask-rise, amber underline sweep). The renderer re-composites the person matte on top."""
    kind = "behind"
    def __init__(self, text, t0, t1, right=1050, base=1400, size=170, weight=800, color=OFFWHITE, underline=True, x=None, track=-0.035):
        self.text, self.t0, self.t1, self.base, self.size, self.weight, self.color, self.underline = text, t0, t1, base, size, weight, color, underline
        w = text_width(text, weight, size, track)
        self.x = x if x is not None else right - w
        self.track = track; self.xs = []; cx = float(self.x)
        for i, ch in enumerate(text):
            self.xs.append(cx)
            adv = _adv(text[i:i + 2], weight, size, track) - _adv(text[i + 1:i + 2], weight, size, track) if i + 1 < len(text) else _adv(ch, weight, size, track)
            cx += adv
        self.x1 = cx
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_D + 0.1
    def draw(self, fr, t):
        lt = t - self.t0; n = len(self.text); out = clamp01((t - self.t1) / 0.3)
        win = (0, int(self.base - self.size * 0.80), W, int(self.base + self.size * 0.26))
        for i, ch in enumerate(self.text):
            if ch == " ": continue
            p = ease_out_expo((lt - i * 0.04) / 0.6)
            q = ease_in_cubic((out - (n - 1 - i) * 0.03) / 0.7) if out > 0 else 0
            spr, ox, oy = sprite(ch, self.weight, self.size, self.color, 0, shadow=0.35)
            blit(fr, spr, int(self.xs[i]) - ox, self.base - oy + int((1 - p) * self.size * 0.95 + q * self.size * 0.35),
                 a=min(1, p * 2.2) * (1 - q), clip=win)
        if self.underline:
            u = ease_in_out_cubic((lt - 0.5) / 0.5); ua = 1 - ease_in_cubic((out - 0.1) / 0.6)
            fill_rect(fr, self.x + 4, self.base + 18, self.x + 4 + (self.x1 - self.x - 8) * u, self.base + 24, AMBER, ua)

class SectionTag:
    """Top-left section label that slides up when the topic changes (amber square + tracked caps)."""
    kind = "tag"
    def __init__(self, text, t0, t1, x=44, y=124, size=30):
        self.text, self.t0, self.t1, self.x, self.y, self.size = text, t0, t1, x, y, size
    def active(self, t): return self.t0 <= t <= self.t1 + 0.3
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.25)
        p = ease_out_expo(lt / 0.5); a = (1 - ease_in_cubic(out))
        s = self.size; sq = int(s * 0.5)
        fill_rect(fr, self.x, self.y - s * 0.75, self.x + sq * ease_out_expo(lt / 0.3), self.y - s * 0.75 + sq, AMBER, a)
        spr, ox, oy = sprite(self.text, 700, s, OFFWHITE, 0.14)
        win = (self.x + sq + 14, int(self.y - s * 1.1), W, int(self.y + s * 0.4))
        blit(fr, spr, self.x + sq + 14 - ox, self.y - oy + int((1 - p) * s * 1.2) - int(ease_in_cubic(out) * s * 1.2), a=a, clip=win)

class Ring:
    """UI callout: amber rounded outline around a source-screen rect + optional label chip. Tracks the zoom via ctx['map']."""
    kind = "ring"
    def __init__(self, rect, t0, t1, label=None, dim=0.0, place="below"):
        self.rect, self.t0, self.t1, self.label, self.dim, self.place = rect, t0, t1, label, dim, place
    def active(self, t): return self.t0 <= t <= self.t1 + 0.3
    def draw(self, fr, t, ctx=None):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.25); p = ease_out_expo(lt / 0.5); a = 1 - ease_in_cubic(out)
        (x0, y0), s = ctx["map"](self.rect[0], self.rect[1]), ctx["scale"]
        x1, y1 = ctx["map"](self.rect[2], self.rect[3])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hh = (x1 - x0) / 2 * p + 8, (y1 - y0) / 2 * p + 6
        cxl, cyl, cxr, cyr = SCR_CARD[0] + 6, SCR_CARD[1] + 6, SCR_CARD[2] - 6, SCR_CARD[3] - 6
        if self.dim > 0:
            ov = fr[SCR_CARD[1]:SCR_CARD[3], SCR_CARD[0]:SCR_CARD[2]]
            m = np.full(ov.shape[:2], self.dim * a * p, np.float32)
            rx0, ry0, rx1, ry1 = int(cx - hw - SCR_CARD[0]), int(cy - hh - SCR_CARD[1]), int(cx + hw - SCR_CARD[0]), int(cy + hh - SCR_CARD[1])
            m[max(ry0, 0):max(ry1, 0), max(rx0, 0):max(rx1, 0)] = 0
            m = cv2.GaussianBlur(m, (0, 0), 6)
            ov[:] = (ov * (1 - m[..., None]) + np.array(NAVY[::-1], np.float32) * m[..., None]).astype(np.uint8)
        # outline (anti-aliased via supersampled mask on a small canvas)
        x0i, y0i, x1i, y1i = int(cx - hw), int(cy - hh), int(cx + hw), int(cy + hh)
        pad = 8; w_, h_ = x1i - x0i + 2 * pad, y1i - y0i + 2 * pad
        if w_ > 4 and h_ > 4:
            m = np.zeros((h_ * 2, w_ * 2), np.uint8)
            cv2.rectangle(m, (pad * 2, pad * 2), (w_ * 2 - pad * 2, h_ * 2 - pad * 2), 255, 5, cv2.LINE_AA)
            m = cv2.resize(m, (w_, h_), interpolation=cv2.INTER_AREA)
            spr = np.zeros((h_, w_, 4), np.uint8); spr[..., 0], spr[..., 1], spr[..., 2] = AMBER; spr[..., 3] = m
            blit(fr, spr, x0i - pad, y0i - pad, a=a, clip=(cxl, cyl, cxr, cyr))
        if self.label:
            sp, ox, oy = sprite(self.label, 800, 24, NAVY, 0.1)
            tw = _adv(self.label, 800, 24, 0.1); cw_, ch_ = int(tw + 30), 40
            bx = int(min(max(cx - cw_ / 2, cxl + 4), cxr - cw_ - 4)); by = int(y1i + 12 if self.place == "below" else y0i - 12 - ch_)
            by = min(max(by, cyl + 4), cyr - ch_ - 4)
            chip = np.zeros((ch_, cw_, 4), np.uint8); chip[..., 0], chip[..., 1], chip[..., 2] = AMBER
            r = np.zeros((ch_, cw_), np.uint8); cv2.rectangle(r, (0, 0), (cw_ - 1, ch_ - 1), 255, -1)
            r = cv2.GaussianBlur(r, (0, 0), 0.8); chip[..., 3] = r
            pp = ease_out_expo((lt - 0.12) / 0.45)
            blit(fr, chip, bx, by + int((1 - pp) * 10), a=a * pp)
            blit(fr, sp, bx + 15 - ox, by + 28 - oy + int((1 - pp) * 10), a=a * pp)

class Hook:
    """Opening title: dims the frame, staggered word mask-rise lines, amber underline sweep, wipes out."""
    kind = "hook"
    def __init__(self, lines, t0, t1, size=118, base=None, dim=0.84, sub=None):
        self.lines, self.t0, self.t1, self.size, self.dim, self.sub = lines, t0, t1, size, dim, sub
        self.base = base or 900
    def active(self, t): return self.t0 <= t <= self.t1 + 0.45
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.4)
        am = ease_out_cubic(lt / 0.25) * (1 - ease_in_cubic(out))
        if am > 0:
            fr[:] = (fr.astype(np.float32) * (1 - self.dim * am) + np.array(NAVY[::-1], np.float32) * self.dim * am).astype(np.uint8)
        nl = len(self.lines); lh = int(self.size * 1.12)
        for li, line in enumerate(self.lines):
            base = int(self.base + (li - (nl - 1) / 2) * lh)
            ws = [_adv(w, 800, self.size, -0.03) for w, _ in line]; sp = int(self.size * 0.26)
            tot = sum(ws) + sp * (len(ws) - 1); cx = (W - tot) / 2
            win = (0, int(base - self.size * 0.95), W, int(base + self.size * 0.28))
            for wi, (w, acc) in enumerate(line):
                p = ease_out_expo((lt - 0.08 - li * 0.14 - wi * 0.08) / 0.65)
                spr, ox, oy = sprite(w, 800, self.size, AMBER if acc else OFFWHITE, -0.03)
                q = ease_in_cubic(out)
                blit(fr, spr, int(cx) - ox, base - oy + int((1 - p) * self.size * 1.1 - q * self.size * 0.5), a=min(1, p * 2) * (1 - q), clip=win)
                cx += ws[wi] + sp
        u = ease_in_out_cubic((lt - 0.55) / 0.5) * (1 - ease_in_cubic(out))
        if u > 0:
            ub = int(self.base + nl * self.size * 0.62 + 8)
            fill_rect(fr, W / 2 - 150 * u, ub, W / 2 + 150 * u, ub + 7, AMBER, 1)
        if self.sub:
            p = ease_out_expo((lt - 0.7) / 0.6)
            spr, ox, oy = sprite(self.sub, 700, 30, SOFT, 0.16); w_ = _adv(self.sub, 700, 30, 0.16)
            blit(fr, spr, int((W - w_) / 2) - ox, int(self.base + nl * self.size * 0.62 + 70) - oy, a=p * (1 - ease_in_cubic(out)))

class Sweep:
    """Topic-change wipe: thin amber line sweeps down the screen card with a brief highlight band."""
    kind = "sweep"
    def __init__(self, t0): self.t0 = t0
    def active(self, t): return self.t0 <= t <= self.t0 + 0.5
    def draw(self, fr, t):
        p = ease_in_out_cubic((t - self.t0) / 0.45); a = math.sin(math.pi * clamp01((t - self.t0) / 0.5))
        x0, y0, x1, y1 = SCR_CARD; y = int(lerp(y0, y1, p))
        fill_rect(fr, x0, y - 2, x1, y + 2, AMBER, 0.9 * a)
        band = fr[max(y - 60, y0):y, x0:x1].astype(np.float32)
        if band.size: fr[max(y - 60, y0):y, x0:x1] = (band + (np.array(AMBER[::-1], np.float32) - band) * 0.10 * a).astype(np.uint8)

class Stat:
    """Big number that counts up with a tracked-caps caption (placed in the free right side of the webcam block)."""
    kind = "stat"
    def __init__(self, text, caption, t0, t1, x=1030, base=1230, size=118, align="right"):
        self.text, self.caption, self.t0, self.t1, self.x, self.base, self.size, self.align = text, caption, t0, t1, x, base, size, align
        import re
        self.m = re.match(r"^(\D*)([\d,\.]+)(\D*)$", text)
    def active(self, t): return self.t0 <= t <= self.t1 + 0.3
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / 0.25); a = 1 - ease_in_cubic(out); p = ease_out_expo(lt / 0.6)
        txt = self.text
        if self.m:
            pre, num, suf = self.m.groups(); target = float(num.replace(",", ""))
            v = target * ease_out_cubic(lt / 0.9); fmt = "{:,.0f}" if "," in num or "." not in num else "{:,.1f}"
            txt = pre + (fmt.format(v)) + suf
        spr, ox, oy = sprite(txt, 800, self.size, OFFWHITE, -0.03, shadow=0.4); w_ = spr.shape[1] - 2 * ox
        x = self.x - w_ if self.align == "right" else self.x
        win = (0, int(self.base - self.size * 0.95), W, int(self.base + self.size * 0.3))
        blit(fr, spr, int(x) - ox, self.base - oy + int((1 - p) * self.size), a=a * min(1, p * 2), clip=win)
        sp2, ox2, oy2 = sprite(self.caption, 700, 26, AMBER, 0.16); w2 = _adv(self.caption, 700, 26, 0.16)
        pp = ease_out_expo((lt - 0.25) / 0.5)
        blit(fr, sp2, int(x + w_ - w2 if self.align == "right" else x) - ox2, self.base + 44 - oy2, a=a * pp)
        u = ease_in_out_cubic((lt - 0.3) / 0.5)
        fill_rect(fr, x, self.base + 14, x + w_ * u, self.base + 18, AMBER, a * 0.9)
