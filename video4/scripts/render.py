"""Render the picture (silent, 1080x1920 @ 120 fps).  usage: render.py --out work/silent.mp4 [--t0 --t1] [-j 4] [--crf 15]"""
import sys, os, json, argparse, subprocess, bisect, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import spec

EDL = json.load(open(os.path.join(WORK, "edl.json"))); SEG = EDL["segments"]; O0 = [s["o0"] for s in SEG]; TOTAL = EDL["total"]
def out2src(t):
    i = max(0, bisect.bisect_right(O0, t) - 1); s = SEG[i]
    return min(s["s0"] + (t - s["o0"]) * s["speed"], s["s1"]), i

# ---------- grade: soft filmic curve, warm highlights, gently lifted blacks ----------
def make_lut():
    x = np.linspace(0, 1, 256)
    s = x + 0.16 * (x - 0.5) * (1 - np.abs(2 * x - 1)) * 1.6          # mild S-curve
    s = 0.025 + s * 0.965                                               # lifted blacks / soft white
    hi = np.clip((x - 0.55) / 0.45, 0, 1)
    r = s * (1.02 + 0.03 * hi); g = s * 1.005; b = s * (0.965 - 0.03 * hi)
    lut = np.stack([b, g, r], 1)                                        # BGR
    return (np.clip(lut, 0, 1) * 255 + .5).astype(np.uint8).reshape(256, 1, 3)
LUT = make_lut()

_S = {}
def static():
    if _S: return _S
    x0, y0, x1, y1 = WIN; ww, wh = x1 - x0, y1 - y0
    m = np.zeros((wh * 4, ww * 4), np.uint8); r = 26
    cv2.rectangle(m, (r * 4, 0), (ww * 4 - r * 4, wh * 4), 255, -1); cv2.rectangle(m, (0, r * 4), (ww * 4, wh * 4 - r * 4), 255, -1)
    for cx, cy in ((r, r), (ww - r, r), (r, wh - r), (ww - r, wh - r)): cv2.circle(m, (cx * 4, cy * 4), r * 4, 255, -1)
    _S["mask"] = (cv2.resize(m, (ww, wh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)[..., None]
    er = cv2.erode(_S["mask"][..., 0], np.ones((3, 3), np.uint8)); _S["edge"] = np.clip(_S["mask"][..., 0] - er, 0, 1)[..., None]
    yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32); d = np.sqrt(((xx - ww / 2) / (ww / 2)) ** 2 + ((yy - wh * 0.46) / (wh * 0.56)) ** 2)
    _S["vig"] = (1 - 0.30 * np.clip(d - 0.55, 0, 1) ** 1.4)[..., None]
    sh = np.zeros((H, W), np.float32); sh[y0 + 22:y1 + 22, x0 + 6:x1 - 6] = 1; _S["shadow"] = cv2.GaussianBlur(sh, (0, 0), 30)[..., None]
    yv, xv = np.mgrid[0:H, 0:W].astype(np.float32); dd = np.sqrt(((xv - W / 2) / (W * 0.75)) ** 2 + ((yv - H * 0.45) / (H * 0.7)) ** 2)
    _S["bgvig"] = np.clip(1.08 - 0.75 * dd ** 1.5, 0.25, 1)[..., None]
    return _S

def camera(t, keys, seg_i, t_in_seg, seg_dur):
    """returns (z, cx, cy) in footage coordinates: slow alternating push, plus eased close-ups on key moments."""
    d = (seg_i % 2 == 0)
    p = ease_in_out_cubic(t_in_seg / max(seg_dur, 0.5)) if seg_dur > 0.5 else 0
    z = (1.0 + 0.05 * p) if d else (1.055 - 0.05 * p)
    cx, cy = 0.5, 0.5 - 0.02 * (p if d else 1 - p)
    for (a, b, kx, ky, kz) in keys:
        if a - 0.7 <= t <= b + 0.7:
            w = ease_in_out_cubic(min((t - (a - 0.7)) / 0.7, ((b + 0.7) - t) / 0.7, 1.0))
            z = z * (1 + (kz - 1) * w); cx = cx + (kx - cx) * w; cy = cy + (ky - cy) * w
    return z, cx, cy

def compose(src, t, ctx):
    S = static(); sp, si = ctx["o2s"](t); sg = SEG[si]
    z, cx, cy = camera(t, ctx["keys"], si, t - sg["o0"], (sg["s1"] - sg["s0"]) / sg["speed"])
    cw, ch = PW / z, PH / z; x0 = min(max(cx * PW - cw / 2, 0), PW - cw); y0 = min(max(cy * PH - ch / 2, 0), PH - ch)
    wx0, wy0, wx1, wy1 = WIN; ww, wh = wx1 - wx0, wy1 - wy0; s = ww / cw
    M = np.array([[s, 0, -x0 * s], [0, s, -y0 * s]], np.float32)
    win = cv2.warpAffine(src, M, (ww, wh), flags=cv2.INTER_AREA if s < 0.9 else cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    win = cv2.LUT(win, LUT)
    # ambient backdrop: the same picture, heavily blurred, dark and warm
    small = cv2.resize(src, (54, 96), interpolation=cv2.INTER_AREA); small = cv2.GaussianBlur(small, (0, 0), 3)
    bg = cv2.resize(small, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    bg = bg * np.array([0.30, 0.34, 0.40], np.float32) + np.array(ESP[::-1], np.float32) * 0.55
    fr = bg * S["bgvig"] * (1 - 0.7 * S["shadow"])
    wf = win.astype(np.float32) * S["vig"]
    reg = fr[wy0:wy1, wx0:wx1]; m = S["mask"]
    reg[:] = wf * m + reg * (1 - m)
    e = S["edge"] * 0.5; reg[:] = reg * (1 - e) + np.array(GOLD[::-1], np.float32) * 0.45 * e
    fr = np.clip(fr, 0, 255).astype(np.uint8)
    for el in ctx["els"]:
        if el.active(t): el.draw(fr, t)
    return fr

def make_ctx():
    b = spec.build(EDL)
    return dict(els=b["elements"], keys=b["keys"], o2s=out2src)

def worker(args):
    k0, k1, path, crf = args; ctx = make_ctx()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", "1",
           "-x264-params", "keyint=240:min-keyint=240:scenecut=0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); cap = cv2.VideoCapture(PROXY); last = -10; fr = None
    for k in range(k0, k1):
        t = k / FPS; s, _ = out2src(t); i = int(round(s * SRC_FPS))
        if i != last:
            if i != last + 1: cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f0 = cap.read()
            if not ok: f0 = fr if fr is not None else np.zeros((PH, PW, 3), np.uint8)
            fr = f0; last = i
        p.stdin.write(compose(fr, t, ctx).tobytes())
    p.stdin.close(); p.wait(); return path

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--t0", type=float, default=0); ap.add_argument("--t1", type=float, default=1e9)
    ap.add_argument("-j", type=int, default=4); ap.add_argument("--crf", type=int, default=15); ap.add_argument("--stills", nargs="*")
    a = ap.parse_args()
    if a.stills is not None:
        ctx = make_ctx(); cap = cv2.VideoCapture(PROXY); O = spec.build(EDL)["o"]
        for st in a.stills:
            t = O(float(st[1:])) if st[0] == "s" else float(st)
            s, _ = out2src(t); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(s * SRC_FPS))); ok, f = cap.read()
            cv2.imwrite(os.path.join(WORK, f"still_{st}.png"), compose(f, t, ctx)); print("still", st, round(t, 2))
        sys.exit()
    from multiprocessing import Pool
    k0, k1 = int(round(a.t0 * FPS)), int(round(min(a.t1, TOTAL) * FPS)); n = a.j * 3; bounds = np.linspace(k0, k1, n + 1).astype(int)
    tmp = os.path.join(WORK, "chunks"); os.makedirs(tmp, exist_ok=True)
    jobs = [(int(bounds[i]), int(bounds[i + 1]), os.path.join(tmp, f"c{i:03d}.mp4"), a.crf) for i in range(n)]; t_start = time.time()
    with Pool(a.j) as pool:
        for i, r in enumerate(pool.imap(worker, jobs)): print(f"chunk {i + 1}/{n} done {time.time() - t_start:.0f}s", flush=True)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out]); print("wrote", a.out, k1 - k0, "frames")
