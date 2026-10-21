"""Render the edited picture (silent). usage:
  render_video.py --out output/x_silent.mp4 [--t0 S --t1 S] [-j 4] [--crf 16]
Timeline comes from edl.json (cuts) + spec.py (typography, zooms). Chunks render in parallel and are concat-copied."""
import sys, os, json, argparse, subprocess, bisect, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec

EDL = json.load(open(os.path.join(WORK, "edl.json")))
SEG = EDL["segments"]            # [{s0,s1,o0}] source seconds -> output seconds
O0 = [s["o0"] for s in SEG]
TOTAL = EDL["total"]

def out2src(t):
    i = max(0, bisect.bisect_right(O0, t) - 1); s = SEG[i]
    return s["s0"] + min(t - s["o0"], s["s1"] - s["s0"]), i

_matte_cache = {}
def load_matte(src_idx):
    k = src_idx // 3 * 3
    if k in _matte_cache: return _matte_cache[k]
    p = os.path.join(WORK, "mattes", f"{k:06d}.png")
    m = cv2.imread(p, 0)
    r = None if m is None else m.astype(np.float32) / 255
    if len(_matte_cache) > 40: _matte_cache.clear()
    _matte_cache[k] = r
    return r

def zoom_state(zooms, t):
    """Smoothly eased screen zoom: returns (z, cx, cy). zooms: list of (t0,t1,cx,cy,z,tin,tout)."""
    z, cx, cy = 1.0, W / 2, ZOOM_H / 2
    for (t0, t1, zx, zy, zz, tin, tout) in zooms:
        if t < t0 - 0.001 or t > t1 + tout: continue
        a = ease_in_out_cubic((t - t0) / tin) if t < t1 else 1 - ease_in_out_cubic((t - t1) / tout)
        z = 1 + (zz - 1) * a
        cx = W / 2 + (zx - W / 2) * a; cy = ZOOM_H / 2 + (zy - ZOOM_H / 2) * a
    return z, cx, cy

def apply_zoom(fr, z, cx, cy):
    if z <= 1.0005: return
    cw, ch = W / z, ZOOM_H / z
    x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), ZOOM_H - ch)
    M = np.array([[z, 0, -x0 * z], [0, z, -y0 * z]], np.float32)
    fr[:ZOOM_H] = cv2.warpAffine(fr[:ZOOM_H], M, (W, ZOOM_H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # soften the seam where the zoomed screen meets the static webcam/taskbar strip
    ramp = np.linspace(0, 0.9, 36, dtype=np.float32)[None, :, None].transpose(1, 0, 2)
    seg = fr[ZOOM_H - 36:ZOOM_H].astype(np.float32)
    fr[ZOOM_H - 36:ZOOM_H] = (seg + (np.array([20, 18, 15], np.float32) - seg) * ramp).astype(np.uint8)

_band_bg = None
def band_bg(full=False):
    global _band_bg
    x0, y0, x1, y1 = (0, 875, 1440, 1080) if full else BAND
    yy = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :]
    g = 0.0 + 0.0 * xx + yy * 0
    base = np.array(NAVY[::-1], np.float32)[None, None, :]; top = np.array(NAVY2[::-1], np.float32)[None, None, :]
    mix = (0.35 * (1 - yy) + 0.65 * (1 - xx) * 0.5)[..., None]
    _band_bg = (base + (top - base) * mix).astype(np.float32)
    return _band_bg

FULLCAM = (0, 0, 1440, 875)
def is_full(t):
    s, _ = out2src(t); return 30.7 <= s < 45.0

def compose(fr, t, ctx):
    """fr: source frame BGR (modified in place). ctx: dict(els, zooms, punch, matte)."""
    full = is_full(t)
    x0, y0, x1, y1 = FULLCAM if full else CAM
    # screen zoom
    if not full:
        z, cx, cy = zoom_state(ctx["zooms"], t); apply_zoom(fr, z, cx, cy)
    # navy band behind the typography (only where the source is pure black)
    bx0, by0, bx1, by1 = (0, 875, 1440, 1080) if full else BAND
    reg = fr[by0:by1, bx0:bx1]
    blk = (reg.max(2) < 14)
    if blk.mean() > 0.85:
        key = ("band", full)
        if key not in ctx: ctx[key] = band_bg(full)
        bg = ctx[key]
        reg[:] = np.where(blk[..., None], bg.astype(np.uint8), reg)
        # hairline between screen and band
        fill_rect(fr, bx0, by0, bx1, by0 + 1, (40, 46, 58), 0.8)
    cam = fr[y0:y1, x0:x1].copy()
    need = any(e.kind == "behind" and e.active(t) for e in ctx["els"])
    m = ctx["matte"](t) if need else None
    if m is not None and m.shape != cam.shape[:2]: m = cv2.resize(m, (cam.shape[1], cam.shape[0]), interpolation=cv2.INTER_LINEAR)
    if m is not None: m = cv2.GaussianBlur(cv2.erode(m, np.ones((3, 3), np.uint8)), (0, 0), 0.8)
    ps = ctx["punch"](t)
    if ps > 1.0005:
        pcx, pcy = (840, 480) if full else (279, 130)
        M = np.array([[ps, 0, (1 - ps) * pcx], [0, ps, (1 - ps) * pcy]], np.float32)
        cam = cv2.warpAffine(cam, M, (x1 - x0, y1 - y0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        if m is not None: m = cv2.warpAffine(m, M, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    fr[y0:y1, x0:x1] = cam
    behind = [e for e in ctx["els"] if e.kind == "behind" and e.active(t)]
    if behind and m is not None:
        # dim the room behind the creator while a giant keyword is on screen
        s = max(min(1, (t - e.t0) / 0.35) * min(1, max(0, (e.t1 + 0.28 - t) / 0.28)) for e in behind)
        s = max(s, 0.0)
        bgdim = cam.astype(np.float32) * (1 - 0.5 * s)
        fr[y0:y1, x0:x1] = (bgdim * (1 - m[..., None]) + cam.astype(np.float32) * m[..., None]).astype(np.uint8)
    for e in ctx["els"]:
        if e.kind == "card": continue
        if e.active(t): e.draw(fr, t)
    if behind and m is not None:
        reg = fr[y0:y1, x0:x1].astype(np.float32)
        fr[y0:y1, x0:x1] = (reg * (1 - m[..., None]) + cam.astype(np.float32) * m[..., None] + 0.5).astype(np.uint8)
    for e in ctx["els"]:
        if e.kind == "card" and e.active(t): e.draw(fr, t)
    return fr

def make_ctx():
    built = spec.build(EDL)
    punches = built["punches"]
    def punch(t):
        v = 1.0
        for (a, b, s) in punches:
            if a <= t < b: v = max(v, s)
        return v
    def matte(t):
        s, _ = out2src(t); return load_matte(int(round(s * FPS)))
    return dict(els=built["elements"], zooms=built["zooms"], punch=punch, matte=matte)

def grab(cap, t):
    s, _ = out2src(t); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(s * FPS))); ok, fr = cap.read(); return fr

def worker(args):
    k0, k1, path, crf = args
    ctx = make_ctx()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", "1",
           "-x264-params", "keyint=120:min-keyint=120:scenecut=0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
           path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(SRC60); last = -10
    for k in range(k0, k1):
        t = k / FPS
        s, _ = out2src(t); idx = int(round(s * FPS))
        if idx != last + 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, fr = cap.read()
        if not ok:
            fr = np.zeros((H, W, 3), np.uint8)
        last = idx
        p.stdin.write(compose(fr, t, ctx).tobytes())
    p.stdin.close(); p.wait()
    return path

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--t0", type=float, default=0); ap.add_argument("--t1", type=float, default=TOTAL)
    ap.add_argument("-j", type=int, default=4); ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    from multiprocessing import Pool
    k0, k1 = int(round(a.t0 * FPS)), int(round(min(a.t1, TOTAL) * FPS))
    n = a.j * 3; bounds = np.linspace(k0, k1, n + 1).astype(int)
    tmp = os.path.join(WORK, "chunks"); os.makedirs(tmp, exist_ok=True)
    jobs = [(int(bounds[i]), int(bounds[i + 1]), os.path.join(tmp, f"c{i:03d}.mp4"), a.crf) for i in range(n)]
    t_start = time.time()
    with Pool(a.j) as pool:
        for i, r in enumerate(pool.imap(worker, jobs)):
            print(f"chunk {i + 1}/{n} done  {time.time() - t_start:.0f}s", flush=True)
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out])
    print("wrote", a.out, "frames", k1 - k0)
