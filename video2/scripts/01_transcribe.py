"""Word-level transcript. usage: 01_transcribe.py in.wav out.json [model] [lang|auto]"""
import sys, json, wave
import numpy as np
from faster_whisper import WhisperModel
wav, out = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "large-v3"
lang = sys.argv[4] if len(sys.argv) > 4 else "auto"
PROMPT = ("Demo of Job Hunter, a desktop app that finds remote jobs, drafts emails with a tailored CV and cover letter, "
          "Gmail drafts, Gemini API key, config.json, GitHub, auto-run every 30 minutes, filters.")
m = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=4)
w = wave.open(wav)
audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
segs, info = m.transcribe(audio, word_timestamps=True, language=None if lang == "auto" else lang,
                          initial_prompt=PROMPT, beam_size=5, condition_on_previous_text=False, no_speech_threshold=0.9)
print("lang", info.language, info.language_probability, flush=True)
res = []
for s in segs:
    res.append({"start": s.start, "end": s.end, "text": s.text,
                "words": [{"w": x.word, "s": x.start, "e": x.end, "p": x.probability} for x in s.words]})
    print(round(s.start, 1), s.text, flush=True)
json.dump(res, open(out, "w"), indent=1)
