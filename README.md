# Job Hunter demo: premium minimal edit

Edit of the creator's 4:29 portrait screen-recording (phone-format 1080×1920 @ 60 fps): the "Job Hunter" app on top, the creator on camera below. Everything was produced unattended in the cloud by the scripts in `scripts/`.

## Deliverables
| File | What | Size |
|---|---|---|
| `output/sample.mp4` | 20 s sample (intro + typed command + filter zooms) | 13 MB |
| `output/final_1080p_smaller.mp4` | **Full edit, 258.7 s, 1080×1920, 60 fps.** 2-pass x264 at 2.55 Mb/s so it fits GitHub's 100 MB limit | 91.7 MB |
| `output/final.mp4` | **Full edit, same as above at full quality** (H.264 High, CRF 17, AAC 256k, yuv420p, +faststart) | 162 MB, **see "Where is the full-quality file" below** |
| `INSPECTION.md` | Format, composition, face location, audio findings | |
| `EDIT_PLAN.md` | Timestamped plan and the TYPOGRAPHY SYSTEM | |
| `previews/*.png` | 8 frames from the real renders | |
| `scripts/`, `data/`, `assets/fonts/` | Everything needed to reproduce the edit | |

The two full edits are the same picture and audio. The smaller file measures SSIM 0.994 against the full-quality one. Both measure −14.0 LUFS integrated, with a true peak of −0.9 dBFS.

The source `source.mov` is **not** in the repo (`.gitignore`). It is the Google Drive file `1Kkr1mTN1IbI8zYIhFOgVwaM5ODVrg-0_`.

### Where is the full-quality file
See the section "Full-quality file status" at the end of this README. It records whether `output/final.mp4` could be published, and how.

## What was done
- **Cuts.** The 61 pauses over 0.3 s (26 s in total) were found by voice-band VAD and tightened to about 0.22 s. Cuts land in silence, on frame boundaries (258.7 s output from 269.2 s). After a removed pause the webcam toggles between 100 % and 104.5 % scale (at most once per 2.5 s) so cuts read as deliberate punch-ins. The screen band is never punched.
- **Feature-focused UI zooms.** The UI is only 1080 px wide, so 13 eased zooms (×1.5 to ×2.5) land inside the screen band on the keyword field, max age, the Pakistan checkbox, the locations and salary columns, Save & search, the log terminal, the status column, the job pane, the Make CV button, and the Auto-run toggle. The band edges never move.
- **Typography** (Inter, white / soft-gray, one teal accent `#19D3C5`). The full spec is in `EDIT_PLAN.md`.
  - 13 big keywords sit **behind the creator's head** using a per-frame person matte (u2net_human_seg + guided-filter edge refinement).
  - Top-band statements (e.g. "Pakistanis can apply", "Make CV + Cover Letter"), bottom-band captions, and left / right stacks beside the face ("10 DAYS", "Anywhere / Worldwide / APAC", "$1000 PER TASK", "APPLY ON SITE", "READY").
  - A typed `$ git clone jobhunter` and small teal feature labels over the screen band.
  - Motion is limited to rise-reveals, word-by-word reveals, short slides and fades. No bounce, glow, particles or glitch.
- **Sound.**
  - Voice: denoise, EQ, gentle compression, then two-pass loudnorm of the mix to −14 LUFS.
  - Procedural SFX at very low level: 14 mouse clicks placed on real UI events found by frame differencing, 18 typed key clacks for the typing animation, soft whooshes for text entrances, and four faint swishes at feature changes. No bass, risers or impacts.
  - No music.

## Decisions (the creator could not be asked)
1. **Webcam drop for behind-the-head words.** The crown of his head sits only 45 px below the top of the webcam band, so text placed behind it would be fully hidden. During those words the webcam eases down 120 px (0.55 s in, 0.5 s out). The top rows are filled with edge replication plus blur, which is invisible on this blurred background, and the crown overlaps the lower ~10 % of the letters. This is the only layout change.
2. **Captions use only the English words he actually says**, plus on-screen UI names. He speaks Urdu mixed with English tech terms, and automatic transcription of the Urdu was not reliable enough to caption. Two captions are paraphrases ("AI searches jobs from your prompt", "Your filter, applied automatically"). The typed command `git clone jobhunter` illustrates "clone it".
3. **Branch.** The task asked for commits to `main`. This session was assigned the branch `claude/kind-feynman-4oltg7`, so everything is pushed there.

## Known issues (honest list)
- **I could not listen to the audio.** Loudness, peak, SFX levels and cut continuity were checked numerically only. The SFX are intentionally quiet. If any sound is too subtle or too present, the levels are single constants in `scripts/make_audio.py`.
- **Click sync is by construction, not by ear.** Each click is placed at the mapped output time of a detected UI-change frame, minus 10 ms. I verified that the UI change lands on the expected output frame. I did not independently measure the audio onsets.
- **Transcript and keyword timing.** Whisper `large-v3` forced to English gives a usable sentence gloss, and English keyword times are reliable to about ±0.3 s. Text entrances were aligned to those times. A few words may appear slightly early or late relative to the Urdu speech.
- **Matte limits.** The matte is good for the head and shoulders. It is imperfect at the thin mic boom and at fast hand gestures near the crown (a hand can briefly pop in front of or behind a letter), and the headphone band is treated as part of the head. No visible artefacts were found in the frames I reviewed, but I did not review every frame.
- **Zoom softness.** The source UI is 1080 px wide, so ×2+ zooms are enlarged and slightly soft (lightly sharpened). They are readable but not crisp.
- **Platform UI overlap.** Captions in the bottom band (y ≈ 1676–1760) may sit under TikTok / Reels / Shorts interface elements.
- **The 2-pass smaller file is a re-encode of the full render**, so it is one generation lower than `final.mp4`.
- The sample is a montage of three source ranges (0–11.3 s, 11.9–15.1 s, 29.3–35.0 s), so it jumps between topics by design.

## Reproduce
```
pip install gdown opencv-python opencv-contrib-python pillow numpy faster-whisper onnxruntime fonttools brotli
gdown 1Kkr1mTN1IbI8zYIhFOgVwaM5ODVrg-0_ -O /tmp/claude-0/work/src/source.mov
# models: u2net_human_seg.onnx -> /tmp/claude-0/work/models/ (github.com/danielgatis/rembg/releases/download/v0.0.0/)
python scripts/01_transcribe.py audio16k.wav transcript.json large-v3   # optional, informs EDIT_PLAN
python scripts/analyze_audio.py                  # data/silences.json (pauses)
python scripts/make_mattes.py                    # person mattes for the behind-head windows
python scripts/render_video.py --mode final      # silent video + timeline.json (~12 min on 4 cores)
python scripts/make_audio.py  --mode final       # voice + SFX + loudnorm
python scripts/mux.py --mode final output/final.mp4
scripts/make_small.sh                            # <95 MB version
```
All creative decisions (copy, timing, zooms, click times) live in `scripts/spec.py`. `scripts/gen_plan_tables.py` prints the tables in `EDIT_PLAN.md` from that file.

## Full-quality file status
- `output/final.mp4` (162 MB) is stored with **Git LFS** on this branch (`.gitattributes` tracks `output/final.mp4`). The upload succeeded.
- To get the real file, run `git lfs install`, then `git clone` the repo or `git lfs pull`. The file's "Download" button in the GitHub web UI works for LFS files. "Download ZIP" gives only a small pointer file, not the video.
- GitHub's free LFS plan has a 1 GB/month bandwidth quota, so about six downloads of this file per month.
- **No GitHub Release was created.** The `gh` CLI in this session had an invalid token, and the GitHub tools available here cannot create releases. If you prefer a Release, upload `output/final.mp4` to one manually (limit 2 GB).
- `output/final_1080p_smaller.mp4` (91.7 MB) is a normal git file and works with any download method.
