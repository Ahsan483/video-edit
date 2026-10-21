"""Procedural SFX (48 kHz mono float). Deliberately quiet, no bass, no risers."""
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
def _bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x)
def _env(n, a, d):  # attack/decay exponential envelope
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)

def click(rng, gain=1.0):
    """mouse click: tiny 'tick' (down) + softer release 70 ms later"""
    out = np.zeros(int(0.16 * SR), np.float32)
    for off, g, f in ((0, 1.0, 2600), (0.07, 0.45, 2000)):
        n = int(0.03 * SR); nz = rng.standard_normal(n)
        s = _bp(nz, f * .6, f * 1.8) * _env(n, 0.0004, 0.0045)
        s += 0.5 * np.sin(2 * np.pi * (f * .5) * np.arange(n) / SR) * _env(n, 0.0003, 0.003)
        i = int(off * SR); out[i:i + n] += (s * g * 0.5).astype(np.float32)
    return out * gain

def key(rng, gain=1.0):
    n = int(0.05 * SR); f = rng.uniform(1700, 2900)
    s = _bp(rng.standard_normal(n), f * .55, f * 1.6) * _env(n, 0.0003, 0.007)
    s += 0.35 * np.sin(2 * np.pi * rng.uniform(380, 520) * np.arange(n) / SR) * _env(n, 0.0003, 0.006)
    return (s * 0.42 * gain * rng.uniform(0.7, 1.0)).astype(np.float32)

def whoosh(rng, dur=0.34, f0=500, f1=2800, gain=1.0):
    n = int(dur * SR); nz = rng.standard_normal(n)
    out = np.zeros(n); blocks = 24
    for b in range(blocks):
        a, e = b * n // blocks, (b + 1) * n // blocks
        f = f0 * (f1 / f0) ** (b / blocks)
        out[a:e] = _bp(nz, f * .7, f * 1.35)[a:e]
    t = np.linspace(0, 1, n)
    env = np.sin(np.pi * np.clip(t, 0, 1)) ** 2.2
    return (out * env * 0.55 * gain).astype(np.float32)

def swish(rng, gain=1.0):   # light transition sound: shorter, higher, thinner
    return whoosh(rng, dur=0.2, f0=1400, f1=5200, gain=0.8 * gain)

def tick(rng, gain=1.0):    # tiny accent when a label lands
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1760 * t) * _env(n, 0.001, 0.02) * 0.10 * gain).astype(np.float32)

def place(buf, snd, t, gain_db=0.0):
    i = int(round(t * SR))
    if i < 0 or i >= len(buf): return
    g = 10 ** (gain_db / 20); j = min(len(buf), i + len(snd)); buf[i:j] += snd[:j - i] * g
