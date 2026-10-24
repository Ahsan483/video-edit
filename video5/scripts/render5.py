"""Render the long Glass UI edit (silent, 1080x1920 @ 120 fps).  usage: render5.py --out work/silent.mp4 [--t0 --t1] [-j 4] [--crf 16] | --stills t..."""
import sys, os, json, argparse, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from elements5 import *
import spec5
TOTAL = spec5.TOTAL

_S = {}
def static():
    if _S: return _S
    sh = np.zeros((H, W), np.float32)
    for (x0, y0, x1, y1) in (PANEL_SCR, PANEL_CAM, CAP_PILL):
        sh[y0 + 16:y1 + 16, x0 + 8:x1 - 8] = 1.0
    _S["shadow"] = (1 - 0.40 * cv2.GaussianBlur(sh, (0, 0), 26))[..., None]
    sw, sht = SCR_IN[2] - SCR_IN[0], SCR_IN[3] - SCR_IN[1]; cw, cht = CAM_IN[2] - CAM_IN[0], CAM_IN[3] - CAM_IN[1]
    _S["m_scr"] = rr(sw, sht, 30)[0]; _S["m_cam"] = rr(cw, cht, 30)[0]
    return _S

PAL = [(70, 120, 255), (190, 80, 255), (40, 220, 200), (255, 110, 170)]
def backdrop(t):
    h, w = 480, 270; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); xx /= w; yy /= h
    base = np.zeros((h, w, 3), np.float32); base[:] = np.array(NAVY[::-1], np.float32)
    pos = [(0.18 + 0.12 * math.sin(t * 0.20), 0.14 + 0.05 * math.cos(t * 0.15), 0.55), (0.85 + 0.06 * math.cos(t * 0.18), 0.48 + 0.14 * math.sin(t * 0.22), 0.5),
           (0.28 + 0.10 * math.cos(t * 0.17 + 1), 0.86 + 0.04 * math.sin(t * 0.2), 0.52), (0.80 + 0.06 * math.sin(t * 0.25), 0.10 + 0.04 * math.sin(t * 0.3), 0.36)]
    for i, (bx, by, r) in enumerate(pos):
        a_ = 0.5 + 0.5 * math.sin(t * 0.05 + i * 1.7); c0, c1 = PAL[i], PAL[(i + 1) % 4]
        c = tuple(c0[j] * (1 - a_) + c1[j] * a_ for j in range(3))
        d = np.sqrt((xx - bx) ** 2 + ((yy - by) * 1.6) ** 2) / r; a = np.clip(1 - d, 0, 1) ** 1.5
        base = base * (1 - a[..., None] * 0.80) + np.array(c[::-1], np.float32) * a[..., None] * 0.80
    return cv2.resize(base, (W, H), interpolation=cv2.INTER_CUBIC)

def make_backdrop(t):
    S = static(); fr = backdrop(t) * S["shadow"]; fr = np.clip(fr, 0, 255).astype(np.uint8)
    glass(fr, PANEL_SCR[0], PANEL_SCR[1], PANEL_SCR[2] - PANEL_SCR[0], PANEL_SCR[3] - PANEL_SCR[1], 44, 1.0, tint=0.12)
    glass(fr, PANEL_CAM[0], PANEL_CAM[1], PANEL_CAM[2] - PANEL_CAM[0], PANEL_CAM[3] - PANEL_CAM[1], 44, 1.0, tint=0.12)
    glass(fr, CAP_PILL[0], CAP_PILL[1], CAP_PILL[2] - CAP_PILL[0], CAP_PILL[3] - CAP_PILL[1], 44, 1.0, tint=0.13)
    return fr

def zoom_state(keys, t):
    z, cx, cy = 1.0, (SCRSRC[2] - SCRSRC[0]) / 2, (SCRSRC[3] - SCRSRC[1]) / 2
    for (ts, kx, ky, kz, d) in keys:
        if t < ts: break
        a = ease_in_out_cubic((t - ts) / d); z, cx, cy = z + (kz - z) * a, cx + (kx - cx) * a, cy + (ky - cy) * a
        if a >= 1: z, cx, cy = kz, kx, ky
    return z, cx, cy

def compose(src, t, ctx, bd):
    S = static(); fr = bd.copy()
    z, zx, zy = zoom_state(ctx["zoom"], t); sx0, sy0, sx1, sy1 = SCRSRC; scr = src[sy0:sy1, sx0:sx1]
    sw, sh_ = sx1 - sx0, sy1 - sy0; cw_, ch_ = sw / z, sh_ / z
    ox = min(max(zx - cw_ / 2, 0), sw - cw_); oy = min(max(zy - ch_ / 2, 0), sh_ - ch_)
    iw, ih = SCR_IN[2] - SCR_IN[0], SCR_IN[3] - SCR_IN[1]; s = iw / cw_
    card = cv2.warpAffine(scr, np.array([[s, 0, -ox * s], [0, s, -oy * s]], np.float32), (iw, ih),
                          flags=cv2.INTER_CUBIC if z > 1.01 else cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
    reg = fr[SCR_IN[1]:SCR_IN[3], SCR_IN[0]:SCR_IN[2]]; m = S["m_scr"]; reg[:] = (card * m + reg * (1 - m)).astype(np.uint8)
    ctx["scale"] = s; ctx["map"] = lambda x, y: (SCR_IN[0] + (x - ox) * s, SCR_IN[1] + (y - sy0 - oy) * s)
    cx0, cy0, cx1, cy1 = CAMSRC; cam = src[cy0:cy1, cx0:cx1]; cwid, chei = CAM_IN[2] - CAM_IN[0], CAM_IN[3] - CAM_IN[1]
    k = cwid / (cx1 - cx0); camo = cv2.warpAffine(cam, np.array([[k, 0, 0], [0, k, 0]], np.float32), (cwid, chei), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    bl = cv2.GaussianBlur(camo, (0, 0), 1.3); camo = cv2.addWeighted(camo, 1.3, bl, -0.3, 0)
    reg = fr[CAM_IN[1]:CAM_IN[3], CAM_IN[0]:CAM_IN[2]]; m = S["m_cam"]; reg[:] = (camo * m + reg * (1 - m)).astype(np.uint8)
    for e in ctx["els"]:
        if not e.active(t): continue
        if e.kind == "card": continue
        (e.draw(fr, t, ctx) if e.kind == "ring" else e.draw(fr, t))
    for e in ctx["els"]:
        if e.kind == "card" and e.active(t): e.draw(fr, t)
    return fr

def make_ctx(): b = spec5.build(); return dict(els=b["elements"], zoom=b["zoom"])

def worker(args):
    k0, k1, path, crf = args; ctx = make_ctx()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", "1",
           "-x264-params", "keyint=240:min-keyint=240:scenecut=0", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); cap = cv2.VideoCapture(SRC); last = -10; fr = None; lastbd = -1; bd = None
    for k in range(k0, k1):
        t = k / FPS; i = min(int(round(t * SRC_FPS)), 23891)
        if i != last:
            if i != last + 1: cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f0 = cap.read()
            if not ok: f0 = fr if fr is not None else np.zeros((SRC_H, SRC_W, 3), np.uint8)
            fr = f0; last = i
        if k // 4 != lastbd: bd = make_backdrop(t); lastbd = k // 4
        p.stdin.write(compose(fr, t, ctx, bd).tobytes())
    p.stdin.close(); p.wait(); return path

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out"); ap.add_argument("--t0", type=float, default=0); ap.add_argument("--t1", type=float, default=1e9)
    ap.add_argument("-j", type=int, default=4); ap.add_argument("--crf", type=int, default=16); ap.add_argument("--stills", nargs="*")
    a = ap.parse_args()
    if a.stills is not None:
        ctx = make_ctx(); cap = cv2.VideoCapture(SRC)
        for st in a.stills:
            t = float(st); cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * SRC_FPS))); ok, f = cap.read()
            cv2.imwrite(os.path.join(WORK, f"still_{st}.png"), compose(f, t, ctx, make_backdrop(t))); print("still", st)
        sys.exit()
    from multiprocessing import Pool
    k0, k1 = int(round(a.t0 * FPS)), int(round(min(a.t1, TOTAL) * FPS)); n = a.j * 4; bounds = np.linspace(k0, k1, n + 1).astype(int)
    tmp = os.path.join(WORK, "chunks"); os.makedirs(tmp, exist_ok=True)
    jobs = [(int(bounds[i]), int(bounds[i + 1]), os.path.join(tmp, f"c{i:03d}.mp4"), a.crf) for i in range(n)]; t_start = time.time()
    with Pool(a.j) as pool:
        for i, r in enumerate(pool.imap(worker, jobs)): print(f"chunk {i + 1}/{n} done {time.time() - t_start:.0f}s", flush=True)
    lst = os.path.join(tmp, "list.txt"); open(lst, "w").write("".join(f"file '{j[2]}'\n" for j in jobs))
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", a.out]); print("wrote", a.out, k1 - k0, "frames")
