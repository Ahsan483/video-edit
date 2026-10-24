from lib import *

# ================================================================= 05 PAPER CUT COLLAGE
class T05:
    name = "05_paper_collage"
    def __init__(self):
        rs = np.random.RandomState(4); self.rs = rs
        base = np.zeros((H, W, 3), np.float32); base[:] = (150, 168, 196)[::-1] * np.array([1, 1, 1])
        base = np.zeros((H, W, 3), np.float32); base[:] = np.array((196, 160, 118)[::-1], np.float32)
        n = cv2.resize(rs.randn(H // 4, W // 4).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC) * 7
        n2 = rs.randn(H, W).astype(np.float32) * 5
        self.bg = base + n[..., None] + n2[..., None]
        self.strips = [  # (text, font, size, bg, fg, cy, rot, w, h, delay, from)
            ("BIG", "anton", 360, (245, 236, 214), (26, 26, 26), 520, -4, 760, 360, 0.0, "L"),
            ("SALE", "anton", 380, (205, 52, 40), (250, 240, 220), 900, 3, 860, 380, 0.25, "R"),
            ("WEEKEND", "anton", 200, (36, 118, 128), (250, 240, 220), 1230, -2, 920, 250, 0.5, "L"),
            ("UP TO 50% OFF", "archivo-black", 70, (232, 170, 40), (26, 26, 26), 1480, 2, 780, 120, 0.8, "R")]
        self.cache = {}
        self.poly = {}
        for i, s in enumerate(self.strips):
            w, h = s[7], s[8]; pts = []
            for x in np.linspace(0, w, 28): pts.append((x, rs.randn() * 2.2))
            for y in np.linspace(0, h, 12): pts.append((w + rs.randn() * 2.2, y))
            for x in np.linspace(w, 0, 28): pts.append((x, h + rs.randn() * 2.2))
            for y in np.linspace(h, 0, 12): pts.append((rs.randn() * 2.2, y))
            self.poly[i] = np.array(pts, np.float32)
    def strip_sprite(self, i):
        if i in self.cache: return self.cache[i]
        txt, fnt, size, bg, fg, cy, rot, w, h, dl, fr = self.strips[i]
        pad = 20; can = np.zeros((h + pad * 2, w + pad * 2, 4), np.uint8)
        p = (self.poly[i] + pad).astype(np.int32); cv2.fillPoly(can, [p], (*bg, 255), cv2.LINE_AA)
        # paper edge highlight
        cv2.polylines(can, [p], True, (255, 255, 255, 255) if False else (*[min(255, c + 20) for c in bg], 255), 2, cv2.LINE_AA)
        ts = spr(txt, fnt, size, fg, 0.0); th, tw = ts.shape[:2]
        ys, xs = np.nonzero(ts[..., 3] > 20); bcx, bcy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
        ox, oy = can.shape[1] // 2 - bcx, can.shape[0] // 2 - bcy
        for yy in range(max(oy, 0), min(oy + th, can.shape[0])):
            pass
        cy0, cx0 = max(oy, 0), max(ox, 0); cy1, cx1 = min(oy + th, can.shape[0]), min(ox + tw, can.shape[1])
        reg = can[cy0:cy1, cx0:cx1]; tsc = ts[cy0 - oy:cy1 - oy, cx0 - ox:cx1 - ox]
        al = tsc[..., 3:4].astype(np.float32) / 255; reg[..., :3] = (reg[..., :3] * (1 - al) + tsc[..., :3] * al).astype(np.uint8)
        self.cache[i] = can; return can
    def frame(self, t, k):
        tq = math.floor(t * 12) / 12.0          # stop-motion: everything steps at 12 fps
        fr = self.bg.copy()
        stepseed = int(tq * 12); rs = np.random.RandomState(stepseed)
        layers = np.zeros((H, W, 3), np.uint8); shadow = np.zeros((H, W), np.float32)
        order = []
        for i, s in enumerate(self.strips):
            dl, side = s[9], s[10]; p = e_out(lin(tq, 0.1 + dl, 0.75 + dl), 3)
            jx, jy, jr = rs.uniform(-3, 3), rs.uniform(-3, 3), rs.uniform(-0.8, 0.8)
            x = W / 2 + (1 - p) * (-900 if side == "L" else 900) + jx; y = s[5] + jy + (6 * math.sin(tq * 3 + i) if tq > 2 else 0)
            exit_p = e_in(lin(tq, 4.3 + 0.08 * i, 4.9), 2); x += exit_p * (1100 if side == "L" else -1100)
            spt = self.strip_sprite(i); order.append((spt, x, y, s[6] + jr))
        sh = np.zeros((H, W, 3), np.uint8)
        for spt, x, y, r in order:
            a = spt[..., 3:4].copy(); blk = np.dstack([np.zeros_like(spt[..., :3]), spt[..., 3]]); put(sh, blk, x + 14, y + 20, rot=r, alpha=0.55)
        fr = fr - cv2.GaussianBlur(sh, (0, 0), 12).astype(np.float32) * 0.4
        out = to8(fr)
        for spt, x, y, r in order: put(out, spt, x, y, rot=r)
        # confetti shapes pop
        shapes = [((W - 150, 230), 90, (205, 52, 40)), ((150, 1680), 70, (36, 118, 128)), ((W - 190, 1700), 60, (245, 236, 214))]
        for i, (c, r, col) in enumerate(shapes):
            p = e_back(lin(tq, 1.6 + i * 0.2, 2.1 + i * 0.2)) * (1 - e_in(lin(tq, 4.5, 4.9)))
            if p > 0: cv2.circle(out, (int(c[0] + rs.uniform(-2, 2)), int(c[1] + rs.uniform(-2, 2))), int(r * p), col[::-1], -1, cv2.LINE_AA)
        # star burst
        p = e_back(lin(tq, 1.4, 2.0)) * (1 - e_in(lin(tq, 4.5, 4.9)))
        if p > 0:
            pts = []
            for j in range(16):
                a = j * math.pi / 8 + tq * 0.4; rr = (130 if j % 2 == 0 else 78) * p; pts.append((150 + rr * math.cos(a), 220 + rr * math.sin(a)))
            cv2.fillPoly(out, [np.array(pts, np.int32)], (60, 190, 245), cv2.LINE_AA)
        return out

# ================================================================= 06 GOLD LUXE
class T06:
    name = "06_gold_luxe"
    GOLD0 = (150, 104, 40); GOLD1 = (242, 208, 128); GOLD2 = (255, 247, 214)
    def __init__(self):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((xx - W / 2) / 760) ** 2 + ((yy - H / 2) / 1000) ** 2)
        self.bg = (np.clip(1.0 - d, 0, 1) ** 1.3 * 26 + 5)[..., None] * np.array([1.0, 0.92, 0.8], np.float32)[::-1]
        self.tile = noise_tile(2); self.cache = {}
    def gold_text(self, txt, name, size, track):
        key = (txt, name, size, round(track, 2))
        if key not in self.cache: self.cache[key] = spr(txt, name, size, (255, 255, 255), track)
        return self.cache[key]
    def gold_fill(self, s, cx, cy, phase, alpha, out):
        h, w = s.shape[:2]; x = np.arange(w, dtype=np.float32)[None, :]; y = np.arange(h, dtype=np.float32)[:, None]
        u = (x * 0.9 + y * 0.35) / (w + h * 0.35)
        band = 0.5 + 0.5 * np.sin((u * 2.4 - phase) * math.pi * 2)
        sweep = np.exp(-((u - phase) / 0.07) ** 2)
        c0, c1, c2 = (np.array(c[::-1], np.float32) for c in (self.GOLD0, self.GOLD1, self.GOLD2))
        col = c0 * (1 - band[..., None]) + c1 * band[..., None]; col = col * (1 - sweep[..., None]) + c2 * sweep[..., None]
        rgba = np.dstack([col[..., ::-1].astype(np.uint8), s[..., 3]]); put(out, rgba, cx, cy, alpha=alpha)
    def frame(self, t, k):
        fr = self.bg.copy(); out = to8(fr)
        # frame lines draw in
        p = e_io(lin(t, 0.1, 1.6)); m = 70; L = (255, 224, 160)
        gold_bgr = (112, 168, 212)
        cv2.rectangle(out, (m, m), (int(m + (W - 2 * m) * p), m + 2), gold_bgr, -1)
        cv2.rectangle(out, (W - m - 2, m), (W - m, int(m + (H - 2 * m) * p)), gold_bgr, -1)
        cv2.rectangle(out, (int(W - m - (W - 2 * m) * p), H - m - 2), (W - m, H - m), gold_bgr, -1)
        cv2.rectangle(out, (m, int(H - m - (H - 2 * m) * p)), (m + 2, H - m), gold_bgr, -1)
        cv2.rectangle(out, (m + 18, m + 18), (W - m - 18, H - m - 18), (60, 90, 120), 1)
        # diamond ornament
        dp = e_back(lin(t, 0.9, 1.5)); c = (W // 2, 700)
        for r, col, th in ((26, gold_bgr, 2),):
            pts = np.array([[c[0], c[1] - r * dp], [c[0] + r * dp, c[1]], [c[0], c[1] + r * dp], [c[0] - r * dp, c[1]]], np.int32); cv2.polylines(out, [pts], True, col, th, cv2.LINE_AA)
        cv2.line(out, (int(c[0] - 150 * dp), c[1]), (int(c[0] - 44 * dp), c[1]), gold_bgr, 2, cv2.LINE_AA); cv2.line(out, (int(c[0] + 44 * dp), c[1]), (int(c[0] + 150 * dp), c[1]), gold_bgr, 2, cv2.LINE_AA)
        # title with expanding tracking
        trk = mix(-0.02, 0.07, e_out(lin(t, 0.7, 3.2))); phase = (t - 0.8) / 3.0
        a1 = e_out(lin(t, 0.9, 1.9)); a2 = e_out(lin(t, 1.15, 2.15))
        s1 = self.gold_text("THE", "cormorant-600", 96, round(trk * 0.5, 2)); s2 = self.gold_text("COLLECTION", "cormorant-600", 118, round(trk * 0.5, 2))
        self.gold_fill(s1, W / 2, 800 + (1 - a1) * 26, phase, a1, out); self.gold_fill(s2, W / 2, 930 + (1 - a2) * 26, phase + 0.05, a2, out)
        # script line
        s3 = spr("Autumn / Winter 2026", "cormorant-i", 62, (232, 214, 170), 0.04); a3 = e_out(lin(t, 2.2, 3.1))
        put(out, s3, W / 2, 1150 + (1 - a3) * 16, alpha=a3)
        s4 = spr("PRIVATE PREVIEW  ·  BY INVITATION", "spacegrotesk-500", 28, (176, 150, 104), 0.42); put(out, s4, W / 2, 1560, alpha=e_out(lin(t, 2.8, 3.6)))
        # vignette fade out
        fo = e_in(lin(t, 4.5, 5.0), 2)
        res = grain(out.astype(np.float32), 2.2, k, self.tile) * (1 - fo)
        return to8(res)

# ================================================================= 07 DATA DASHBOARD
class T07:
    name = "07_data_dashboard"
    BG = (9, 14, 28); CARD = (18, 27, 52); LINE = (40, 56, 96); BLUE = (64, 134, 255); MINT = (58, 222, 160); TEXT = (236, 241, 255); MUTE = (126, 140, 178)
    def __init__(self):
        self.bgimg = np.zeros((H, W, 3), np.uint8); self.bgimg[:] = np.array(self.BG[::-1], np.uint8)
        for x in range(0, W, 60): self.bgimg[:, x] = np.minimum(self.bgimg[:, x].astype(int) + 5, 255).astype(np.uint8)
        for y in range(0, H, 60): self.bgimg[y, :] = np.minimum(self.bgimg[y, :].astype(int) + 5, 255).astype(np.uint8)
        self.data = [38, 52, 44, 66, 61, 82, 78, 96, 110, 104, 128, 150]
        self.bars = [42, 58, 51, 74, 69, 96, 120]
        self.masks = {}
    def card(self, fr, x, y, w, h, p):
        if p <= 0.01: return None
        yy = y + (1 - p) * 90; key = (w, h)
        if key not in self.masks: self.masks[key] = rrect_mask(h, w, 30)
        m = self.masks[key][..., None] * p; yi = int(yy); xi = int(x)
        reg = fr[yi:yi + h, xi:xi + w].astype(np.float32); c = np.array(self.CARD[::-1], np.float32)
        reg[:] = reg * (1 - m) + c * m; fr[yi:yi + h, xi:xi + w] = reg.astype(np.uint8)
        cv2.rectangle(fr, (xi + 1, yi + 1), (xi + w - 2, yi + h - 2), tuple(int(v * p + (1 - p) * b) for v, b in zip(self.LINE[::-1], self.BG[::-1])), 1, cv2.LINE_AA) if False else None
        return yi, xi
    def frame(self, t, k):
        fr = self.bgimg.copy()
        # header
        p = e_expo(lin(t, 0.0, 0.7)); put(fr, spr("Q3 Performance", "spacegrotesk-700", 70, self.TEXT, -0.01), 80 + spr("Q3 Performance", "spacegrotesk-700", 70, self.TEXT, -0.01).shape[1] / 2 - 20, 150 + (1 - p) * 30, alpha=p)
        put(fr, spr("Oct 2026  ·  All regions", "inter-500", 32, self.MUTE), 80 + 190, 220, alpha=p)
        # LIVE chip
        pulse = 0.5 + 0.5 * math.sin(t * 6); chip = rrect_mask(54, 150, 27)[..., None]; reg = fr[120:174, W - 230:W - 80].astype(np.float32)
        reg[:] = reg * (1 - chip * 0.9 * p) + np.array(self.CARD[::-1], np.float32) * chip * 0.9 * p; fr[120:174, W - 230:W - 80] = reg.astype(np.uint8)
        cv2.circle(fr, (W - 200, 147), int(8 + 2 * pulse), self.MINT[::-1], -1, cv2.LINE_AA); put(fr, spr("LIVE", "spacegrotesk-700", 28, self.TEXT, 0.12), W - 140, 147, alpha=p)
        # KPI card
        p1 = e_expo(lin(t, 0.25, 1.1)); self.card(fr, 60, 290, W - 120, 420, p1)
        if p1 > 0.2:
            v = int(248 * e_out(lin(t, 0.6, 2.2), 3)); put(fr, spr(f"+{v}%", "spacegrotesk-700", 250, self.TEXT, -0.03), 60 + 80 + spr(f"+{v}%", "spacegrotesk-700", 250, self.TEXT, -0.03).shape[1] / 2 - 40, 520 + (1 - p1) * 90, alpha=p1)
            put(fr, spr("REVENUE GROWTH  ·  YoY", "spacegrotesk-500", 32, self.MUTE, 0.18), 60 + 80 + 280, 360 + (1 - p1) * 90, alpha=p1)
            ch = rrect_mask(52, 210, 26)[..., None]; yb = int(620 + (1 - p1) * 90); reg = fr[yb:yb + 52, 140:350].astype(np.float32)
            reg[:] = reg * (1 - ch * 0.9) + np.array((16, 70, 52)[::-1], np.float32) * ch * 0.9; fr[yb:yb + 52, 140:350] = reg.astype(np.uint8)
            put(fr, spr("+12.4% MoM", "spacegrotesk-700", 28, self.MINT, 0.04), 245, yb + 26, alpha=p1)
        # line chart card
        p2 = e_expo(lin(t, 0.55, 1.4)); self.card(fr, 60, 760, W - 120, 560, p2)
        if p2 > 0.3:
            x0, x1, y0, y1 = 130, W - 130, 870, 1250; n = len(self.data); prog = e_io(lin(t, 1.0, 3.0))
            pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * (v - 30) / 130.0) for i, v in enumerate(self.data)]
            full = np.array(pts, np.float32); cnt = prog * (n - 1); i = int(cnt); u = cnt - i
            vis = [tuple(p) for p in pts[:i + 1]]
            if i < n - 1: vis.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u))
            for gy in range(4): cv2.line(fr, (x0, y0 + gy * 127), (x1, y0 + gy * 127), self.LINE[::-1], 1, cv2.LINE_AA)
            if len(vis) > 1:
                poly = np.array(vis + [(vis[-1][0], y1), (vis[0][0], y1)], np.int32); fill = fr.copy(); cv2.fillPoly(fill, [poly], self.BLUE[::-1]); fr = cv2.addWeighted(fr, 0.82, fill, 0.18, 0)
                cv2.polylines(fr, [np.array(vis, np.int32)], False, self.BLUE[::-1], 6, cv2.LINE_AA)
                cv2.circle(fr, (int(vis[-1][0]), int(vis[-1][1])), 14, self.TEXT[::-1], -1, cv2.LINE_AA); cv2.circle(fr, (int(vis[-1][0]), int(vis[-1][1])), 22, self.BLUE[::-1], 3, cv2.LINE_AA)
            put(fr, spr("Monthly revenue", "spacegrotesk-700", 36, self.TEXT), 130 + 140, 815, alpha=p2)
        # bars card
        p3 = e_expo(lin(t, 0.85, 1.7)); self.card(fr, 60, 1370, W - 120, 440, p3)
        if p3 > 0.3:
            bx0, by1 = 140, 1760; bw = 90; gap = (W - 280 - bw * 7) / 6
            for i, v in enumerate(self.bars):
                gp = e_expo(lin(t, 1.5 + i * 0.1, 2.5 + i * 0.1)); hh = int(v * 2.6 * gp); x = int(bx0 + i * (bw + gap))
                col = self.MINT if i == 6 else self.BLUE; cv2.rectangle(fr, (x, by1 - hh), (x + bw, by1), tuple(int(c * (1.0 if i == 6 else 0.75)) for c in col[::-1]), -1)
            put(fr, spr("Weekly signups", "spacegrotesk-700", 36, self.TEXT), 130 + 130, 1425, alpha=p3)
        if t > 4.5: fr = to8(fr.astype(np.float32) * (1 - e_in(lin(t, 4.5, 5.0), 2)))
        return fr
