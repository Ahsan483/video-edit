"""Render the silent edited video (frame-accurate compositing) + a timeline.json for the audio pass.
usage: render_video.py --mode sample|final [--out PATH]"""
import sys, os, json, argparse, subprocess, time, random
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec

SAMPLE_RANGES = [(0.0, 11.3), (11.9, 15.1), (29.3, 35.0)]
MIN_VISIBLE = 0.9          # drop overlays that would be visible for less than this (output seconds)
MARGIN = 72                # left/right text margin
DROP = 120                 # px the webcam eases down for behind-head text
PUNCH = 1.045              # jump-cut punch-in scale
IN_D, OUT_D = 0.5, 0.26

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["sample", "final"], required=True)
ap.add_argument("--out", default=None)
ap.add_argument("--limit", type=int, default=0, help="debug: stop after N output frames")
args = ap.parse_args()
ranges = SAMPLE_RANGES if args.mode == "sample" else [(0.0, 269.2)]
OUT = args.out or os.path.join(WORK, f"video_{args.mode}.mp4")
TL = os.path.join(WORK, f"timeline_{args.mode}.json")

silences = json.load(open(os.path.join(REPO, "data", "silences.json")))
TOTAL_SRC = 16154
kept = build_keep_frames(ranges, silences, TOTAL_SRC)
cm = CutMap(kept)
N = cm.n
DUR = N / FPS
print(f"{args.mode}: {N} frames = {DUR:.2f}s", flush=True)

# ---------------------------------------------------------------- helpers
def vis(t0, t1):
    if not cm.covered(t0, t1): return None
    a, b = cm.out_time(t0), cm.out_time(t1)
    return (a, b) if b - a >= MIN_VISIBLE else None

def accent_colors(text, accent):
    if not accent: return None
    i = text.find(accent)
    return {k: TEAL for k in range(i, i + len(accent))} if i >= 0 else None

def anim_alpha(t, a, b, tin=IN_D, tout=OUT_D):
    if t < a or t > b + tout: return 0.0
    x = out_cubic((t - a) / tin) if t < b else 1 - in_cubic((t - b) / tout)
    return x if t < b else max(x, 0)

sfx = []          # {"t": out seconds, "kind": ..., "gain": ...}

# matte loader
MDIR = os.path.join(WORK, "mattes")
_mcache = {}
def load_matte(fidx):
    if fidx in _mcache: return _mcache[fidx]
    p = os.path.join(MDIR, f"{fidx:06d}.png")
    m = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
    m = None if m is None else m.astype(np.float32) / 255
    if len(_mcache) > 8: _mcache.pop(next(iter(_mcache)))
    _mcache[fidx] = m
    return m

# ---------------------------------------------------------------- overlays
class Words:
    """Word-by-word reveal in one line (or two), used by top/bottom statements."""
    def __init__(self, text, role, size, accent, max_w, shadow=0.0, upper=False):
        self.lines = []
        words = text.split(" ")
        def width(s): return text_width(s, role, size, upper)
        lines = [text]
        if width(text) > max_w:
            h = len(words) // 2
            lines = [" ".join(words[:h]), " ".join(words[h:])]
        self.size = size
        self.sprites = []     # (sprite, x_offset, y_offset, word_index)
        wi = 0
        lh = int(size * TYPE[role][3] * 1.12)
        for li, ln in enumerate(lines):
            c = accent_colors(ln, accent)
            for w_i, w in enumerate(ln.split(" ")):
                start = len(" ".join(ln.split(" ")[:w_i])) + (1 if w_i else 0)
                xo = text_width(ln[:start], role, size, upper) if start else 0
                cc = {k - start: v for k, v in (c or {}).items() if start <= k < start + len(w)} or None
                spr = text_sprite(w, role, WHITE, size=size, shadow=shadow, upper=upper, colors=cc)
                self.sprites.append((spr, xo, li * lh, wi)); wi += 1
        self.nwords = wi
        self.height = lh * len(lines)

    def draw(self, frame, x, y, t, a, b, clip=None):
        for spr, xo, yo, wi in self.sprites:
            ta = a + min(wi * 0.07, 0.35)
            k = out_cubic((t - ta) / 0.34)
            if t > b: k *= 1 - in_cubic((t - b) / OUT_D)
            if k <= 0: continue
            rise = (1 - out_quart((t - ta) / 0.42)) * 20
            blit(frame, spr, x + xo - spr.pad, y + yo - spr.cap_top + rise, k, clip=clip)

class Eyebrow:
    def __init__(self, text, a, b):
        self.a, self.b = a, b
        self.spr = text_sprite(text, "label", TEAL, upper=True)
    def draw(self, frame, t):
        k = anim_alpha(t, self.a, self.b, 0.4, 0.2)
        if k <= 0: return
        ek = out_quart((t - self.a) / 0.45)
        rule = int(44 * ek)
        y = 196
        if rule > 0:
            ov = frame[y - 2:y + 1, MARGIN:MARGIN + rule].astype(np.float32)
            frame[y - 2:y + 1, MARGIN:MARGIN + rule] = (ov * (1 - k) + np.array(TEAL[::-1], np.float32) * k).astype(np.uint8)
        blit(frame, self.spr, MARGIN + 62 + (1 - ek) * 16 - self.spr.pad, y - 1 - self.spr.baseline * 0.62, k)

class Statement:
    """top / bottom statement, left aligned at MARGIN."""
    def __init__(self, text, accent, a, b, where):
        self.a, self.b, self.where = a, b, where
        if where == "top":
            role, size = "statement", fit_size(text, "statement", W - 2 * MARGIN, 84)
            self.w = Words(text, role, size, accent, W - 2 * MARGIN)
        else:
            role = "caption"; size = fit_size(text, role, W - 2 * MARGIN, 58)
            if size < 48: size = 54
            self.w = Words(text, role, size, accent, W - 2 * MARGIN)
    def draw(self, frame, t):
        if t < self.a or t > self.b + OUT_D: return
        nl = len({yo for _, _, yo, _ in self.w.sprites})
        lh = self.w.height // nl
        if self.where == "top":
            top_y = 150 - 0.73 * self.w.size - (nl - 1) * lh      # last line's baseline sits at y=150
        else:
            top_y = 1676
        self.w.draw(frame, MARGIN, top_y, t, self.a, self.b)

def scene_crown_rel(t0, t1):
    """Median top of the person matte (cam-band px) over a scene -> where the head really is in that scene."""
    tops = []
    f = int(t0 * FPS) // 3 * 3
    while f <= int(t1 * FPS):
        m = load_matte(f)
        if m is not None:
            rows = np.where((m > 0.5).sum(1) >= 20)[0]
            if len(rows): tops.append(rows[0] * 2.0)
        f += 12
    return float(np.median(tops)) if tops else CROWN_Y - CAM_Y0

class Behind:
    def __init__(self, text, accent, a, b, crown_rel):
        self.a, self.b = a, b
        self.size = fit_size(text, "display", W - 2 * 70, 190, upper=True)
        self.spr = text_sprite(text, "display", WHITE, size=self.size, upper=True, colors=accent_colors(text.upper(), accent))
        # baseline sits 28px below the crown of the (dropped) head, in cam-band coordinates
        self.base_rel = crown_rel + DROP + 8      # overlap ~8 px: the crown tucks over the lower edge of the letters
        self.x = (W - self.spr.w) // 2
        self.y = CAM_Y0 + self.base_rel - self.spr.baseline
    def alpha(self, t): return anim_alpha(t, self.a, self.b, 0.5, 0.3)
    def draw(self, frame, t, matte_full):
        k = self.alpha(t)
        if k <= 0: return
        rise = (1 - out_quart((t - self.a) / 0.55)) * self.spr.h * 0.6 if t < self.a + 0.55 else 0
        box = (0, max(int(self.y), CAM_Y0), W, int(self.y + self.spr.h))
        blit(frame, self.spr, self.x, self.y + rise, k, clip=box, behind=matte_full, behind_oy=CAM_Y0)

class Side:
    def __init__(self, side, lines, a, b):
        self.a, self.b, self.side = a, b, side
        self.items = []
        maxw = 215 if side == "l" else 260
        col = {"white": WHITE, "soft": SOFT, "teal": TEAL}
        y = (CROWN_Y + 28) if side == "l" else (CROWN_Y + 95)
        for lt, text, size, c in lines:
            size = fit_size(text, "side", maxw, size, upper=text.isupper() or False)
            spr = text_sprite(text, "side", col[c], size=size, shadow=0.55)
            self.items.append((lt, spr, y))
            y += int(size * 0.98) + 12
    def draw(self, frame, t, ts_map):
        for lt, spr, y in self.items:
            ta = ts_map(lt)
            k = out_cubic((t - ta) / 0.4)
            if t > self.b: k *= 1 - in_cubic((t - self.b) / OUT_D)
            if k <= 0: continue
            rise = (1 - out_quart((t - ta) / 0.45)) * 16
            x = 52 if self.side == "l" else W - 52 - spr.w + spr.pad
            blit(frame, spr, x - (spr.pad if self.side == "l" else 0), y - spr.cap_top + rise, k, clip=(0, CAM_Y0, W, CAM_Y1))

class Typed:
    def __init__(self, text, a, b, seed=7):
        self.a, self.b, self.text = a, b, text
        self.spr_full = None
        rnd = random.Random(seed)
        t = a + 0.3
        self.times = []
        for ch in text:
            self.times.append(t)
            t += rnd.uniform(0.045, 0.095) + (0.05 if ch == " " else 0)
        self.sprs = [text_sprite(text[:i + 1], "mono", WHITE) if i >= 0 else None for i in range(len(text))]
        self.cursor_x = [text_width(text[:i + 1], "mono") for i in range(len(text))]
        for i, tt in enumerate(self.times):
            if text[i] != " ": sfx.append({"t": tt, "kind": "key", "gain": 1.0})
    def draw(self, frame, t):
        k = anim_alpha(t, self.a, self.b, 0.25, 0.25)
        if k <= 0: return
        n = sum(1 for x in self.times if x <= t)
        y = 1690
        if n:
            spr = self.sprs[n - 1]
            blit(frame, spr, MARGIN - spr.pad, y - spr.cap_top - 10, k)
        cx = MARGIN + (self.cursor_x[n - 1] if n else 0) + 6
        blink = 1.0 if (n < len(self.text) and True) or int((t - self.a) * 2.2) % 2 == 0 else 0.0
        if blink:
            x0, x1, y0, y1 = int(cx), int(cx) + 18, y - 38, y + 8
            reg = frame[y0:y1, x0:x1].astype(np.float32)
            frame[y0:y1, x0:x1] = (reg * (1 - k) + np.array(TEAL[::-1], np.float32) * k).astype(np.uint8)

# ---------------------------------------------------------------- build overlays
ts_map = cm.out_time
behinds, tops, bottoms, sides, typeds, eyebrows = [], [], [], [], [], []
for t0, t1, text, acc in spec.BEHIND:
    v = vis(t0, t1)
    if v: behinds.append(Behind(text, acc, *v, scene_crown_rel(t0, t1))); sfx.append({"t": v[0] - 0.03, "kind": "whoosh", "gain": 1.0})
for t0, t1, text, acc in spec.TOP:
    v = vis(t0, t1)
    if v: tops.append(Statement(text, acc, v[0], v[1], "top")); sfx.append({"t": v[0] - 0.02, "kind": "whoosh", "gain": 0.55})
for t0, t1, text, acc in spec.BOTTOM:
    v = vis(t0, t1)
    if v: bottoms.append(Statement(text, acc, v[0], v[1], "bottom"))
for t0, t1, side, lines in spec.SIDE:
    v = vis(t0, t1)
    if v: sides.append(Side(side, lines, *v))
for t0, t1, text in spec.TYPED:
    v = vis(t0, t1)
    if v: typeds.append(Typed(text, *v))
for t0, t1, text in spec.EYEBROW:
    v = vis(t0, t1)
    if v: eyebrows.append(Eyebrow(text, *v))
for c in spec.CLICKS:
    if cm.covered(c - 0.02, c + 0.02): sfx.append({"t": cm.out_time(c) - 0.01, "kind": "click", "gain": 1.0})

# webcam drop envelope (out seconds -> px)
def drop_at(t):
    d = 0.0
    for b in behinds:
        up = in_out_cubic((t - (b.a - 0.55)) / 0.55)
        dn = 1 - in_out_cubic((t - (b.b + 0.05)) / 0.5)
        d = max(d, min(up, dn))
    return d * DROP

# UI zoom keyframes (out time)
def build_zoom_keys():
    keys = []   # (t, cx, cy, ls)
    ident = (W / 2, SCR_H / 2, 0.0)
    prev_t1, prev_state = None, None
    zs = []
    for t0, t1, cx, cy, s in spec.ZOOMS:
        v = vis(t0, t1)
        if v: zs.append((v[0], v[1], cx, cy, np.log(s)))
    for i, (a, b, cx, cy, ls) in enumerate(zs):
        tgt = (cx, cy, ls)
        if prev_t1 is not None and a - prev_t1 < 0.5:
            keys.append((a, *prev_state)); keys.append((a + 0.6, *tgt))
        else:
            if prev_t1 is not None:
                keys.append((prev_t1, *prev_state)); keys.append((prev_t1 + 0.6, *ident))
            keys.append((max(a - 0.0, 0), *ident)); keys.append((a + 0.6, *tgt))
        keys.append((max(b - 0.0, a + 0.6), *tgt))
        prev_t1, prev_state = max(b, a + 0.6), tgt
    if prev_t1 is not None:
        keys.append((prev_t1, *prev_state)); keys.append((prev_t1 + 0.6, *ident))
    return keys
ZK = build_zoom_keys()
ZK_T = [k[0] for k in ZK]
for z in spec.ZOOMS:
    if z[0] in (28.8, 74.6, 121.4, 236.0):
        v = vis(z[0], z[1])
        if v: sfx.append({"t": v[0] + 0.05, "kind": "swish", "gain": 0.6})

def zoom_at(t):
    if not ZK or t <= ZK[0][0] or t >= ZK[-1][0]:
        return None
    i = int(np.searchsorted(ZK_T, t, side="right")) - 1
    (t0, x0, y0, s0), (t1, x1, y1, s1) = ZK[i], ZK[min(i + 1, len(ZK) - 1)]
    if t1 - t0 < 1e-6: return (x0, y0, np.exp(s0))
    e = in_out_cubic((t - t0) / (t1 - t0))
    ls = s0 + (s1 - s0) * e
    if abs(ls) < 1e-3 and abs(s0) < 1e-3 and abs(s1) < 1e-3: return None
    return (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, np.exp(ls))

# jump-cut punch-in schedule (toggle on cuts that removed >= 0.25 s, at least 2.5 s apart)
punch = np.ones(N, np.float32)
state, last_t = 1.0, -9
cut_sfx = []
for i in range(1, N):
    gap = (kept[i] - kept[i - 1] - 1) / FPS
    if gap >= 0.25 and i / FPS - last_t > 2.5:
        state = PUNCH if state == 1.0 else 1.0
        last_t = i / FPS
    punch[i] = state

def matte_at(sidx):
    f0 = sidx // 3 * 3
    m0, m1 = load_matte(f0), load_matte(f0 + 3)
    if m0 is None: return m1
    if m1 is None: return m0
    w = (sidx - f0) / 3
    return m0 * (1 - w) + m1 * w

# side-dim gradients
xs = np.arange(W, dtype=np.float32)
sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
side_dim = {"r": 1 - 0.42 * sm((xs - 700) / 260), "l": 1 - 0.42 * sm((330 - xs) / 260)}
ys = np.arange(CAM_H, dtype=np.float32)
vwin = sm((ys - 20) / 60) * (1 - sm((ys - 520) / 120))
PX, PY = 540.0, 300.0

# ---------------------------------------------------------------- I/O
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", f"{ranges[-1][1] + 0.5:.2f}", "-an",
                        "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=bgr24", "-f", "rawvideo", "-"],
                       stdout=subprocess.PIPE, bufsize=W * H * 3 * 3)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-profile:v", "high", "-level", "5.1",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", str(FPS),
                        "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
FB = W * H * 3
kept_set = {int(k): i for i, k in enumerate(kept)}
last_src = int(kept[-1])
t_start = time.time()
sidx = 0
n_out = 0
while sidx <= last_src:
    buf = dec.stdout.read(FB)
    if len(buf) < FB: break
    if sidx in kept_set:
        t = n_out / FPS
        frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        # ---- screen band: feature zoom
        z = zoom_at(t)
        if z is not None:
            cx, cy, s = z
            cw, ch = W / s, SCR_H / s
            x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), SCR_H - ch)
            M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
            band = frame[SCR_Y0:SCR_Y1]
            zb = cv2.warpAffine(band, M, (W, SCR_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            if s > 1.3:
                bl = cv2.GaussianBlur(zb, (0, 0), 1.1)
                zb = cv2.addWeighted(zb, 1.45, bl, -0.45, 0)
            frame[SCR_Y0:SCR_Y1] = zb
        # ---- webcam band: drop + punch
        D = drop_at(t); sc = float(punch[n_out])
        cam = frame[CAM_Y0:CAM_Y1]
        need_matte = any(b.alpha(t) > 0 for b in behinds)
        matte_full = None
        if D > 0.5 or sc != 1.0:
            M = np.float32([[sc, 0, (1 - sc) * PX], [0, sc, (1 - sc) * PY + D]])
            cam = cv2.warpAffine(cam, M, (W, CAM_H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            if D > 0.5:
                n = int(D + 40)
                strip = cv2.GaussianBlur(cam[:n], (0, 0), 18)
                wgt = np.clip((n - np.arange(n)) / 40.0, 0, 1)[:, None, None].astype(np.float32)
                cam[:n] = (strip * wgt + cam[:n] * (1 - wgt)).astype(np.uint8)
        else:
            M = np.float32([[1, 0, 0], [0, 1, 0]])
        if need_matte:
            mh = matte_at(int(sidx))
            if mh is not None:
                Ms = np.float32([[M[0, 0] * 2, 0, M[0, 2]], [0, M[1, 1] * 2, M[1, 2]]])
                matte_full = cv2.warpAffine(mh, Ms, (W, CAM_H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        # background dim behind text
        a_b = max([b.alpha(t) for b in behinds] + [0])
        if a_b > 0 and matte_full is not None:
            camf = cam.astype(np.float32)
            camf *= (1 - 0.34 * a_b * (1 - matte_full))[..., None]
            cam = np.clip(camf, 0, 255).astype(np.uint8)
        for sd in sides:
            ak = anim_alpha(t, sd.a, sd.b, 0.4, OUT_D)
            if ak > 0:
                g = 1 - ak * (1 - side_dim[sd.side])[None, :] * vwin[:, None]
                cam = np.clip(cam.astype(np.float32) * g[..., None], 0, 255).astype(np.uint8)
        frame[CAM_Y0:CAM_Y1] = cam
        # ---- typography
        if matte_full is not None:
            for b in behinds: b.draw(frame, t, matte_full)
        for sd in sides: sd.draw(frame, t, ts_map) if (sd.a - 0.5 <= t <= sd.b + 0.5) else None
        for e in eyebrows: e.draw(frame, t)
        for s_ in tops: s_.draw(frame, t)
        for s_ in bottoms: s_.draw(frame, t)
        for ty in typeds: ty.draw(frame, t)
        # ---- head / tail fade
        f = min(1.0, n_out / 8.0, (N - 1 - n_out) / 18.0)
        if f < 1.0: frame = (frame.astype(np.float32) * f).astype(np.uint8)
        enc.stdin.write(frame.tobytes())
        n_out += 1
        if n_out % 300 == 0:
            el = time.time() - t_start
            print(f"  {n_out}/{N} frames  {n_out / el:.1f} fps  eta {(N - n_out) / (n_out / el) / 60:.1f} min", flush=True)
        if args.limit and n_out >= args.limit: break
    sidx += 1
enc.stdin.close(); enc.wait(); dec.kill()
json.dump({"mode": args.mode, "fps": FPS, "frames": n_out, "kept": [int(k) for k in kept], "sfx": sorted(sfx, key=lambda e: e["t"])},
          open(TL, "w"))
print("done", OUT, n_out, "frames", f"{time.time() - t_start:.0f}s", flush=True)
