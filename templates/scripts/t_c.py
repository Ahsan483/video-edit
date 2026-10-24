from lib import *

def star_pts(cx, cy, r_out, r_in, n, rot):
    pts = []
    for j in range(n * 2):
        a = j * math.pi / n + rot; r = r_out if j % 2 == 0 else r_in; pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts, np.int32)

# ================================================================= 08 STICKER POP
class T08:
    name = "08_sticker_pop"
    YEL = (255, 213, 0); PINK = (255, 70, 150); BLUE = (40, 92, 255); BLK = (20, 20, 20); WHT = (255, 255, 255); MINT = (60, 230, 170)
    def sticker(self, txt, size, fill, off=14, stroke=16):
        key = (txt, size, fill)
        if not hasattr(self, "c"): self.c = {}
        if key in self.c: return self.c[key]
        inner = spr(txt, "bowlby", size, fill, 0.0, stroke=stroke, stroke_color=self.BLK)
        # white outer sticker border + pink hard shadow
        a = inner[..., 3]; k = np.ones((3, 3), np.uint8)
        outer = cv2.dilate(a, np.ones((2 * 14 + 1, 2 * 14 + 1), np.uint8))
        sh = np.zeros_like(a); sh[off:, off:] = outer[:-off, :-off]
        canvas = np.zeros((*a.shape, 4), np.uint8)
        canvas[..., :3] = np.array(self.PINK, np.uint8); canvas[..., 3] = sh
        w3 = np.zeros_like(canvas); w3[..., :3] = 255; w3[..., 3] = outer
        res = canvas.copy(); al = w3[..., 3:4].astype(np.float32) / 255; res[..., :3] = (res[..., :3] * (1 - al) + w3[..., :3] * al).astype(np.uint8); res[..., 3] = np.maximum(canvas[..., 3], w3[..., 3])
        al = inner[..., 3:4].astype(np.float32) / 255; res[..., :3] = (res[..., :3] * (1 - al) + inner[..., :3] * al).astype(np.uint8); res[..., 3] = np.maximum(res[..., 3], inner[..., 3])
        self.c[key] = res; return res
    def frame(self, t, k):
        fr = np.zeros((H, W, 3), np.uint8); fr[:] = self.YEL[::-1]
        # halftone dots
        yy, xx = np.mgrid[0:H:44, 0:W:44]
        for y, x in zip(yy.ravel(), xx.ravel()):
            r = int(5 + 4 * math.sin((x + y) * 0.01 + t * 2)); cv2.circle(fr, (int(x + (22 if (y // 44) % 2 else 0)), int(y)), r, (0, 190, 255) if False else (0, 196, 245), -1, cv2.LINE_AA)
        # starburst behind
        p = e_back(lin(t, 0.0, 0.7)) * (1 - e_in(lin(t, 4.6, 5.0)))
        cv2.fillPoly(fr, [star_pts(W / 2, 760, 560 * p, 440 * p, 14, t * 0.35)], self.BLUE[::-1], cv2.LINE_AA)
        cv2.fillPoly(fr, [star_pts(W / 2, 760, 470 * p, 380 * p, 14, -t * 0.25)], (255, 255, 255)[::-1], cv2.LINE_AA) if p > 0.2 else None
        # WOW!
        for txt, y, size, fill, d, rot0 in (("WOW!", 700, 270, self.PINK, 0.2, -6), ("NEW", 1130, 170, self.WHT, 0.65, 4), ("VIDEO", 1330, 200, self.MINT, 0.85, -3)):
            p = e_elastic(lin(t, d, d + 0.9)); ex = e_in(lin(t, 4.5 + d * 0.1, 4.95))
            s = self.sticker(txt, size, fill); idle = 1 + 0.025 * math.sin(t * 5 + d * 4)
            put(fr, s, W / 2, y, scale=max(p, 0.001) * idle * (1 - ex), rot=rot0 + 5 * math.sin(t * 3 + d * 3) * min(p, 1))
        # shapes pop
        shapes = [("circle", (160, 330), 70, self.BLUE, 1.0), ("circle", (W - 140, 1020), 60, self.PINK, 1.15), ("zig", (W - 230, 380), 0, self.BLK, 1.3), ("plus", (170, 1620), 56, self.BLK, 1.45), ("circle", (W - 190, 1680), 90, self.BLUE, 1.6)]
        for kind, c, r, col, d in shapes:
            p = e_back(lin(t, d, d + 0.5)) * (1 - e_in(lin(t, 4.6, 5.0)))
            if p <= 0: continue
            bob = 10 * math.sin(t * 3 + d * 5)
            if kind == "circle": cv2.circle(fr, (c[0], int(c[1] + bob)), int(r * p), col[::-1], -1, cv2.LINE_AA); cv2.circle(fr, (c[0], int(c[1] + bob)), int(r * p), self.BLK[::-1], 6, cv2.LINE_AA)
            elif kind == "plus":
                rr = int(r * p); cv2.line(fr, (c[0] - rr, c[1]), (c[0] + rr, c[1]), col[::-1], 22, cv2.LINE_AA); cv2.line(fr, (c[0], c[1] - rr), (c[0], c[1] + rr), col[::-1], 22, cv2.LINE_AA)
            else:
                pts = np.array([(c[0] - 110 * p + i * 44 * p, c[1] + (30 if i % 2 else -30) * p + bob) for i in range(6)], np.int32); cv2.polylines(fr, [pts], False, col[::-1], 14, cv2.LINE_AA)
        # arrow sticker
        return fr

# ================================================================= 09 GLASS UI
class T09:
    name = "09_glass_ui"
    def __init__(self):
        self.tile = noise_tile(8); self.cm = {}
    def bgf(self, t):
        h, w = 480, 270; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); xx /= w; yy /= h
        base = np.zeros((h, w, 3), np.float32); base[:] = (14, 18, 52)[::-1]
        bl = [((70, 120, 255), 0.2 + 0.12 * math.sin(t * 0.8), 0.18 + 0.05 * math.cos(t * 0.6), 0.55), ((190, 80, 255), 0.85, 0.5 + 0.12 * math.sin(t * 0.9), 0.5),
              ((40, 220, 200), 0.3 + 0.1 * math.cos(t * 0.7), 0.85, 0.5), ((255, 120, 170), 0.75 + 0.08 * math.sin(t), 0.12, 0.35)]
        for c, bx, by, r in bl:
            d = np.sqrt((xx - bx) ** 2 + ((yy - by) * 1.6) ** 2) / r; a = np.clip(1 - d, 0, 1) ** 1.5
            base = base * (1 - a[..., None] * 0.85) + np.array(c[::-1], np.float32) * a[..., None] * 0.85
        return cv2.resize(base, (W, H), interpolation=cv2.INTER_CUBIC)
    def glass(self, fr, x, y, w, h, r, p, tint=0.13):
        if p <= 0.01: return
        yi, xi = int(y + (1 - p) * 120), int(x); key = (w, h, r)
        if key not in self.cm:
            m = rrect_mask(h, w, r); self.cm[key] = (m, np.clip(m - cv2.erode(m, np.ones((3, 3), np.uint8)), 0, 1))
        m, edge = self.cm[key]; m3 = m[..., None] * p
        # shadow
        sh = np.zeros((H, W), np.float32); sh[yi + 18:yi + h + 18, xi + 6:xi + w - 6] = 1; sh = cv2.GaussianBlur(sh, (0, 0), 28)[..., None]
        fr[:] = fr * (1 - 0.35 * sh * p)
        reg = fr[yi:yi + h, xi:xi + w]
        blur = cv2.GaussianBlur(reg, (0, 0), 14)
        grad = np.linspace(1.0, 0.35, h, dtype=np.float32)[:, None, None]
        reg[:] = reg * (1 - m3) + (blur * 0.9 + 255 * tint * grad) * m3
        reg[:] = reg + edge[..., None] * 255 * 0.35 * p * np.linspace(1, 0.2, h)[:, None, None]
    def frame(self, t, k):
        fr = self.bgf(t)
        # floating orbs for depth
        for i, (cx, cy, r, c) in enumerate(((190, 360, 120, (255, 255, 255)), (W - 150, 1520, 160, (255, 255, 255)))):
            p = e_expo(lin(t, 0.0, 1.0)); yb = cy + 14 * math.sin(t * 1.3 + i * 2); ov = np.zeros((H, W), np.float32); cv2.circle(ov, (cx, int(yb)), int(r * p), 1.0, -1, cv2.LINE_AA)
            ov = cv2.GaussianBlur(ov, (0, 0), 2)[..., None]; fr = fr * (1 - ov * 0.18) + 255 * ov * 0.18
        # big glass card with greeting
        p1 = e_expo(lin(t, 0.15, 1.1)); self.glass(fr, 70, 320, W - 140, 640, 56, p1)
        # profile bubble
        pa = e_back(lin(t, 0.5, 1.2)); ov = np.zeros((H, W, 3), np.float32)
        if pa > 0.02:
            c = (190, 500 + (1 - p1) * 120); cv2.circle(ov, (int(c[0]), int(c[1])), int(70 * pa), (255, 255, 255), -1, cv2.LINE_AA)
            g = np.zeros((H, W, 3), np.float32); cv2.circle(g, (int(c[0]), int(c[1])), int(70 * pa), (255, 120, 90)[::-1] if False else (130, 120, 255), -1, cv2.LINE_AA)
            m = (ov[..., :1] > 0).astype(np.float32); fr = fr * (1 - m) + (g * 0.0 + np.array((255, 170, 120)[::-1], np.float32)) * m
        tmp = to8(fr)
        if pa > 0.02: put(tmp, spr("C", "spacegrotesk-700", 80, (255, 255, 255)), 190, 500 + (1 - p1) * 120, scale=pa, alpha=pa)
        pp = e_expo(lin(t, 0.55, 1.4)); put(tmp, spr("Hello, Creator", "inter-800", 84, (255, 255, 255), -0.03), 70 + 60 + spr("Hello, Creator", "inter-800", 84, (255, 255, 255), -0.03).shape[1] / 2 - 20, 690 + (1 - pp) * 40 + (1 - p1) * 120, alpha=pp, clip=(0, 0, W, 800))
        pp2 = e_expo(lin(t, 0.8, 1.6)); put(tmp, spr("Your studio is ready.", "inter-300", 46, (230, 236, 255), 0.0), 70 + 60 + spr("Your studio is ready.", "inter-300", 46, (230, 236, 255), 0.0).shape[1] / 2 - 20, 770 + (1 - p1) * 120, alpha=pp2)
        fr = tmp.astype(np.float32)
        # three action chips
        for i, lab in enumerate(("Edit", "Publish", "Analytics")):
            p = e_expo(lin(t, 1.1 + i * 0.16, 2.0 + i * 0.16)); w = 270 if i < 2 else 330; xs = 70 + i * 300 if i < 2 else 70 + 600
            self.glass(fr, xs, 840 if False else 1010, w if i < 2 else 330, 130, 65, p, tint=0.16)
        tmp = to8(fr)
        for i, lab in enumerate(("Edit", "Publish", "Analytics")):
            p = e_expo(lin(t, 1.1 + i * 0.16, 2.0 + i * 0.16)); w = 270 if i < 2 else 330; xs = 70 + i * 300 if i < 2 else 70 + 600
            put(tmp, spr(lab, "inter-500", 42, (255, 255, 255)), xs + (w if i < 2 else 330) / 2, 1010 + 65 + (1 - p) * 120, alpha=p)
        fr = tmp.astype(np.float32)
        # progress ring card
        p3 = e_expo(lin(t, 1.5, 2.4)); self.glass(fr, 70, 1190, W - 140, 520, 56, p3)
        tmp = to8(fr)
        if p3 > 0.3:
            c = (300, int(1450 + (1 - p3) * 120)); prog = e_io(lin(t, 2.0, 3.6)) * 0.82
            ring = np.zeros((H, W), np.uint8); cv2.ellipse(ring, c, (130, 130), 0, -90, -90 + 360, 255, 22, cv2.LINE_AA)
            tmp = (tmp * (1 - ring[..., None] / 255.0 * 0.25)).astype(np.uint8)
            ring2 = np.zeros((H, W), np.uint8); cv2.ellipse(ring2, c, (130, 130), 0, -90, -90 + 360 * prog, 255, 22, cv2.LINE_AA)
            a = ring2[..., None].astype(np.float32) / 255; tmp = (tmp * (1 - a) + np.array((255, 255, 255)[::-1], np.float32) * a).astype(np.uint8)
            put(tmp, spr(f"{int(prog * 100)}%", "inter-800", 78, (255, 255, 255), -0.02), c[0], c[1], alpha=p3)
            put(tmp, spr("Render complete", "inter-800", 52, (255, 255, 255), -0.02), 690, c[1] - 40, alpha=p3)
            put(tmp, spr("4K · 120 fps · exported", "inter-300", 36, (230, 236, 255)), 690, c[1] + 30, alpha=p3)
        fr = tmp.astype(np.float32)
        fr = grain(fr, 3.0, k, self.tile)
        if t > 4.5: fr = fr * (1 - e_in(lin(t, 4.5, 5.0)) * 0.9)
        return to8(fr)

# ================================================================= 10 MARQUEE STACK
class T10:
    name = "10_marquee_stack"
    BG = (12, 12, 12); LIME = (200, 255, 0); WHT = (244, 244, 240)
    def __init__(self):
        self.cw = 3000; self.cache = {}
    def row_sprite(self, kind):
        if kind in self.cache: return self.cache[kind]
        txt = "CREATE EVERYTHING  /  "
        if kind == "fill": s = spr(txt * 3, "anton", 300, self.WHT, 0.0)
        elif kind == "lime": s = spr(txt * 3, "anton", 300, self.LIME, 0.0)
        else: s = spr(txt * 3, "anton", 300, self.BG, 0.0, stroke=3, stroke_color=(120, 120, 120))
        one = text_w(txt, "anton", 300, 0.0); self.cache[kind] = (s, one); return self.cache[kind]
    def frame(self, t, k):
        # draw rows on a large canvas then rotate for the diagonal look
        CW, CH = 2300, 2500; can = np.zeros((CH, CW, 3), np.uint8); can[:] = self.BG[::-1]
        rows = 8; rh = 250; y0 = CH // 2 - rows * rh // 2
        ease = e_expo(lin(t, 0.0, 1.2)); speed = 1.0 + 3.5 * (1 - e_out(lin(t, 0.0, 2.2), 2))
        for i in range(rows):
            kind = "lime" if i == 4 else ("fill" if i % 2 == 0 else "outline")
            s, one = self.row_sprite(kind); direction = 1 if i % 2 == 0 else -1
            off = (t * (220 + 90 * (i % 3)) * (1 + 3.0 * (1 - e_out(lin(t, 0.0, 2.4), 2))) * direction) % one
            # bring rows in with a staggered vertical slide
            p = e_expo(lin(t, 0.05 + abs(i - 3.5) * 0.07, 0.9 + abs(i - 3.5) * 0.07)); ycen = y0 + i * rh + rh / 2 + (1 - p) * (900 if i % 2 else -900)
            cx = CW / 2 - off if direction == 1 else CW / 2 - one + off
            x = cx
            while x - s.shape[1] / 2 > -200: x -= one
            put(can, s, x + s.shape[1] / 2 if False else cx, ycen, scale=1.0, alpha=p)
        # rotate canvas -9 deg and crop to frame, with a slow push
        ang = -9; sc = 1.0 + 0.06 * e_io(lin(t, 0, 5.0))
        M = cv2.getRotationMatrix2D((CW / 2, CH / 2), ang, sc); M[:, 2] += np.array([W / 2 - CW / 2, H / 2 - CH / 2])
        fr = cv2.warpAffine(can, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=self.BG[::-1])
        # tag pill
        p = e_back(lin(t, 1.6, 2.2)) * (1 - e_in(lin(t, 4.6, 5.0)))
        if p > 0.02:
            bw, bh = int(640 * p), int(120 * p)
            if bw > 20:
                m = rrect_mask(bh, bw, bh // 2); cx, cy = W // 2, 1560
                reg = fr[cy - bh // 2:cy - bh // 2 + bh, cx - bw // 2:cx - bw // 2 + bw].astype(np.float32); reg[:] = reg * (1 - m[..., None]) + np.array(self.WHT[::-1], np.float32) * m[..., None]
                fr[cy - bh // 2:cy - bh // 2 + bh, cx - bw // 2:cx - bw // 2 + bw] = reg.astype(np.uint8)
                put(fr, spr("NEW SEASON", "spacegrotesk-700", 46, self.BG, 0.05), cx - 50, cy, scale=p); cv2.arrowedLine(fr, (cx + 150, cy), (cx + 210, cy), self.BG[::-1], 5, cv2.LINE_AA, tipLength=0.4) if p > 0.9 else None
        if t > 4.6: fr = to8(fr.astype(np.float32) * (1 - e_in(lin(t, 4.6, 5.0), 2)))
        return fr
