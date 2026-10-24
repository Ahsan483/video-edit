from lib import *

# ================================================================= 01 NEON NOIR
class T01:
    name = "01_neon_noir"
    def __init__(self):
        self.rs = np.random.RandomState(7)
        self.flick = {i: self.rs.rand(40) for i in range(12)}
        self.bg = vgrad((10, 5, 22), (4, 2, 10)).astype(np.float32)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt(((xx - W / 2) / 800) ** 2 + ((yy - H * 0.5) / 1100) ** 2)
        self.bg *= np.clip(1.15 - d, 0.25, 1)[..., None]
        self.tile = noise_tile(3)
    def neon_text(self, txt, size, col, y, t, t0, idx0):
        f = np.zeros((H, W, 3), np.float32); core = np.zeros((H, W, 3), np.float32)
        lt = t - t0
        if lt < 0: return f, core
        fl = self.flick[idx0]; step = int(lt * 24)
        if lt < 1.0:
            on = 1.0 if (step >= 38 or fl[min(step, 39)] > 0.55 + 0.4 * (1 - lt)) else 0.12
            al = on * (0.55 + 0.45 * e_out(lt))
        else: al = min(1.0, 1.0 - 0.06 * abs(math.sin(lt * 31)) * (1 if lt < 4.4 else 0))
        put(f, spr(txt, "unbounded", size, col, -0.02), W / 2, y, alpha=al)
        put(core, spr(txt, "unbounded", size, (255, 255, 255), -0.02, stroke=0), W / 2, y, alpha=al * 0.85)
        return f, core
    def frame(self, t, k):
        fr = self.bg.copy()
        # perspective floor lines (retro-wave)
        horizon = 1180; lay = np.zeros((H, W, 3), np.float32)
        for i in range(-12, 13):
            x_far = W / 2 + i * 38; x_near = W / 2 + i * 190
            cv2.line(lay, (int(x_far), horizon), (int(x_near), H), (170, 40, 255), 2, cv2.LINE_AA)
        for j in range(14):
            p = ((j + (t * 0.6) % 1.0) / 14.0) ** 2.2; y = horizon + p * (H - horizon)
            cv2.line(lay, (0, int(y)), (W, int(y)), (170, 40, 255), 2, cv2.LINE_AA)
        fl = e_out(lin(t, 0.2, 1.4)) * 0.75
        lay[:horizon] = 0; lay *= np.clip((np.linspace(0, 1, H)[:, None, None] - horizon / H) * 4, 0, 1) * fl
        # sun disc
        sun = np.zeros((H, W, 3), np.float32); cv2.circle(sun, (W // 2, horizon - 20), 190, (90, 120, 255), -1, cv2.LINE_AA)
        for r in range(0, 190, 26): cv2.rectangle(sun, (0, horizon - 20 - 190 + r + 100 - 6 + (r // 26) * 2), (W, horizon - 20 - 190 + r + 100 + (r // 26) * 5), (0, 0, 0), -1)
        sun[horizon - 20:] = 0; sun *= e_out(lin(t, 0.1, 1.2)) * 0.9
        fr += sun * 0.55 + lay
        # neon words
        g = np.zeros((H, W, 3), np.float32); core = np.zeros((H, W, 3), np.float32)
        for (txt, col, y, t0, ix) in (("NIGHT", (255, 45, 175), 560, 0.35, 0), ("SHIFT", (30, 150, 255), 760, 0.85, 1)):
            a, c = self.neon_text(txt, 205, col, y, t, t0, ix); g += a; core += c
        fr = glow(fr, g, 1.0) + core * 0.65
        # frame border draw-on
        bd = np.zeros((H, W, 3), np.float32); p = e_io(lin(t, 1.2, 2.6)); per = 2 * (W - 160) + 2 * (H - 160)
        pts = [(80, 80), (W - 80, 80), (W - 80, H - 80), (80, H - 80), (80, 80)]; need = p * per; acc = 0
        for (a, b) in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); u = cl((need - acc) / L); acc += L
            if u > 0: cv2.line(bd, a, (int(a[0] + (b[0] - a[0]) * u), int(a[1] + (b[1] - a[1]) * u)), (255, 170, 40), 3, cv2.LINE_AA)
        fr = glow(fr, bd, 0.6, (4, 14, 40))
        # sub copy
        s = spr("OPEN 24/7  ·  CITY LIGHTS", "spacegrotesk-500", 34, (255, 255, 255), 0.3); put_fr = np.zeros((H, W, 3), np.uint8)
        put(put_fr, s, W / 2, 940, alpha=e_out(lin(t, 2.0, 2.8)) * 0.85); fr += put_fr.astype(np.float32) * 0.9
        # exit pulse
        if t > 4.5: fr *= 1 - 0.55 * e_in(lin(t, 4.5, 5.0), 2)
        fr = grain(fr, 3.0, k, self.tile)
        return to8(fr)

# ================================================================= 02 SWISS GRID
class T02:
    name = "02_swiss_grid"
    INK = (18, 18, 18); PAPER = (238, 236, 230); RED = (226, 48, 36)
    def frame(self, t, k):
        fr = np.zeros((H, W, 3), np.uint8); fr[:] = np.array(self.PAPER[::-1], np.uint8)
        col, M = 6, 60; cw = (W - 2 * M) / col
        # grid lines draw in
        gp = e_expo(lin(t, 0.0, 0.9))
        for i in range(col + 1):
            x = int(M + i * cw); rect(fr, x, M, x + 1, M + (H - 2 * M) * gp, (200, 197, 190))
        for j in range(0, 13):
            y = int(M + j * (H - 2 * M) / 12); rect(fr, M, y, M + (W - 2 * M) * gp, y + 1, (200, 197, 190))
        # red disc slides on grid
        dx = mix(M + cw * 5.5, M + cw * 3.5, e_expo(lin(t, 0.4, 1.4))) if t < 3.2 else mix(M + cw * 3.5, M + cw * 5.5, e_io(lin(t, 3.2, 4.2)))
        r = 150 * e_back(lin(t, 0.3, 1.0))
        cv2.circle(fr, (int(dx), 560), int(max(r, 1)), self.RED[::-1], -1, cv2.LINE_AA)
        # big words slide in from left under masks
        lines = [("Design", 470), ("is", 640), ("Every-", 830), ("thing.", 1040)]
        sizes = {"Design": 230, "is": 120, "Every-": 230, "thing.": 230}
        for i, (w, y) in enumerate(lines):
            s = spr(w, "inter-800", sizes[w], self.INK, -0.045); p = e_expo(lin(t, 0.5 + i * 0.16, 1.3 + i * 0.16))
            x = M - int(sizes[w] * 0.3) + s.shape[1] / 2 - (1 - p) * (s.shape[1] + 120)
            clipx = (M, 0, W - M, H); put(fr, s, x, y, clip=clipx)
        # vertical year
        s = spr("2026", "spacegrotesk-700", 64, self.INK, 0.12); p = e_expo(lin(t, 1.3, 2.0))
        put(fr, s, W - M - 40, 1300 - (1 - p) * 120, rot=90, alpha=p)
        # captions
        for i, (txt, y) in enumerate((("A manifesto on", 1330), ("clarity, rhythm and grid.", 1380))):
            s = spr(txt, "inter-500", 38, self.INK, 0.0); p = e_expo(lin(t, 1.6 + i * 0.15, 2.3 + i * 0.15))
            put(fr, s, M + s.shape[1] / 2 - 18, y + (1 - p) * 30, alpha=p, clip=(0, y - 40, W, y + 40))
        # index numerals
        for i, n in enumerate(("01", "02", "03")):
            s = spr(n, "spacegrotesk-700", 44, self.RED if i == 0 else self.INK, 0.05); p = e_expo(lin(t, 2.2 + i * 0.12, 2.8 + i * 0.12))
            put(fr, s, M + 40 + i * 140, 1620, alpha=p)
        rect(fr, M, 1560, M + (W - 2 * M) * e_expo(lin(t, 2.0, 2.9)), 1564, self.INK)
        # exit wipe (red bar sweeps up)
        if t > 4.3:
            p = e_io(lin(t, 4.3, 4.95)); rect(fr, 0, H * (1 - p), W, H, self.RED)
        return fr

# ================================================================= 03 LIQUID GRADIENT
class T03:
    name = "03_liquid_gradient"
    def __init__(self):
        self.tile = noise_tile(5); self.cache = {}
    def bgf(self, t):
        h, w = 480, 270; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); xx /= w; yy /= h
        base = np.zeros((h, w, 3), np.float32); base[:] = (60, 22, 70)[::-1]
        blobs = [((255, 175, 120), 0.25 + 0.2 * math.sin(t * 0.9), 0.2 + 0.1 * math.cos(t * 0.7), 0.55),
                 ((255, 90, 150), 0.8 + 0.12 * math.cos(t * 0.8), 0.45 + 0.15 * math.sin(t * 1.1), 0.5),
                 ((120, 100, 255), 0.3 + 0.15 * math.sin(t * 1.2 + 1), 0.78 + 0.1 * math.cos(t * 0.9), 0.6),
                 ((90, 210, 235), 0.85 + 0.1 * math.sin(t * 0.7), 0.92 + 0.05 * math.sin(t), 0.45)]
        for c, bx, by, r in blobs:
            d = np.sqrt((xx - bx) ** 2 + ((yy - by) * 1.6) ** 2) / r; a = np.clip(1 - d, 0, 1) ** 1.6
            base = base * (1 - a[..., None] * 0.9) + np.array(c[::-1], np.float32) * a[..., None] * 0.9
        return cv2.resize(base, (W, H), interpolation=cv2.INTER_CUBIC)
    def word_sprite(self, txt, size, blur):
        key = (txt, size, blur)
        if key not in self.cache:
            s = spr(txt, "playfair-bi", size, (255, 255, 255), -0.01).copy()
            if blur > 0: s[..., 3] = cv2.GaussianBlur(s[..., 3], (0, 0), blur)
            self.cache[key] = s
        return self.cache[key]
    def frame(self, t, k):
        fr = self.bgf(t)
        # soft sheen sweep
        sweep = np.exp(-((np.arange(W, dtype=np.float32) - (-300 + 1700 * lin(t, 0.0, 5.0))) / 220) ** 2)[None, :, None] * 14
        fr = fr + sweep
        shadow = np.zeros((H, W, 3), np.uint8)
        for i, (w, y, size) in enumerate((("Soft", 640, 290), ("Launch", 900, 290))):
            p = e_expo(lin(t, 0.35 + i * 0.25, 1.5 + i * 0.25)); bl = [0, 2, 4, 8, 14][max(0, min(4, int((1 - p) * 5)))]
            s = self.word_sprite(w, size, bl); dy = (1 - p) * 70 + 8 * math.sin(t * 1.4 + i)
            sh = np.zeros((H, W, 3), np.uint8); put(sh, np.dstack([np.zeros_like(s[..., :3]), s[..., 3]]), W / 2 + 6, y + 14 + dy, alpha=0.5 * p)
            fr = fr - cv2.GaussianBlur(sh, (0, 0), 22).astype(np.float32) * 0.22
            tmp = to8(fr); put(tmp, s, W / 2, y + dy, alpha=p); fr = tmp.astype(np.float32)
        tmp = to8(fr)
        s = spr("COMING NOVEMBER", "spacegrotesk-500", 36, (255, 255, 255), 0.35); p = e_expo(lin(t, 1.9, 2.7))
        put(tmp, s, W / 2, 1130 + (1 - p) * 24, alpha=p * 0.9)
        # pill button grows in
        p = e_back(lin(t, 2.4, 3.2)); bw, bh = int(430 * max(p, 0.01)), 112
        if bw > 6:
            m = rrect_mask(bh, bw, 56); reg = tmp[1290:1290 + bh, W // 2 - bw // 2:W // 2 - bw // 2 + bw].astype(np.float32)
            reg[:] = reg * (1 - m[..., None] * 0.95) + 255 * m[..., None] * 0.95; tmp[1290:1290 + bh, W // 2 - bw // 2:W // 2 - bw // 2 + bw] = reg.astype(np.uint8)
            s = spr("Pre-order", "spacegrotesk-700", 42, (60, 22, 70), 0.02); aa = e_out(lin(t, 2.8, 3.4)); put(tmp, s, W / 2 - 24, 1346, alpha=aa)
            ax = W // 2 + 96; cv2.arrowedLine(tmp, (ax, 1346), (ax + 44, 1346), (70, 22, 60), 4, cv2.LINE_AA, tipLength=0.45) if aa > 0.5 else None
        fr = grain(tmp.astype(np.float32), 4.0, k, self.tile)
        if t > 4.5: fr = fr * (1 - e_in(lin(t, 4.5, 5.0)) * 0.9) + 255 * e_in(lin(t, 4.5, 5.0)) * 0.9 * 0.0
        return to8(fr)

# ================================================================= 04 RETRO VHS
class T04:
    name = "04_retro_vhs"
    def __init__(self):
        self.rs = np.random.RandomState(11); self.tile = noise_tile(9)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / 700) ** 2 + ((yy - H / 2) / 1100) ** 2); self.vig = np.clip(1.15 - d ** 2 * 0.6, 0.35, 1)[..., None]
        self.scan = np.ones((H, 1, 1), np.float32); self.scan[::4] = 0.78; self.scan[1::4] = 0.9
    def scene(self, t):
        fr = vgrad((22, 40, 92), (10, 16, 46)).astype(np.float32)
        fr = to8(fr)
        # perspective color bars (top) like a tape test pattern
        cols = [(235, 235, 235), (235, 235, 20), (20, 235, 235), (20, 235, 20), (235, 20, 235), (235, 20, 20), (20, 20, 235)]
        bw = W // 7; p = e_out(lin(t, 0.0, 0.5))
        if t < 0.55:
            for i, c in enumerate(cols): rect(fr, i * bw, 0, (i + 1) * bw, int(H * 0.72 * p), c)
        # title
        glitch = 0.0
        s = spr("MEMORIES", "pixel", 118, (255, 246, 214), 0.0)
        a = e_out(lin(t, 0.55, 1.0)); put(fr, s, W / 2, 900, alpha=a)
        s2 = spr("A HOME VIDEO", "pixel", 40, (255, 210, 90), 0.1); put(fr, s2, W / 2, 1010, alpha=e_out(lin(t, 1.0, 1.4)))
        # HUD
        blink = (int(t * 2) % 2 == 0)
        put(fr, spr("PLAY", "pixel", 40, (255, 255, 255)), 190, 130, alpha=1); cv2.fillPoly(fr, [np.array([[60, 108], [60, 152], [96, 130]], np.int32)], (255, 255, 255))
        put(fr, spr("SP", "pixel", 40, (255, 255, 255)), W - 130, 130)
        put(fr, spr(f"0:0{min(int(t),5)}:{int((t % 1) * 24):02d}", "pixel", 36, (255, 255, 255)), 280, 1790)
        put(fr, spr("OCT 24 2026", "pixel", 36, (255, 210, 90)), W - 290, 1790)
        if blink: cv2.circle(fr, (W - 150, 205), 14, (30, 30, 235), -1, cv2.LINE_AA)
        put(fr, spr("REC", "pixel", 34, (255, 255, 255)), W - 270, 205)
        return fr
    def frame(self, t, k):
        fr = self.scene(t)
        rs = np.random.RandomState(k // 3)
        # glitch bursts at intro and ~2.2 s / 3.9 s
        g = 0.0
        for c in (0.55, 2.2, 3.9):
            if c <= t < c + 0.28: g = 1.0 - (t - c) / 0.28
        out = fr.astype(np.float32)
        if g > 0:
            for _ in range(int(10 * g) + 2):
                y = rs.randint(0, H - 60); hh = rs.randint(8, 90); sh = int(rs.randint(-90, 90) * g)
                out[y:y + hh] = np.roll(out[y:y + hh], sh, 1)
        # chromatic aberration
        ab = 5 + int(14 * g)
        out[..., 2] = np.roll(out[..., 2], ab, 1); out[..., 0] = np.roll(out[..., 0], -ab, 1)
        # tracking band rolling
        by = int((t * 420) % (H + 300)) - 150
        y0, y1 = max(by, 0), min(by + 90, H)
        if y1 > y0: out[y0:y1] = np.roll(out[y0:y1], 22, 1) * 1.15 + 16
        out = out * self.scan * self.vig + 6
        out = grain(out, 9.0, k, self.tile)
        if t > 4.6: out *= 1 - e_in(lin(t, 4.6, 5.0), 2)
        return to8(out)
