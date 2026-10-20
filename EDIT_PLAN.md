# EDIT PLAN

Source: 269 s portrait screen-recording of the creator's **Job Hunter** app (1080×1920, 60 fps).
The creator speaks Urdu mixed with English tech words. He walks through the app in this order:

| Source time | What he says and shows |
|---|---|
| 0:00 – 0:29 | Intro: he built Job Hunter to find remote jobs, including ones Pakistanis can apply to. Repo link to clone. Free Gemini models, no paid stuff. AI works from a prompt. |
| 0:29 – 0:58 | Filter row: keyword *Python*, max age 10 days, "only open to Pakistan" checkbox. Locations column (Anywhere / Worldwide / APAC) and the salary column ($1000 per task). |
| 0:58 – 1:26 | Save & search, then the log terminal while it searches every site. Results: **Apply on site** vs **Ready** (= email found). Compose an email. |
| 1:27 – 1:46 | What to put in the email: resume and profile, a perfect fit. The recruiter or CEO can reply. |
| 1:46 – 2:00 | Apply-on-site rows, "posted today", reading the job description. |
| 2:00 – 2:55 | **Make CV + Cover Letter** button: Tailored CV (PDF, ATS format) and a cover letter. Fill in name and other fields manually. 90–95 % chance. |
| 2:55 – 3:28 | One filter across every site. Results are aligned (Python jobs, senior data engineer). |
| 3:28 – 3:56 | The project is on his GitHub ("jobhunter"), link below the video. Run it locally. |
| 3:56 – 4:29 | **Auto-run every 30 minutes**, Gmail drafts, sign-off. |

## Editorial decisions
1. **Keep the split-screen.** It is 9:16, 60 fps, with the same aspect ratio, frame rate and framing as the original. The only layout change is that the webcam eases down 120 px for the behind-the-head keywords (see below).
2. **Pauses.** Voice-band VAD found 61 pauses longer than 0.3 s, 26 s in total. Each pause longer than 0.38 s is tightened to about 0.22 s (0.44 s for pauses over 0.7 s). Cuts always fall in silence, on frame boundaries, and the audio is joined with 6 ms dips.
3. **Jump-cut cover.** After a removed pause of 0.25 s or more, the webcam toggles between 100 % and 104.5 % scale. This happens at most once per 2.5 s, so cuts read as deliberate punch-ins. The screen band is never punched.
4. **UI zooms.** The UI is only 1080 px wide, so its text is tiny on a phone. Thirteen zooms (×1.5 – ×2.5) sit inside the screen band and always land on the thing being discussed. They are eased (in-out cubic, 0.6 s) and the band edges never move.
5. **Typography never covers UI.** All type sits in the black bands (y 0–224 and 1627–1919) or on the webcam picture (y ≥ 845). Nothing is placed in the screen band at y 225–837.
6. **Captions are English words he actually says.** These are Job Hunter, remote jobs, Pakistan, Gemini, Python, repo, CV, ATS, Gmail and similar terms, plus on-screen UI names (Apply on site, Ready, Make CV + cover letter). His Urdu sentences are not translated into captions, to avoid putting wrong words in his mouth. Two short captions are paraphrases of what he says: "AI searches jobs from your prompt" and "Your filter, applied automatically". The typed command `$ git clone jobhunter` illustrates "clone it".
7. **Subject mask.** A per-frame person matte (u2net_human_seg, guided-filtered to the image edges, temporally interpolated) is computed only for the windows that need it. It is used to place text behind the head and to dim only the background behind that text, never the person.
8. **Behind-the-head layout.** The crown of his head sits only 45 px below the top of the webcam band, so a keyword placed behind it would be fully hidden. During those words the webcam eases down 120 px (0.55 s in, 0.5 s out). The top rows are filled by edge replication plus blur, which is invisible on this out-of-focus background. The baseline is placed from the measured crown height of each scene, 8 px below it, so the crown only tucks over the lower edge of the letters (about 0–25 px depending on head movement). The word stays fully readable and still reads as sitting behind the head. There are 13 such keywords, each held for 1.7 s or more.

## TYPOGRAPHY SYSTEM (fixed before editing)
Font: **Inter** (static 400–800 from fontsource). Accent: **#19D3C5** teal, used for at most one word or element per scene. Everything else is white `#FFFFFF` or soft gray `#B0B7C0`.
Canvas 1080×1920, side margin 72 px, top-band baseline y = 150, bottom-band cap-top y = 1676, eyebrow centreline y = 196.

| Role | Weight / size | Tracking | Case | Where | Use |
|---|---|---|---|---|---|
| Display | ExtraBold 800, auto-fit to 940 px wide, max 190 px | −2 % | UPPER | centred behind the crown, baseline = measured crown + 8 px | one keyword or short phrase per scene |
| Statement | Bold 700, 84 px (auto-fit to 936 px, wraps to 2 lines) | −1.5 % | Sentence | top band, left-aligned at 72 | key statements |
| Caption | SemiBold 600, 58 px (auto-fit, then 2 lines) | −1 % | Sentence | bottom band, left-aligned at 72 | short supporting lines |
| Side stack | ExtraBold 800, 40–170 px, auto-fit to the free column (215 px left, 260 px right) | −1 % | UPPER / numerals | beside the face, with a soft shadow | numbers and short labels |
| Label (eyebrow) | SemiBold 600, 27 px | +16 % | UPPER, teal | top band above the screen, with a 44 px teal rule | names the feature on screen |
| Mono | JetBrains Mono 500, 46 px | 0 | as typed | bottom band | typed command, with a teal block cursor |

**Motion rules**
- **Behind-head keyword:** rise from the baseline inside a clip box (0.55 s, ease-out-quart) plus fade, then it holds. Exit is a 0.3 s fade. Nothing bounces or scales.
- **Statements and captions:** word-by-word reveal. Each word rises 20 px and fades in over about 0.34 s, staggered 70 ms, capped at 0.35 s total. Exit is a 0.26 s fade.
- **Labels:** the rule grows from 0 to 44 px and the text slides 16 px while fading in, over 0.45 s. Exit is a fade.
- **Side stacks:** each line rises 16 px and fades in at its own spoken time. The beside-the-face background gets a soft dim gradient for legibility.
- **Typing:** 45–95 ms per character with deterministic jitter, teal block cursor, no extra effect.
- **Zoom:** in-out cubic, 0.6 s. Consecutive zooms chain directly from one to the next.
- **Never:** glow, particles, bounce, glitch, shake, spinning or stretching text. At most one big text element on screen at a time.

## SOUND PLAN
- **Voice:** mono, 85 Hz high-pass, FFT denoise, EQ (−2.5 dB at 230 Hz, +2.5 dB at 3.2 kHz, +1.2 dB air shelf), gentle 3:1 compression, limiter. Then two-pass loudnorm of the final mix to **−14 LUFS, true peak ≤ −1 dBTP**.
- **SFX are procedural** (numpy) and kept very low in the mix. A 140 Hz high-pass on the SFX bus means no bass.
  - Mouse clicks (down plus a softer up) at the real UI events found by frame differencing.
  - Key clacks, one per visible typed character.
  - Soft band-limited whooshes only for behind-head keywords (full level) and top statements (about half level).
  - A very faint swish at four feature changes (zoom starts).
- No music (no licence-free track available offline, and the voice is already dense).

## TIMESTAMPED PLAN
All times are in **source** time, before pause removal. "behind head" means the subject matte hides the lower part of the letters. Click sounds are listed under the zoom table.

| source time | layout | text |
|---|---|---|
| 0:00.95 – 0:03.10 | behind head (matte) | JOB HUNTER |
| 0:03.20 – 0:06.10 | behind head (matte) | REMOTE JOBS |
| 0:06.60 – 0:10.90 | top band | Pakistanis can apply |
| 0:12.00 – 0:15.10 | label | GITHUB REPO |
| 0:12.00 – 0:15.10 | typing animation | $ git clone jobhunter |
| 0:14.70 – 0:17.60 | behind head (matte) | FREE MODELS |
| 0:15.30 – 0:17.60 | bottom band | Gemini free models |
| 0:17.90 – 0:21.60 | top band | No paid stuff. |
| 0:23.40 – 0:29.00 | bottom band | AI searches jobs from your prompt |
| 0:28.60 – 0:32.60 | label | KEYWORD |
| 0:29.60 – 0:32.50 | behind head (matte) | PYTHON |
| 0:32.90 – 0:36.90 | label | MAX AGE |
| 0:33.00 – 0:36.80 | right of face | 10 / DAYS |
| 0:37.60 – 0:44.80 | label | PAKISTAN FILTER |
| 0:37.90 – 0:41.50 | bottom band | Only open to Pakistan |
| 0:41.60 – 0:44.80 | bottom band | Apply from anywhere |
| 0:44.90 – 0:50.70 | label | LOCATIONS |
| 0:45.30 – 0:50.60 | right of face | Anywhere / Worldwide / APAC |
| 0:52.70 – 0:57.90 | label | SALARY |
| 0:55.80 – 0:57.90 | right of face | $1000 / PER TASK |
| 0:58.40 – 1:02.20 | label | SAVE & SEARCH |
| 0:59.60 – 1:02.20 | bottom band | Filter. Search. |
| 1:06.90 – 1:09.70 | behind head (matte) | ALL SITES |
| 1:14.60 – 1:20.90 | label | RESULTS |
| 1:14.90 – 1:17.40 | left of face | APPLY / ON SITE |
| 1:17.00 – 1:20.80 | right of face | READY |
| 1:18.60 – 1:23.20 | bottom band | Ready = their email |
| 1:24.60 – 1:28.00 | bottom band | Compose an email |
| 1:31.80 – 1:35.00 | bottom band | My resume. My profile. |
| 1:39.80 – 1:41.65 | behind head (matte) | RECRUITER |
| 1:41.70 – 1:43.40 | behind head (matte) | OR CEO |
| 1:46.40 – 1:53.50 | label | APPLY ON SITE |
| 1:49.50 – 1:52.90 | left of face | POSTED / TODAY |
| 1:55.70 – 1:59.60 | bottom band | Read the job description |
| 2:01.80 – 2:06.60 | top band | Make CV + Cover Letter |
| 2:06.40 – 2:09.20 | bottom band | Upload your CV first |
| 2:16.00 – 2:22.00 | label | ONE BUTTON |
| 2:26.00 – 2:29.30 | behind head (matte) | TAILORED CV |
| 2:29.40 – 2:33.90 | top band | PDF · ATS format |
| 2:34.70 – 2:37.30 | behind head (matte) | COVER LETTER |
| 2:39.80 – 2:42.60 | bottom band | Tailored CV + cover letter |
| 2:46.00 – 2:49.40 | bottom band | First name · Last name |
| 2:50.90 – 2:54.80 | behind head (matte) | 90–95% |
| 3:01.80 – 3:10.00 | label | ONE FILTER · EVERY SITE |
| 3:14.40 – 3:19.80 | behind head (matte) | ALIGNED |
| 3:22.90 – 3:25.10 | top band | Senior Data Engineer |
| 3:25.30 – 3:28.00 | bottom band | All Python jobs |
| 3:33.60 – 3:36.60 | behind head (matte) | GITHUB |
| 3:38.20 – 3:42.20 | top band | jobhunter |
| 3:40.30 – 3:42.60 | bottom band | Link below the video |
| 3:50.10 – 3:53.40 | bottom band | Run it locally |
| 3:56.00 – 4:02.60 | label | AUTO-RUN |
| 3:57.40 – 4:00.80 | top band | Every 30 minutes |
| 4:01.40 – 4:06.60 | bottom band | Your filter, applied automatically |
| 4:19.40 – 4:23.60 | bottom band | Automatic email drafts |
| 4:23.90 – 4:26.30 | behind head (matte) | GMAIL |
| 4:26.40 – 4:29.20 | top band | See you in the next video. |

| source time | UI zoom (centre x,y in screen band · scale) |
|---|---|
| 0:28.80 – 0:32.80 | (215, 100) · ×1.9 |
| 0:32.90 – 0:37.20 | (870, 100) · ×2.3 |
| 0:37.50 – 0:42.60 | (955, 100) · ×2.4 |
| 0:44.90 – 0:52.60 | (470, 235) · ×2.0 |
| 0:52.80 – 0:57.80 | (585, 235) · ×2.3 |
| 0:58.50 – 1:01.00 | (1000, 100) · ×2.4 |
| 1:01.40 – 1:10.00 | (540, 480) · ×1.5 |
| 1:14.60 – 1:20.60 | (110, 220) · ×1.9 |
| 1:46.40 – 1:53.60 | (330, 260) · ×1.5 |
| 1:54.20 – 1:59.60 | (850, 260) · ×1.6 |
| 2:01.40 – 2:07.00 | (900, 150) · ×2.3 |
| 2:15.70 – 2:22.60 | (900, 150) · ×2.3 |
| 3:56.00 – 4:02.70 | (960, 60) · ×2.5 |

Click SFX (source time): 1:01.12, 1:15.75, 1:17.07, 1:46.80, 1:47.85, 1:50.12, 1:50.97, 1:52.05, 1:53.38, 2:19.60, 3:15.95, 3:18.42, 3:22.13, 3:28.50
