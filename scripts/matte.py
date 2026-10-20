"""Person matte for the webcam band (y 838..1626 of the 1080x1920 frame) using u2net_human_seg."""
import cv2, numpy as np, onnxruntime as ort
CAM_Y0, CAM_Y1 = 838, 1627
_sess = None
def session(threads=2):
    global _sess
    if _sess is None:
        so = ort.SessionOptions(); so.intra_op_num_threads = threads
        _sess = ort.InferenceSession('/tmp/claude-0/work/models/u2net_human_seg.onnx', so, providers=['CPUExecutionProvider'])
    return _sess
def matte(frame_bgr, threads=2):
    cam = frame_bgr[CAM_Y0:CAM_Y1]
    x = cv2.resize(cam, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32)[:, :, ::-1] / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    s = session(threads)
    o = s.run(None, {s.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = np.clip((o - o.min()) / (o.max() - o.min() + 1e-6), 0, 1)
    m = cv2.resize(m, (cam.shape[1], cam.shape[0]), interpolation=cv2.INTER_CUBIC)
    # tighten the soft u2net edge with a smoothstep, then snap to the image edges (guided filter)
    m = np.clip((m - 0.35) / 0.4, 0, 1); m = m * m * (3 - 2 * m)
    guide = cv2.cvtColor(cam, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    m = cv2.ximgproc.guidedFilter(guide, m.astype(np.float32), 9, 4e-3)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    m = np.clip((m - 0.2) / 0.6, 0, 1)
    return m.astype(np.float32)
