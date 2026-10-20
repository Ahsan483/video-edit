"""Shared constants + helpers for the Job Hunter edit (typography engine, easing, cut map)."""
import os, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("EDIT_WORK", "/tmp/claude-0/work")
SRC = os.path.join(WORK, "src", "source.mov")
FONT_DIR = os.path.join(REPO, "assets", "fonts")

W, H, FPS = 1080, 1920, 60
SCR_Y0, SCR_Y1 = 225, 838          # screen recording band (1080x613)
CAM_Y0, CAM_Y1 = 838, 1627         # webcam band (1080x789)
SCR_H, CAM_H = SCR_Y1 - SCR_Y0, CAM_Y1 - CAM_Y0
CROWN_Y = 883                      # median top of head (abs y)

# ---- palette ---------------------------------------------------------------
WHITE = (255, 255, 255)
SOFT = (176, 183, 192)             # soft gray
TEAL = (25, 211, 197)              # single accent #19D3C5
INK = (8, 10, 12)

# ---- typography system (see EDIT_PLAN.md) -----------------------------------
# role -> (font file, size px, tracking em, line-height em)
TYPE = {
    "display": ("inter-800.ttf", 178, -0.02, 0.92),   # behind-head keyword (size is auto-fitted)
    "statement": ("inter-700.ttf", 84, -0.015, 1.02),  # top-band statements
    "caption": ("inter-600.ttf", 58, -0.01, 1.08),     # bottom-band lines
    "side": ("inter-800.ttf", 64, -0.01, 1.0),         # beside-the-face stacks
    "label": ("inter-600.ttf", 27, 0.16, 1.0),         # eyebrow, uppercase, tracked
    "mono": ("jb-500.ttf", 46, 0.0, 1.2),              # typed command
}


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(round(size)))


# ---- easing -----------------------------------------------------------------
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def out_quart(x):
    x = clamp01(x); return 1 - (1 - x) ** 4


def out_cubic(x):
    x = clamp01(x); return 1 - (1 - x) ** 3


def in_cubic(x):
    x = clamp01(x); return x ** 3


def in_out_cubic(x):
    x = clamp01(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


# ---- text sprites -----------------------------------------------------------
class Sprite:
    """Premultiplied RGBA float32 image + placement metadata."""
    def __init__(self, rgba_premult, ascent_box=None):
        self.p = rgba_premult            # (h, w, 4), rgb premultiplied
        self.h, self.w = rgba_premult.shape[:2]


def _measure(text, f, tracking_px):
    xs, x = [], 0.0
    for i, ch in enumerate(text):
        xs.append(f.getlength(text[:i]) + tracking_px * i)
    total = f.getlength(text) + tracking_px * max(len(text) - 1, 0)
    return xs, total


def text_sprite(text, role, color=WHITE, size=None, pad=0, shadow=0.0, upper=False, colors=None):
    """Render one line. `colors` optionally maps char index -> rgb (for one accent word)."""
    fname, sz, trk, _ = TYPE[role]
    sz = size or sz
    if upper: text = text.upper()
    f = font(fname, sz)
    tpx = trk * sz
    xs, total = _measure(text, f, tpx)
    asc, desc = f.getmetrics()
    sh = int(sz * 0.25) if shadow else 0
    w = int(np.ceil(total)) + 2 * pad + 2 * sh + 4
    h = asc + desc + 2 * pad + 2 * sh
    layer = Image.new("L", (w, h), 0)
    alpha_per_color = {}
    cols = colors or {}
    # draw text mask per colour group so one accent word is possible
    groups = {}
    for i, ch in enumerate(text):
        groups.setdefault(cols.get(i, color), []).append(i)
    rgb = np.zeros((h, w, 3), np.float32); a = np.zeros((h, w), np.float32)
    for col, idxs in groups.items():
        m = Image.new("L", (w, h), 0); d = ImageDraw.Draw(m)
        for i in idxs:
            d.text((pad + sh + 2 + xs[i], pad + sh), text[i], font=f, fill=255)
        ma = np.asarray(m, np.float32) / 255
        rgb += ma[..., None] * np.array(col, np.float32)
        a = np.maximum(a, ma)
    out = np.zeros((h, w, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a
    if shadow:
        blur = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sz * 0.09)), np.float32) / 255
        sa = np.clip(blur * shadow, 0, 1) * (1 - a)       # shadow only where text isn't
        out[..., 3] = np.clip(a + sa, 0, 1)               # (shadow colour = black -> adds 0 rgb)
    spr = Sprite(out)
    spr.cap_top = pad + sh + (asc - 0.73 * sz)            # approx cap top (for alignment)
    spr.baseline = pad + sh + asc
    spr.pad = pad + sh
    return spr


def text_width(text, role, size=None, upper=False):
    fname, sz, trk, _ = TYPE[role]
    sz = size or sz
    if upper: text = text.upper()
    return _measure(text, font(fname, sz), trk * sz)[1]


def fit_size(text, role, max_w, max_size=None, upper=False):
    fname, sz, trk, _ = TYPE[role]
    s = max_size or sz
    while s > 20 and text_width(text, role, s, upper) > max_w:
        s -= 2
    return s


def blit(base, spr, x, y, k=1.0, mask=None, clip=None, behind=None, behind_oy=0):
    """Composite premultiplied sprite onto uint8 BGR `base` at (x, y) (top-left), RGB->BGR handled here.
    k: scalar alpha. mask: optional float (h,w) multiplier in sprite coords. clip: (x0,y0,x1,y1) hard clip."""
    x, y = int(round(x)), int(round(y))
    H_, W_ = base.shape[:2]
    cx0, cy0, cx1, cy1 = clip if clip else (0, 0, W_, H_)
    x0, y0 = max(x, cx0, 0), max(y, cy0, 0)
    x1, y1 = min(x + spr.w, cx1, W_), min(y + spr.h, cy1, H_)
    if x1 <= x0 or y1 <= y0 or k <= 0.002: return
    s = spr.p[y0 - y:y1 - y, x0 - x:x1 - x]
    kk = k
    if mask is not None:
        kk = mask[y0 - y:y1 - y, x0 - x:x1 - x] * k
        kk = kk[..., None]
    if behind is not None:        # `behind` = person matte aligned with base rows (offset behind_oy): subject occludes the text
        kk = ((1 - behind[y0 - behind_oy:y1 - behind_oy, x0:x1]) * k)[..., None]
    reg = base[y0:y1, x0:x1].astype(np.float32)
    a = s[..., 3:4] * kk
    prem = s[..., :3][..., ::-1] * kk                      # RGB -> BGR
    reg = reg * (1 - a) + prem
    base[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)


# ---- cut map ----------------------------------------------------------------
def build_keep_frames(ranges, silences, total_frames):
    """Frame indices kept: inside `ranges` (source seconds), with pauses > 0.38 s tightened."""
    keep = np.zeros(total_frames, bool)
    for a, b in ranges:
        keep[int(round(a * FPS)):int(round(b * FPS))] = True
    for a, b in silences:
        L = b - a
        if L <= 0.38: continue
        pad = 0.11 if L < 0.7 else 0.22
        keep[int(round((a + pad) * FPS)):int(round((b - pad) * FPS))] = False
    return np.where(keep)[0]


class CutMap:
    def __init__(self, kept):
        self.kept = np.asarray(kept)
        self.n = len(self.kept)

    def out_frame(self, t_src):
        """Output frame index of the first kept frame at/after source time t."""
        i = int(np.searchsorted(self.kept, int(round(t_src * FPS))))
        return min(i, self.n - 1) if self.n else 0

    def out_time(self, t_src):
        return self.out_frame(t_src) / FPS

    def covered(self, t0, t1):
        a, b = int(round(t0 * FPS)), int(round(t1 * FPS))
        i0, i1 = np.searchsorted(self.kept, a), np.searchsorted(self.kept, b)
        return i1 > i0
