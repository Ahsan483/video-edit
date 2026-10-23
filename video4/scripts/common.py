"""Shared constants, easing, serif/sans text sprites and compositing helpers (video 4: perfume review)."""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work"); OUT = os.path.join(ROOT, "output"); ASSETS = os.path.join(ROOT, "assets")
SRC = os.path.join(ROOT, "source.mp4"); PROXY = os.path.join(WORK, "proxy.mp4")     # proxy: HDR->SDR tone-mapped 1440x2560 @ 60 fps
W, H, FPS = 1080, 1920, 120
SRC_FPS = 60; PW, PH = 1440, 2560
WIN = (100, 64, 980, 1628)            # picture window x0,y0,x1,y1 (880x1564, same 9:16 aspect as the footage)
# palette: espresso black, ivory, champagne gold
ESP = (13, 10, 8); ESP2 = (24, 18, 14); IVORY = (243, 237, 226); GOLD = (214, 178, 112); SOFT = (176, 166, 150)

def ease_out_expo(t): t = min(max(t, 0.0), 1.0); return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def ease_out_cubic(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def ease_in_cubic(t): t = min(max(t, 0.0), 1.0); return t ** 3
def ease_in_out_cubic(t): t = min(max(t, 0.0), 1.0); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def clamp01(x): return min(max(x, 0.0), 1.0)

FONTS = {"serif500": "cormorant-garamond-500-normal.ttf", "serif600": "cormorant-garamond-600-normal.ttf",
         "serifi": "cormorant-garamond-500-italic.ttf", "sans": "inter-600-normal.ttf"}
_f = {}
def font(fam, size):
    k = (fam, size)
    if k not in _f: _f[k] = ImageFont.truetype(os.path.join(ASSETS, FONTS[fam]), size)
    return _f[k]
def adv(txt, fam, size, track=0.0):
    f = font(fam, size); w = 0.0
    for i, ch in enumerate(txt):
        a = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        w += a + track * size
    return w
_spr = {}
def sprite(txt, fam, size, color, track=0.0):
    """RGBA sprite; returns (img, ox, oy) with the baseline-left origin at (ox, oy)."""
    key = (txt, fam, size, color, round(track, 3))
    if key in _spr: return _spr[key]
    f = font(fam, size); pad = int(size * 0.3); asc, desc = f.getmetrics()
    w = int(adv(txt, fam, size, track)) + pad * 2; h = asc + desc + pad * 2; ox, oy = pad, pad + asc
    layer = Image.new("L", (w, h), 0); d = ImageDraw.Draw(layer); x = float(ox)
    for i, ch in enumerate(txt):
        d.text((x, oy), ch, font=f, fill=255, anchor="ls")
        a = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        x += a + track * size
    al = np.asarray(layer, np.uint8); rgb = np.zeros((h, w, 3), np.uint8); rgb[:] = color
    _spr[key] = (np.dstack([rgb, al]), ox, oy); return _spr[key]

def blit(dst, spr, x, y, a=1.0, clip=None):
    if a <= 0.003: return
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if clip: x0, y0, x1, y1 = max(x0, clip[0]), max(y0, clip[1]), min(x1, clip[2]), min(y1, clip[3])
    if x1 <= x0 or y1 <= y0: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]; al = s[..., 3:4].astype(np.float32) * (a / 255.0)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (d + (s[..., 2::-1].astype(np.float32) - d) * al + 0.5).astype(np.uint8)

def fill_rect(dst, x0, y0, x1, y1, color, a=1.0):
    x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1), dst.shape[1]), min(int(y1), dst.shape[0])
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    c = np.array(color[::-1], np.float32); r = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (r + (c - r) * a + .5).astype(np.uint8)
