# PayFlow Pro: one complete video, Glass UI style (video 5)

Source: `video3/source.mp4` (Google Drive `1ghJ0P27cnrvDLAJ_6dbN3Os1XI5lwJA-`, 1080×1440 @ 60 fps, 6:38). Output (not committed, 221 MB): `output/payflow_pro_glass_120fps.mp4`: **1080×1920, 120 fps**, H.264 CRF 16, AAC 224k, 398.2 s, −13.5 LUFS, −1.2 dBFS peak.

## What changed vs the 3 shorts
- **One complete video, the whole recording.** Nothing was cut: video and audio are the original timeline (398.2 s). The 3 shorts had trimmed ~36 s of pauses and word gaps; here none is removed.
- **Voice**: original voice untouched in timing; only a 70 Hz high-pass, light denoise (`afftdn nr=8`), gentle EQ, light 2.2:1 compression and loudnorm to −14 LUFS. No sound effects.
- **Captions**: the full English gloss of every sentence (`data/words.json`), shown in whole phrases (up to 10 words / 64 characters on two lines) inside a glass pill; the spoken word lights up in ice-blue. Nothing is dropped or clipped.
- **Glass UI look**: moving gradient backdrop (4 slow colour blobs), frosted-glass panels for screen, webcam and captions, glass section chips, brand chip, progress bar and timer, ice-blue UI callout rings with glass labels, glass stat cards (placed beside, never over, the face), glass title and closing cards.
- **Feature zooms** on the screen (×1.15–1.9) with eased moves, same cues as before.

## Honest notes
- 120 fps: footage is 60 fps (frames doubled); gradient, zoom, ring and caption motion is rendered natively at 120 fps.
- Captions are an English translation of Urdu speech (Whisper large-v3, forced English). Word-level timing inside a sentence is approximate; a few unclear names were replaced with neutral wording in `video3/scripts/03_edl.py`.
- I could not listen to the audio; levels were checked numerically only. About 15 frames across the film were reviewed.
- The backdrop and glass panels are refreshed at 30 fps (every 4th frame) for speed; all content in front updates at 120 fps.

## Reproduce
`scripts/audio5.py` then `scripts/run.sh` (renders in 16 parallel chunks, ~27 min on 4 cores, then muxes).
