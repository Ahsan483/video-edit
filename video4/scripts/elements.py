"""Placards: understated serif typography that lives in the margin BELOW the picture window (never on the face)."""
from common import *
OUT_D = 0.35

class Placard:
    kind = "placard"
    def __init__(self, kicker, title, notes, t0, t1, base=1784):
        self.kicker, self.title, self.notes, self.t0, self.t1, self.base = kicker, title, notes, t0, t1, base
        self.size = 96 if adv(title, "serif600", 96, -0.01) < 860 else 80
    def active(self, t): return self.t0 <= t <= self.t1 + OUT_D
    def draw(self, fr, t):
        lt = t - self.t0; out = clamp01((t - self.t1) / OUT_D); a = 1 - ease_in_cubic(out); lift = int(ease_in_cubic(out) * -14)
        cx = W // 2
        if self.kicker:
            p = ease_out_expo((lt - 0.05) / 0.7)
            sp, ox, oy = sprite(self.kicker, "sans", 21, GOLD, 0.26); w_ = adv(self.kicker, "sans", 21, 0.26)
            blit(fr, sp, int(cx - w_ / 2) - ox, self.base - 100 - oy + int((1 - p) * 14) + lift, a=a * p)
        # title: word-by-word mask rise
        words = self.title.split(" "); sz = self.size; sp_ = int(sz * 0.24)
        ws = [adv(w, "serif600", sz, -0.01) for w in words]; tot = sum(ws) + sp_ * (len(ws) - 1); x = cx - tot / 2
        win = (0, int(self.base - sz * 0.80), W, int(self.base + sz * 0.28))
        for i, w in enumerate(words):
            p = ease_out_expo((lt - 0.12 - i * 0.09) / 0.8)
            spr, ox, oy = sprite(w, "serif600", sz, IVORY, -0.01)
            blit(fr, spr, int(x) - ox, self.base - oy + int((1 - p) * sz * 0.9) + lift, a=min(1, p * 2) * a, clip=win)
            x += ws[i] + sp_
        # hairline draws out from the centre
        u = ease_in_out_cubic((lt - 0.35) / 0.8)
        fill_rect(fr, cx - 150 * u, self.base + 26 + lift, cx + 150 * u, self.base + 27.5 + lift, GOLD, 0.85 * a)
        if self.notes:
            p = ease_out_expo((lt - 0.55) / 0.8)
            sp, ox, oy = sprite(self.notes, "sans", 20, SOFT, 0.22); w_ = adv(self.notes, "sans", 20, 0.22)
            blit(fr, sp, int(cx - w_ / 2) - ox, self.base + 66 - oy + int((1 - p) * 10) + lift, a=a * p)

class TopLabel:
    """Tiny tracked-caps label in the top margin; present the whole film."""
    kind = "toplabel"
    def __init__(self, text, t0, t1): self.text, self.t0, self.t1 = text, t0, t1
    def active(self, t): return self.t0 <= t <= self.t1 + 0.5
    def draw(self, fr, t):
        a = ease_out_cubic((t - self.t0) / 1.0) * (1 - ease_in_cubic((t - self.t1) / 0.5)) * 0.8
        sp, ox, oy = sprite(self.text, "sans", 17, GOLD, 0.3); w_ = adv(self.text, "sans", 17, 0.3)
        blit(fr, sp, int((W - w_) / 2) - ox, 42 - oy, a=a)
