# Perfume review: "framed print" edit (video 4)

Source: Google Drive `1oyEN_StVkLlbJeLZXsvQUJJFnFZFX63Y` (iPhone, 2160×3840 portrait, HEVC 10-bit **HLG / Dolby Vision**, 60 fps, 96 s). Not committed.

**Deliverable:** `output/perfume_review_120fps.mp4`: 1080×1920, **120 fps**, H.264 High CRF 15, AAC 192k, yuv420p, +faststart, 74.1 s, −13.7 LUFS, −1.4 dBFS peak, 193 MB. It is too large for a normal GitHub file, so it is *not* committed (delivered as a download in the chat; re-create with `scripts/run.sh`).

## Look
- **Framed print**: the full 9:16 picture sits in a rounded, hairline-edged window on an espresso backdrop (the same shot, blurred and darkened, as ambient light). Nothing is ever cropped away, and **no text touches the face**: all typography lives in the margin under the picture.
- **Typography**: Cormorant Garamond (serif) placards with champagne-gold tracked-caps kickers and a hairline that draws out from the centre; word-by-word mask-rise reveals, gentle exits. Five placards: intro, N° 01 King Khan, N° 02 Oppenheimer, verdict; plus a tiny brand line at the top.
- **Colour**: proper HLG→SDR tone mapping (BT.2020 HLG → BT.709), then a soft filmic curve with lifted blacks and warm highlights.
- **Camera**: slow alternating push on each shot, plus eased 4K close-ups on the bottle labels (the 4K source gives real extra detail).
- **Cuts**: pauses tightened; two silent spraying/application stretches kept but sped up (about 1.9–2×) instead of removed. 96 s → 74 s.
- **Sound**: denoise, EQ, gentle compression, loudnorm. No music or effects.

## Honest notes
- **120 fps**: the footage is 60 fps, so subject motion is 60 fps (frames doubled); the camera moves, close-ups and type animation are rendered natively at 120 fps.
- Delivered as **SDR (Rec.709)** for compatibility; the HDR/Dolby Vision metadata is not preserved.
- Product notes on the placards come from what he says, via a forced-English Whisper transcript of Urdu speech, and are paraphrased: King Khan "fresh, citrusy, office wear"; Oppenheimer "BR540-style, heavy, winter". The final "Best for Winter / Buy it blind" line is shown generally because the transcript does not make clear which bottle he means; **please check these four descriptors before posting.**
- The brand name "Pristine Aroma" is read from the box/label and his words.
- I could not listen to the audio; levels were checked numerically only.
- Not every frame was reviewed (about 20 frames across the film).

## Reproduce
`01_transcribe.py` → `02_pauses.py` → `edl.py` → proxy (`ffmpeg … zscale tonemap`, see `work/` notes in `run.sh`) → `audio.py` → `render.py`. Proxy command: `ffmpeg -i source.mp4 -an -vf "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:param=0.3:desat=0,zscale=t=bt709:m=bt709:r=tv,scale=1440:2560:flags=lanczos,format=yuv420p" -r 60 -c:v libx264 -crf 12 -g 30 work/proxy.mp4`.
