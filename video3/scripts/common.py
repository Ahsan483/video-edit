"""Shared constants, easing, text sprites and compositing helpers for the video2 edit."""
import os, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work"); OUT = os.path.join(ROOT, "output"); ASSETS = os.path.join(ROOT, "assets")
W, H, FPS = 1080, 1920, 120        # output canvas: 9:16 @ 120 fps (source is 60 fps, frames are doubled; all motion graphics run natively at 120)
SRC_FPS = 60
SRC = os.path.join(ROOT, "source.mp4")
SRC_W, SRC_H = 1080, 1440
CAMSRC = (0, 935, 745, 1387)       # webcam rect inside the source frame
SCRSRC = (0, 105, 1080, 893)       # app content (browser chrome + taskbar cropped away)
# output layout
SCR_CARD = (30, 176, 1050, 920)    # screen card (1020x744)
CAP_ZONE = (60, 940, 960, 1110)    # karaoke captions sit between screen and face
CAM_OUT = (0, 1110, 1080, 1765)    # webcam block (1080x655)
# palette: deep navy base, warm off-white, soft grey, single amber accent
NAVY = (11, 14, 20); NAVY2 = (17, 22, 32)
OFFWHITE = (244, 239, 230); SOFT = (154, 160, 170); AMBER = (255, 176, 32)

def ease_out_expo(t): t = min(max(t, 0.0), 1.0); return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def ease_out_cubic(t): t = min(max(t, 0.0), 1.0); return 1 - (1 - t) ** 3
def ease_in_cubic(t): t = min(max(t, 0.0), 1.0); return t ** 3
def ease_in_out_cubic(t):
    t = min(max(t, 0.0), 1.0); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2
def clamp01(x): return min(max(x, 0.0), 1.0)

_fonts = {}
def font(weight=700, size=48, mono=False):
    k = (weight, size, mono)
    if k not in _fonts:
        p = os.path.join(ASSETS, "jb-500.ttf" if mono else f"inter-{weight}.ttf")
        _fonts[k] = ImageFont.truetype(p, size)
    return _fonts[k]

def text_width(txt, weight, size, track=0.0, mono=False):
    f = font(weight, size, mono); w = 0.0
    for i, ch in enumerate(txt):
        adv = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        w += adv + track * size
    return w

_spr = {}
def sprite(txt, weight=700, size=48, color=OFFWHITE, track=0.0, shadow=0.0, mono=False):
    """RGBA uint8 sprite of one run of text. Returns (img, ox, oy): baseline-left origin inside the sprite."""
    key = (txt, weight, size, color, round(track, 3), shadow, mono)
    if key in _spr: return _spr[key]
    f = font(weight, size, mono); pad = int(size * 0.35) + (int(size * .3) if shadow else 0)
    asc, desc = f.getmetrics()
    w = int(text_width(txt, weight, size, track, mono)) + pad * 2; h = asc + desc + pad * 2
    ox, oy = pad, pad + asc
    layer = Image.new("L", (w, h), 0); d = ImageDraw.Draw(layer)
    x = float(ox)
    for i, ch in enumerate(txt):
        d.text((x, oy), ch, font=f, fill=255, anchor="ls")
        adv = f.getlength(txt[i:i + 2]) - f.getlength(txt[i + 1:i + 2]) if i + 1 < len(txt) else f.getlength(ch)
        x += adv + track * size
    a = np.asarray(layer, np.float32) / 255
    rgb = np.zeros((h, w, 3), np.float32); rgb[:] = color
    if shadow:
        sh = cv2.GaussianBlur(a, (0, 0), size * 0.08 + 1) * shadow
        sh = np.roll(sh, int(size * 0.03), 0)
        ta = a + sh * (1 - a)
        rgb = (rgb * a[..., None] + 0 * (sh * (1 - a))[..., None]) / np.maximum(ta, 1e-4)[..., None]
        a = ta
    img = np.dstack([rgb, a * 255]).astype(np.uint8)
    _spr[key] = (img, ox, oy)
    return _spr[key]

def blit(dst, spr, x, y, a=1.0, clip=None):
    """Alpha-blit RGBA (RGB order) sprite onto BGR dst at integer (x,y); clip=(x0,y0,x1,y1)."""
    if a <= 0.003: return
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if clip:
        x0, y0, x1, y1 = max(x0, clip[0]), max(y0, clip[1]), min(x1, clip[2]), min(y1, clip[3])
    if x1 <= x0 or y1 <= y0: return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4].astype(np.float32) * (a / 255.0)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (d + (s[..., 2::-1].astype(np.float32) - d) * al + 0.5).astype(np.uint8)

def fill_rect(dst, x0, y0, x1, y1, color, a=1.0):
    x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1), dst.shape[1]), min(int(y1), dst.shape[0])
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    c = np.array(color[::-1], np.float32)
    r = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (r + (c - r) * a + .5).astype(np.uint8)
