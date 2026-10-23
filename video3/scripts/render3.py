"""Render one short (silent 1080x1920 @ 120 fps).  usage: render3.py --short 1 --out work/s1_silent.mp4 [--t0 --t1] [-j 4] [--crf 17]"""
import sys, os, json, argparse, subprocess, bisect, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from elements3 import *
import spec3

EDLALL = json.load(open(os.path.join(WORK, "edl.json")))

class Short:
    def __init__(self, idx):
        self.idx = idx; self.edl = EDLALL["shorts"][idx - 1]; self.seg = self.edl["segments"]
        self.O0 = [s["o0"] for s in self.seg]; self.total = self.edl["total"]
    def out2src(self, t):
        i = max(0, bisect.bisect_right(self.O0, t) - 1); s = self.seg[i]
        return s["s0"] + min(t - s["o0"], s["s1"] - s["s0"]), i

# ---------- static layers ----------
def _rounded(h, w, r):
    m = np.zeros((h * 4, w * 4), np.uint8)
    cv2.rectangle(m, (r * 4, 0), (w * 4 - r * 4, h * 4), 255, -1); cv2.rectangle(m, (0, r * 4), (w * 4, h * 4 - r * 4), 255, -1)
    for cx, cy in ((r, r), (w - r, r), (r, h - r), (w - r, h - r)): cv2.circle(m, (cx * 4, cy * 4), r * 4, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

_STATIC = {}
def static():
    if _STATIC: return _STATIC
    x0, y0, x1, y1 = SCR_CARD; cw, ch = x1 - x0, y1 - y0
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    base = np.array(NAVY[::-1], np.float32); top = np.array(NAVY2[::-1], np.float32)
    bg = base + (top - base) * (1 - yy) * 0.8 * np.ones((1, W, 1), np.float32)
    # card shadow
    sh = np.zeros((H, W), np.float32); sh[y0 + 14:y1 + 14, x0 + 4:x1 - 4] = 1; sh = cv2.GaussianBlur(sh, (0, 0), 22)
    bg = bg * (1 - 0.65 * sh[..., None])
    _STATIC["bg"] = bg.astype(np.uint8)
    m = _rounded(ch, cw, 26); _STATIC["mask"] = m
    er = cv2.erode(m, np.ones((3, 3), np.uint8)); _STATIC["border"] = np.clip(m - er, 0, 1)
    # webcam top/bottom feather
    ch2 = CAM_OUT[3] - CAM_OUT[1]; f = np.ones((ch2, 1), np.float32)
    f[:36, 0] = np.linspace(0, 1, 36) ** 1.5; f[-60:, 0] = np.linspace(1, 0, 60) ** 1.3
    _STATIC["feather"] = f
    return _STATIC

# ---------- zoom ----------
def zoom_state(keys, t):
    """keys: [(t_start, cx, cy, z, dur)] in screen-crop coords; eased moves between successive keyframes."""
    z, cx, cy = 1.0, SCRSRC[2] / 2, (SCRSRC[3] - SCRSRC[1]) / 2
    for (ts, kx, ky, kz, d) in keys:
        if t < ts: break
        a = ease_in_out_cubic((t - ts) / d)
        z, cx, cy = z + (kz - z) * a, cx + (kx - cx) * a, cy + (ky - cy) * a
        if a >= 1: z, cx, cy = kz, kx, ky
    return z, cx, cy

_mcache = {}
def load_matte(src_idx):
    k = src_idx // 3 * 3
    if k not in _mcache:
        m = cv2.imread(os.path.join(WORK, "mattes3", f"{k:06d}.png"), 0)
        if len(_mcache) > 30: _mcache.clear()
        _mcache[k] = None if m is None else m.astype(np.float32) / 255
    return _mcache[k]
def matte_at(src_t):
    f = src_t * SRC_FPS; k = int(f) // 3 * 3; a = load_matte(k); b = load_matte(k + 3)
    if a is None: return b
    if b is None: return a
    w = (f - k) / 3.0; return a * (1 - w) + b * w

def compose(src, t, sh, ctx):
    S = static(); fr = S["bg"].copy()
    z, zx, zy = zoom_state(ctx["zoom"], t)
    sx0, sy0, sx1, sy1 = SCRSRC; scr = src[sy0:sy1, sx0:sx1]
    sw, shh = sx1 - sx0, sy1 - sy0; cw_, ch_ = sw / z, shh / z
    ox = min(max(zx - cw_ / 2, 0), sw - cw_); oy = min(max(zy - ch_ / 2, 0), shh - ch_)
    cwid, chei = SCR_CARD[2] - SCR_CARD[0], SCR_CARD[3] - SCR_CARD[1]; s = cwid / cw_
    card = cv2.warpAffine(scr, np.array([[s, 0, -ox * s], [0, s, -oy * s]], np.float32), (cwid, chei), flags=cv2.INTER_CUBIC if z > 1.01 else cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = S["mask"][..., None]; reg = fr[SCR_CARD[1]:SCR_CARD[3], SCR_CARD[0]:SCR_CARD[2]]
    reg[:] = (card * m + reg * (1 - m)).astype(np.uint8)
    b = S["border"][..., None] * 0.55; reg[:] = (reg * (1 - b) + np.array([70, 62, 52], np.float32) * b).astype(np.uint8)
    ctx["scale"] = s
    ctx["map"] = lambda x, y: (SCR_CARD[0] + (x - ox) * s, SCR_CARD[1] + (y - sy0 - oy) * s)
    # webcam block
    cx0, cy0, cx1, cy1 = CAMSRC; cam = src[cy0:cy1, cx0:cx1]
    bx0, by0, bx1, by1 = CAM_OUT; bw, bh = bx1 - bx0, by1 - by0
    k = bw / (cx1 - cx0); ps = ctx["punch"](t)
    fcx, fcy = 330.0, 235.0; ocx, ocy = 478.0, 340.0
    M = np.array([[k * ps, 0, ocx - k * ps * fcx], [0, k * ps, ocy - k * ps * fcy]], np.float32)
    camo = cv2.warpAffine(cam, M, (bw, bh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    bl = cv2.GaussianBlur(camo, (0, 0), 1.4); camo = cv2.addWeighted(camo, 1.35, bl, -0.35, 0)
    behind = [e for e in ctx["els"] if e.kind == "behind" and e.active(t)]
    mat = None
    if behind:
        mm = matte_at(sh.out2src(t)[0])
        if mm is not None: mat = cv2.warpAffine(mm, M, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        mat = cv2.GaussianBlur(cv2.erode(mat, np.ones((3, 3), np.uint8)), (0, 0), 0.8) if mat is not None else None
    f = S["feather"][..., None]; breg = fr[by0:by1, bx0:bx1]
    if behind and mat is not None:
        sdim = max(min(1, (t - e.t0) / 0.35) * min(1, max(0, (e.t1 + 0.3 - t) / 0.3)) for e in behind)
        camdim = camo.astype(np.float32) * (1 - 0.5 * sdim)
        camwork = camdim * (1 - mat[..., None]) + camo.astype(np.float32) * mat[..., None]
    else:
        camwork = camo.astype(np.float32)
    breg[:] = (camwork * f + breg * (1 - f)).astype(np.uint8)
    # chrome: progress bar + part label
    fill_rect(fr, SCR_CARD[0], 936, SCR_CARD[2], 940, (44, 50, 62), 1)
    fill_rect(fr, SCR_CARD[0], 936, SCR_CARD[0] + (SCR_CARD[2] - SCR_CARD[0]) * clamp01(t / sh.total), 940, AMBER, 1)
    spr, o_x, o_y = sprite(f"PART {sh.idx}/3", 700, 28, SOFT, 0.16)
    blit(fr, spr, SCR_CARD[2] - 6 - (spr.shape[1] - o_x) - 20 + 0, 146 - o_y, a=0.9)
    # elements
    for e in ctx["els"]:
        if not e.active(t) or e.kind in ("hook", "behind"): continue
        (e.draw(fr, t, ctx) if e.kind == "ring" else e.draw(fr, t))
    for e in behind: e.draw(fr, t)
    if behind and mat is not None:
        breg = fr[by0:by1, bx0:bx1].astype(np.float32)
        fr[by0:by1, bx0:bx1] = (breg * (1 - mat[..., None]) + (camo.astype(np.float32) * f + S["bg"][by0:by1, bx0:bx1] * (1 - f)) * mat[..., None] + 0.5).astype(np.uint8)
    for e in ctx["els"]:
        if e.kind == "hook" and e.active(t): e.draw(fr, t)
    return fr

def make_ctx(sh):
    built = spec3.build(sh.idx, EDLALL)
    P = built["punches"]
    def punch(t):
        v = 1.0
        for (a, b, sc) in P:
            if a <= t < b: v = max(v, sc)
        return v
    return dict(els=built["elements"], zoom=built["zoom"], punch=punch)

def worker(args):
    idx, k0, k1, path, crf = args
    sh = Short(idx); ctx = make_ctx(sh)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", "1",
           "-x264-params", "keyint=240:min-keyint=240:scenecut=0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); cap = cv2.VideoCapture(SRC); last = -10; fr = None
    for k in range(k0, k1):
        t = k / FPS; s, _ = sh.out2src(t); i = int(round(s * SRC_FPS))
        if i != last:
            if i != last + 1: cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, fr0 = cap.read()
            if not ok: fr0 = np.zeros((SRC_H, SRC_W, 3), np.uint8)
            fr = fr0; last = i
        p.stdin.write(compose(fr, t, sh, ctx).tobytes())
    p.stdin.close(); p.wait(); return path

def grab(cap, sh, t):
    s, _ = sh.out2src(t); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(s * SRC_FPS))); ok, fr = cap.read(); return fr

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--short", type=int, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--t0", type=float, default=0); ap.add_argument("--t1", type=float, default=1e9)
    ap.add_argument("-j", type=int, default=4); ap.add_argument("--crf", type=int, default=17)
    a = ap.parse_args(); sh = Short(a.short)
    from multiprocessing import Pool
    k0, k1 = int(round(a.t0 * FPS)), int(round(min(a.t1, sh.total) * FPS))
    n = a.j * 3; bounds = np.linspace(k0, k1, n + 1).astype(int)
    tmp = os.path.join(WORK, f"chunks{a.short}"); os.makedirs(tmp, exist_ok=True)
    jobs = [(a.short, int(bounds[i]), int(bounds[i + 1]), os.path.join(tmp, f"c{i:03d}.mp4"), a.crf) for i in range(n)]
    t_start = time.time()
    with Pool(a.j) as pool:
        for i, r in enumerate(pool.imap(worker, jobs)): print(f"chunk {i + 1}/{n} done {time.time() - t_start:.0f}s", flush=True)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{j[3]}'\n" for j in jobs))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out])
    print("wrote", a.out, "frames", k1 - k0)
