# INSPECTION

Source: Google Drive `1Kkr1mTN1IbI8zYIhFOgVwaM5ODVrg-0_` → `source.mov` (not committed; listed in `.gitignore`).

## Technical
| | |
|---|---|
| Container | QuickTime/MOV, 342 MB, 10.2 Mb/s |
| Video | H.264 High, **1080×1920 portrait (9:16)**, **60 fps** constant, yuv420p, BT.709, 16 154 frames |
| Audio | AAC-LC, 48 kHz stereo, ~158 kb/s |
| Duration | 269.2 s (4:29) |

## Composition (measured on the real frames)
The frame is a vertical stack:

| Band (y px) | Content |
|---|---|
| 0 – 224 | **pure black** letterbox (top) |
| 225 – 837 | **desktop screen recording**, 1080×613 (16:9). It is a Windows app called "Job Hunter" (filters row, results table, job-detail pane, log terminal, taskbar). UI text is tiny at this resolution. |
| 838 – 1626 | **webcam**, 1080×789. The creator is centred, wearing headphones and a mic, in front of a blurred blue background. |
| 1627 – 1919 | **pure black** letterbox (bottom, 293 px) |

Notes:
- The task brief says "UI in the top half, creator in the lower half". In fact the UI occupies only y 225–837, and the black bands (225 px top, 293 px bottom) are the clean negative space for typography.
- **Face location** (person matte, sampled every 2 s): the crown of the head sits at y ≈ 858–896 (median 883), very stable. At 150 px below the crown the head spans x ≈ 190–368 (left) to 617–803 (right). Median x ≈ 285 to 716. Shoulders spread to x ≈ 110–920 below y ≈ 1400.
- **Free space beside the face:** about 250 px on the left and about 300 px on the right at head height. It is wider on the webcam background above and beside the crown.
- **Safe zones for type:**
  1. the black top and bottom bands;
  2. the webcam strip between y 845 and ~1000 (text passes behind the crown);
  3. the narrow side columns beside the head.
  Nothing is ever placed over the screen band (y 225–837).
- **UI events** (frame differencing of the screen band at 30 fps): mouse-driven changes at about 61 s (search), 75–77 s, 106–119 s (row selections), 141 s (Make CV click), 157 s, and 183–208 s (row selections). The log terminal scrolls between 61 and 72 s. These are used for click SFX and zoom timing.

## Audio
- Voice is quiet and fairly constant: about −30 dBFS RMS per second, with a steady room-noise floor. It needs denoise, EQ, compression and loudness normalisation.
- **Language: Urdu/Hindi mixed with English tech words** (Job Hunter, remote jobs, Gemini, Python, repo, CV, ATS, Gmail, GitHub, …).
- Whisper `small.en` was unusable. `large-v3` forced to English gave a usable gloss of the sentences plus reliable English keyword timestamps (`scripts/01_transcribe.py`). Word times are approximate for Urdu words, but good for the English terms used as captions.
- Pauses: 61 silences > 0.3 s totalling 26 s, found by voice-band energy VAD.
