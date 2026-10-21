# Inspection: source video

| | |
|---|---|
| File | Google Drive `1ssvGgSurZsaKdTItgthsCWBDkizoHMZy` → `source.mov` (583 MB, **not committed**) |
| Container / duration | MOV, 463.55 s (7:43) |
| Video | H.264 Main, **1440×1080 (4:3 landscape)**, yuv420p, BT.709, 9.7 Mb/s |
| Frame rate | Container says 300 fps (139,065 packets, 3.33 ms timebase). Frame differencing shows real content updates at ~55–60 fps (the screen recorder duplicates frames), so the edit is conformed to a **constant 60 fps** (`work/src60.mp4`, CRF 12 intermediate) |
| Audio | AAC-LC 48 kHz stereo, but L/R are identical (dual mono mic). Integrated loudness ≈ −23 LUFS |
| Language | The creator speaks English (Whisper large-v3 auto-detected Hindi/Urdu at 54 % but forced-English transcription is clean and consistent). Transcript: `data/transcript_en.json` |

## Composition (differs from the creator's usual portrait layout)
The recording is **landscape 4:3**, not phone-format. There are two layouts:

1. **0:00–0:30.7 and 0:30.7–0:45.0** — 0–30 s is silent (cover-letter PDF on screen, no speech). Speech starts at 30.3 s. From 30.7 s to 45.0 s the webcam fills the full width (1440×875) with a 205 px black bar below.
2. **45.0–end** — a screen recording (VS Code, the *Job Hunter* Tk app, Explorer, Chrome) fills the top 875 px (the Windows taskbar sits at y 837–875). The **webcam is a 559×339 rectangle overlaid bottom-left** (x 0–558, y 741–1079). A pure-black empty band (x 559–1439, y 875–1079, 881×205 px) sits right of the webcam. That band is the only reliable negative space and is where most typography lives.

Face position: in the full-width intro the head sits at x≈410–860, y≈120–700 (left of centre), leaving clean space to its right. In the corner webcam the head is at roughly x 170–420, y 790–1000.

Other findings
- The Job Hunter window occupies x 25–985; to its right the dark VS Code background is empty.
- A Docker notification toast is permanently visible bottom-right of the screen area.
- Real content updates arrive in chunks (the recorder is choppy): the `python -I gui.py` command appears in two jumps rather than being typed char-by-char, so there is no true per-key typing to sync to.
- Dead air is scarce: the creator talks almost continuously. Only 17.7 s of pauses (>0.34 s) were tightened.
