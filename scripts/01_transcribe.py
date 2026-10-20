"""Transcribe with word timestamps. usage: 01_transcribe.py in.wav out.json [model]"""
import sys, json, wave
import numpy as np
from faster_whisper import WhisperModel
wav, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "small.en"
PROMPT = ("Demo of Job Hunter, a desktop app that finds remote jobs, drafts emails with a tailored CV and cover letter "
          "in ATS format, Gmail drafts, auto-run every 30 minutes, filters, Pakistan, worldwide.")
m = WhisperModel(model, device="cpu", compute_type="int8")
w = wave.open(wav)
audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
segs, info = m.transcribe(audio, word_timestamps=True, language="en", initial_prompt=PROMPT,
                          beam_size=5, condition_on_previous_text=False, no_speech_threshold=0.9)
res = [{"start": s.start, "end": s.end, "text": s.text,
        "words": [{"w": x.word, "s": x.start, "e": x.end, "p": x.probability} for x in s.words]} for s in segs]
json.dump(res, open(out, "w"), indent=1)
print(len(res), "segments")
