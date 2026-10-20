"""Find pauses (voice-band energy VAD on a denoised/normalised copy) -> data/silences.json"""
import subprocess, wave, json, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
tmp = os.path.join(WORK, "audio_norm.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "-af",
                "highpass=f=80,afftdn=nf=-25,dynaudnorm=f=150:g=15,loudnorm=I=-16", tmp], check=True)
w = wave.open(tmp); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
fs, hop = 16000, 320
win = np.hanning(hop * 2); f = np.fft.rfftfreq(hop * 2, 1 / fs); band = (f > 150) & (f < 4000)
E = np.array([10 * np.log10((np.abs(np.fft.rfft(a[i * hop:i * hop + hop * 2] * win)) ** 2)[band].sum() + 1e-12)
              for i in range(len(a) // hop - 1)])
sil = E < 14; runs = []; i = 0
while i < len(sil):
    if sil[i]:
        j = i
        while j < len(sil) and sil[j]: j += 1
        if (j - i) * 0.02 >= 0.3: runs.append((i * 0.02, j * 0.02))
        i = j
    else: i += 1
os.makedirs(os.path.join(REPO, "data"), exist_ok=True)
json.dump(runs, open(os.path.join(REPO, "data", "silences.json"), "w"))
print(len(runs), "pauses,", round(sum(b - a for a, b in runs), 1), "s")
