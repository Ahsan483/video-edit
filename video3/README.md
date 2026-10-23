# PayFlow Pro: 3 kinetic-typography Shorts (video 3)

Source: Google Drive `1ghJ0P27cnrvDLAJ_6dbN3Os1XI5lwJA-` (1080×1440 @ 60 fps, 6:38, screen recording on top, webcam bottom-left; not committed). Edited unattended in the cloud on branch `video3`.

| File | Content | Length | Size |
|---|---|---|---|
| `output/short_1.mp4` | Part 1: intro, dashboard, leave approvals, notifications, payroll analytics, employees, profile & tools | 1:36 | 47 MB |
| `output/short_2.mp4` | Part 2: attendance, check-in/break, live monitoring, payroll, payslips, messages, channels | 1:58 | 52 MB |
| `output/short_3.mp4` | Part 3: email, notes, tickets, audit logs, settings/security, new organization, sign-off | 2:18 | 62 MB |

All: **1080×1920 (9:16), 120 fps**, H.264 CRF 17, AAC 192k, yuv420p, −13.7 LUFS. `previews/` has 5 frames; `publish/POSTING_COPY.md` has titles/captions/hashtags.

## What was done
- **Nothing was cut except non-speaking clips** (every pause/gap > 0.30–0.40 s tightened to ~0.11 s; cuts land in silence, 6 ms audio fades). Total removed ≈ 36 s of 398 s; all spoken content is kept and simply split at topic boundaries into three parts.
- **New vertical layout**: browser chrome/taskbar cropped away (also hides the bookmarks bar), rounded screen card with eased feature zooms (×1.25–1.9) on top; captions between; the creator full-width below.
- **Kinetic typography** (Inter 800, navy base, warm white, single amber accent): word-by-word karaoke captions with amber active word and pop; giant keywords **behind the head** via per-frame matte (u2net_human_seg); UI callout rings with label chips that track the zoom; count-up stat cards; section tags; amber sweep wipes at page changes; hook titles; "PART n/3" + progress bar; "next part" teaser; closing card.
- **Sound**: denoise, EQ, compression, loudnorm; quiet procedural clicks/whooshes/swishes.

## Honest notes
- **120 fps**: the source is 60 fps, so footage frames are duplicated; all text, zoom, ring and wipe motion is rendered natively at 120 fps. TikTok/Instagram/YouTube Shorts will typically re-encode to ≤60 fps.
- **Captions are an English gloss**: he speaks Urdu; Whisper large-v3 forced to English gives the text, word timing inside a sentence is approximate. A few unclear names were replaced by neutral wording (`scripts/03_edl.py`).
- I could not listen to the audio; levels were checked numerically only.
- Zooms enlarge a 1080 px screen so small UI text is slightly soft; webcam is upscaled ×1.45 with light sharpening.
- Some zoom/ring coordinates depend on the page not having scrolled; one such ring was removed after review. Not every frame was reviewed (about 60 frames across the three parts).

## Reproduce
`01_transcribe.py` → `02_pauses.py` → `03_edl.py` → `make_mattes3.py` → `run_all.sh` (audio, 120 fps render, mux). `spec3.py` holds all timestamps/graphics; `elements3.py` the animation primitives; `render3.py` the compositor.
