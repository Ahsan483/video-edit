# Job Hunter walkthrough: premium kinetic-typography edit (video 2)

Unattended cloud edit of the creator's second screen recording (landscape 1440×1080, 7:43). Output: **6:55, 1440×1080, 60 fps, H.264 CRF 16 / AAC 192 k / yuv420p / +faststart**, −13.8 LUFS integrated, −1.1 dBFS peak.

## Where every file is
| File | What | Size |
|---|---|---|
| `output/final.mp4` | **Full-quality final edit** (CRF 16). Stored with **Git LFS** (GitHub rejects normal files >100 MB; `gh` was not authenticated in this environment so a Release was not possible). Clone with `git lfs pull`, or use the "Download" button on the file page on GitHub | 113.7 MB |
| `output/final_smaller.mp4` | Same edit, 2-pass x264 @ 1.5 Mb/s so it is a normal file under the limit. SSIM vs the full-quality file 0.998 | 88.4 MB |
| `output/sample.mp4` | 18 s sample from the real edit (intro behind-head title + two behind-head keywords) | 7.2 MB |
| `INSPECTION.md`, `EDIT_PLAN.md` | format/composition findings; timestamped plan + typography system | |
| `previews/*.png` | 6 frames from the final render | |
| `scripts/`, `assets/` (Inter, JetBrains Mono), `data/` | everything to reproduce (transcript, pause map, cut list) | |
`source.mov` (583 MB) is not committed (`.gitignore`).

## What was done
- **Layout kept.** The source is landscape 4:3: screen on top, webcam in the bottom-left, an empty black band to its right; the first 15 s is a full-width webcam intro. Nothing was re-framed.
- **Cuts.** The silent first 30 s was removed. 53 segments, every pause >0.34 s shortened to 0.20 s inside the silence (17.7 s removed; the creator speaks almost continuously, so there is little dead air). On alternate segments the webcam alone punches to 105 %.
- **Typography** (Inter / JetBrains Mono; palette: navy `#0B0E14`, warm off-white, soft grey, one amber `#FFB020` accent, no teal): 10 giant keywords **behind the head/shoulders** using a per-frame person matte (JOB HUNTER, CONFIG, PASSWORD, GEMINI, UPLOAD, 1 CLICK, FILTER, C++, 7 JOBS, TAILORED), ~45 word-by-word staggered statements in the black band, 9 small tracked-caps labels, two typed-command animations, an amber underline sweep, and a closing card. Motion: ease-out-expo mask-rise reveals, wipes, short fade+slide exits. No bounce, glow, particles or glitch. Details in `EDIT_PLAN.md`.
- **UI zooms** (screen rows only, ×1.5–1.9): the `5 roles · 25 bullets · 18 projects · 66 skills` log line, the filter row, the console, and the *Make CV + cover letter* button.
- **Sound.** Voice: denoise, EQ, gentle compression, loudnorm. Procedural SFX at very low level: 6 clicks at detected UI clicks, whooshes on keyword/statement entrances, label ticks, typed-key ticks on the two typed overlays, 6 light swishes on big screen changes. No music, bass, risers or impacts.

## Decisions (no one could be asked)
1. **Frame rate.** The container reports 300 fps with duplicated frames (real updates ≈ 60 fps). The edit is conformed to constant 60 fps.
2. **Captions** are trimmed from what he actually says in English (transcript `data/transcript_en.json`, Whisper large-v3 forced to English). The stretch around 378–404 s (him reading the cover letter) transcribes badly and was left uncaptioned.
3. **Assumed repo URL.** He says "Ahsan483 … job-hunter"; the screen shows the `Ahsan483` git author and `job-hunter` folder, so the closing card reads `github.com/Ahsan483/job-hunter`. Please verify.
4. **Typed `git clone Ahsan483/job-hunter`** is an illustrative overlay (he says "clone the repository"), not something typed on screen. The overlay `python -I gui.py` matches what is actually on screen.
5. **Behind-head words** are right-aligned in the intro (the face leaves free space on the right) and start at x=400 in the corner webcam so the head/shoulder genuinely overlaps the first letter. While a keyword is up the room behind him is dimmed ~50 %.
6. **Branch/folder.** Everything is on branch `video2` under `video2/`; no other files were touched.

## Known issues / honesty
- **I could not listen to the audio.** Loudness, peak and cut points were verified numerically only. SFX levels are single constants in `scripts/make_audio.py` (`db + 14` offset and the per-event dB in `scripts/spec.py`).
- **Click sync is inferred**, not measured: clicks are placed at on-screen change events found by frame differencing (`scripts/04_events.py`). The recording is choppy (the clone/typed text appears in chunks), so there was no real per-key typing to sync to.
- **Matte** is good on head/shoulders but has a slight light rim around the headband and can lag fast hand movement near the shoulders. I reviewed 63 frames (one per typographic element) plus stills, not every frame.
- Zooms up to ×1.9 enlarge a 1440 px UI, so they are slightly soft. A faint darkening ramp hides the seam where the zoomed screen meets the static strip.
- The `final_smaller.mp4` is a re-encode of `final.mp4`, one generation lower.
- The Git LFS file requires LFS to be enabled to clone it (otherwise you get a pointer file); `final_smaller.mp4` always works.

## Reproduce
```
pip install gdown opencv-python-headless pillow numpy scipy faster-whisper onnxruntime
gdown 1ssvGgSurZsaKdTItgthsCWBDkizoHMZy -O video2/source.mov
# model -> video2/work/models/u2net_human_seg.onnx (github.com/danielgatis/rembg/releases/download/v0.0.0/)
ffmpeg -i source.mov -an -vf fps=60 -c:v libx264 -crf 12 -g 60 work/src60.mp4
ffmpeg -i source.mov -vn -ac 1 -ar 16000 work/audio16k.wav
python scripts/01_transcribe.py work/audio16k.wav work/transcript_en.json large-v3 en
python scripts/02_pauses.py work/audio16k.wav work/pauses.json
python scripts/03_build_edl.py        # cut list
python scripts/04_events.py           # screen activity (click placement)
python scripts/make_mattes.py         # person mattes for behind-head words
python scripts/render_video.py --out work/final_silent.mp4 -j 4
python scripts/make_audio.py final
ffmpeg -i work/final_silent.mp4 -i work/audio_final.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart output/final.mp4
./scripts/make_small.sh
```
`spec.py` holds every timestamp (source seconds), caption, zoom and SFX cue; `elements.py` the kinetic text primitives.
