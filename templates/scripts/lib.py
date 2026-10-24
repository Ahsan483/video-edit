"""Tiny motion-graphics toolkit: text sprites with transforms, easing, glow, gradients, noise.  Frames are BGR uint8, 1080x1920."""
import os, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTDIR = os.path.join(ROOT, "fonts")
W, H, FPS, DUR = 1080, 1920, 120, 5.0
N = int(FPS * DUR)

# ---------------------------------------------------------------- easing
def cl(x, a=0.0, b=1.0): return min(max(x, a), b)
def lin(t, a, b): return cl((t - a) / (b - a))
def e_out(t, p=3): t = cl(t); return 1 - (1 - t) ** p
def e_in(t, p=3): t = cl(t); return t ** p
def e_io(t): t = cl(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def e_expo(t): t = cl(t); return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def e_back(t, s=1.70158): t = cl(t); return 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2
def e_elastic(t):
    t = cl(t)
    if t in (0, 1): return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1
def mix(a, b, k): return a + (b - a) * k

# ---------------------------------------------------------------- text
_f = {}
def font(name, size):
    k = (name, size)
    if k not in _f: _f[k] = ImageFont.truetype(os.path.join(FONTDIR, name + ".ttf"), size)
    return _f[k]
def text_w(txt, name, size, track=0.0):
    f = font(name, size); w = 0.0
    for i, ch in enumerate(txt):
        a = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        w += a + track * size
    return w
_s = {}
def spr(txt, name, size, color=(255, 255, 255), track=0.0, stroke=0, stroke_color=(0, 0, 0)):
    """RGBA sprite (RGB colour order). Returns array; origin = centre."""
    key = (txt, name, size, color, round(track, 3), stroke, stroke_color)
    if key in _s: return _s[key]
    f = font(name, size); pad = int(size * 0.3) + stroke * 2; asc, desc = f.getmetrics()
    w = int(text_w(txt, name, size, track)) + pad * 2; h = asc + desc + pad * 2
    lay = Image.new("L", (w, h), 0); d = ImageDraw.Draw(lay); x = float(pad)
    slay = Image.new("L", (w, h), 0); sd = ImageDraw.Draw(slay)
    for i, ch in enumerate(txt):
        d.text((x, pad + asc), ch, font=f, fill=255, anchor="ls")
        if stroke: sd.text((x, pad + asc), ch, font=f, fill=255, anchor="ls", stroke_width=stroke)
        a = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        x += a + track * size
    a_fill = np.asarray(lay, np.uint8)
    if stroke:
        a_str = np.asarray(slay, np.uint8); rgb = np.zeros((h, w, 3), np.float32); rgb[:] = stroke_color
        f3 = (a_fill[..., None] / 255.0); rgb = rgb * (1 - f3) + np.array(color, np.float32) * f3
        out = np.dstack([rgb.astype(np.uint8), a_str])
    else:
        rgb = np.zeros((h, w, 3), np.uint8); rgb[:] = color; out = np.dstack([rgb, a_fill])
    _s[key] = out; return out

def xform(s, scale=1.0, rot=0.0, sx=1.0, sy=1.0):
    """Scale/rotate (degrees, CCW) an RGBA sprite about its centre; returns new RGBA array."""
    h, w = s.shape[:2]; a = math.radians(rot); ca, sa = math.cos(a), math.sin(a)
    kx, ky = scale * sx, scale * sy
    nw = int(abs(w * kx * ca) + abs(h * ky * sa)) + 4; nh = int(abs(w * kx * sa) + abs(h * ky * ca)) + 4
    if nw < 2 or nh < 2: return None
    M = np.array([[kx * ca, ky * sa, 0], [-kx * sa, ky * ca, 0]], np.float32)
    M[:, 2] = np.array([nw / 2, nh / 2]) - M[:, :2] @ np.array([w / 2, h / 2])
    return cv2.warpAffine(s, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

def put(dst, s, cx, cy, scale=1.0, rot=0.0, alpha=1.0, sx=1.0, sy=1.0, clip=None):
    """Alpha-blend sprite s centred at (cx, cy) onto BGR dst."""
    if alpha <= 0.004: return
    t = s if (scale == 1.0 and rot == 0.0 and sx == 1.0 and sy == 1.0) else xform(s, scale, rot, sx, sy)
    if t is None: return
    h, w = t.shape[:2]; x, y = int(round(cx - w / 2)), int(round(cy - h / 2))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if clip: x0, y0, x1, y1 = max(x0, clip[0]), max(y0, clip[1]), min(x1, clip[2]), min(y1, clip[3])
    if x1 <= x0 or y1 <= y0: return
    q = t[y0 - y:y1 - y, x0 - x:x1 - x]; al = q[..., 3:4].astype(np.float32) * (alpha / 255.0)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (d + (q[..., 2::-1].astype(np.float32) - d) * al + 0.5).astype(np.uint8)

def rect(dst, x0, y0, x1, y1, color, alpha=1.0):
    x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1), dst.shape[1]), min(int(y1), dst.shape[0])
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return
    c = np.array(color[::-1], np.float32); r = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (r + (c - r) * alpha + .5).astype(np.uint8)

def rrect_mask(h, w, r):
    m = np.zeros((h * 3, w * 3), np.uint8); R = int(r * 3)
    cv2.rectangle(m, (R, 0), (w * 3 - R, h * 3), 255, -1); cv2.rectangle(m, (0, R), (w * 3, h * 3 - R), 255, -1)
    for cx, cy in ((R, R), (w * 3 - R, R), (R, h * 3 - R), (w * 3 - R, h * 3 - R)): cv2.circle(m, (cx, cy), R, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255

# ---------------------------------------------------------------- image helpers
def vgrad(c0, c1, h=H, w=W):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return (np.array(c0[::-1], np.float32) * (1 - t) + np.array(c1[::-1], np.float32) * t) * np.ones((1, w, 1), np.float32)
def radial(cx, cy, r, color, base=None):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - d, 0, 1)[..., None]
def glow(frame_f, layer_f, strength=1.0, radii=(6, 24, 70)):
    """add bloom of a float layer (HxWx3, 0-255) to float frame"""
    out = frame_f + layer_f * min(strength, 1.0)
    for r, k in zip(radii, (0.9, 0.7, 0.55)):
        out += cv2.GaussianBlur(layer_f, (0, 0), r) * k * strength
    return out
def noise_tile(seed=1, size=512):
    return np.random.RandomState(seed).randn(size, size).astype(np.float32)
def grain(frame, amount, k, tile):
    ox, oy = (k * 37) % tile.shape[1], (k * 91) % tile.shape[0]
    t = np.roll(np.roll(tile, ox, 1), oy, 0)
    big = np.tile(t, (H // t.shape[0] + 1, W // t.shape[1] + 1))[:H, :W]
    return frame + big[..., None] * amount
def to8(f): return np.clip(f, 0, 255).astype(np.uint8)

# ---------------------------------------------------------------- render driver
def render(tpl, out):
    """tpl.frame(t, k) -> BGR uint8 frame (also float allowed). Pipes into ffmpeg (H.264 CRF 15, yuv420p, 120 fps)."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p", "-threads", "2", "-movflags", "+faststart",
           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(N):
        f = tpl.frame(k / FPS, k)
        if f.dtype != np.uint8: f = to8(f)
        p.stdin.write(f.tobytes())
    p.stdin.close(); p.wait()
