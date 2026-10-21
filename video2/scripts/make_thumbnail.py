"""YouTube thumbnail 1280x720 from a real intro frame (face left, big amber/white type right)."""
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
fr = cv2.imread(os.path.join(WORK, "i33.png"))[:875]
# full 16:9 window of the intro frame (face intact on the left), scaled to 1280x720
th = cv2.resize(fr[0:810, 0:1440], (1280, 720), interpolation=cv2.INTER_AREA).astype(np.float32)
blur = cv2.GaussianBlur(th, (0, 0), 1.2); th = np.clip(th + 0.6 * (th - blur), 0, 255)
th = np.clip((th - 128) * 1.12 + 128 + 6, 0, 255)
xx = np.linspace(0, 1, 1280, dtype=np.float32)[None, :, None]
shade = np.clip((xx - 0.55) / 0.2, 0, 1)
navy = np.array(NAVY[::-1], np.float32)[None, None, :]
th = th * (1 - 0.94 * shade) + navy * 0.94 * shade
vig = 1 - 0.35 * np.clip(((np.linspace(-1, 1, 720)[:, None]) ** 2), 0, 1)[..., None]
th = (th * vig).astype(np.uint8)
def line(txt, y, size, col, x=700, w=800):
    s, ox, oy = sprite(txt, w, size, col, -0.03, shadow=0.5); blit(th, s, x - ox, y - oy)
line("AI JOB", 330, 104, OFFWHITE, 800)
line("HUNTER", 448, 104, AMBER, 800)
fill_rect(th, 810, 484, 1225, 489, AMBER, 1)
line("FREE  \u00b7  OPEN SOURCE", 540, 30, SOFT, 810, 700)
cv2.imwrite(os.path.join(ROOT, "publish", "thumbnail.png"), th)
cv2.imwrite(os.path.join(ROOT, "publish", "thumbnail.jpg"), th, [cv2.IMWRITE_JPEG_QUALITY, 95])
