"""Person matte for the webcam rect (u2net_human_seg + guided-filter edge snap). model -> work/models/u2net_human_seg.onnx"""
import os, cv2, numpy as np, onnxruntime as ort
from common import WORK, CAM
_sess = None
def session(threads=1):
    global _sess
    if _sess is None:
        so = ort.SessionOptions(); so.intra_op_num_threads = threads
        _sess = ort.InferenceSession(os.path.join(WORK, "models", "u2net_human_seg.onnx"), so, providers=["CPUExecutionProvider"])
    return _sess

def guided(I, p, r, eps):
    """Plain guided filter (He et al.) with box filters; I,p float32 in [0,1]."""
    k = (2 * r + 1, 2 * r + 1); bf = lambda a: cv2.boxFilter(a, -1, k, normalize=True)
    mI, mp = bf(I), bf(p); cov = bf(I * p) - mI * mp; var = bf(I * I) - mI * mI
    a = cov / (var + eps); b = mp - a * mI
    return bf(a) * I + bf(b)

def matte(frame_bgr, threads=1, rect=CAM):
    x0, y0, x1, y1 = rect
    cam = frame_bgr[y0:y1, x0:x1]
    x = cv2.resize(cam, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32)[:, :, ::-1] / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    s = session(threads)
    o = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = np.clip((o - o.min()) / (o.max() - o.min() + 1e-6), 0, 1)
    m = cv2.resize(m, (cam.shape[1], cam.shape[0]), interpolation=cv2.INTER_CUBIC)
    m = np.clip((m - 0.35) / 0.4, 0, 1); m = m * m * (3 - 2 * m)
    guide = cv2.cvtColor(cam, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    m = guided(guide, m.astype(np.float32), 9, 4e-3)
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    return np.clip((m - 0.2) / 0.6, 0, 1).astype(np.float32)
