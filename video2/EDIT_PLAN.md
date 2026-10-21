# Edit plan: Job Hunter walkthrough (video 2)

Source 7:43 → edit ≈ 6:55 (415 s), 1440×1080 @ 60 fps. Same 4:3 canvas, same split layout (screen on top, webcam bottom-left), nothing re-framed.

## 1. Story / key moments (source timestamps → what the typography says)
| Source t | He says | Treatment |
|---|---|---|
| 0–30 s | (silence, cover letter on screen) | **cut** – edit starts at 30.05 s |
| 31–35 | "a lot of people messaged me to guide" | BEHIND-HEAD "JOB / HUNTER" (right of face), caption "You asked for a guide" |
| 37–43 | "how to run this repo and how to use it" | label "SETUP GUIDE" left of face, caption "How to **run** it and **use** it" |
| 43–50 | "clone the repository" | typed `$ git clone Ahsan483/job-hunter` (illustration) |
| 51–63 | config.example.json / profile.example.json, create profile.json + config.json | two-line statements |
| 63–70 | config.example.json | BEHIND "CONFIG" |
| 71–94 | Gmail address, AI-written draft email to the recruiter | 3 statements |
| 100–115 | Gmail app password, Gemini free API key | BEHIND "PASSWORD", BEHIND "GEMINI", labels |
| 115–153 | "three things to add", README steps | "3 things to add", step statements (two-step verification, app password, API key, paste in config.json) |
| 155 | `python -I gui.py` | typed callout with key sounds, soft swish when the app opens (160.2 s) |
| 166–201 | upload CV, Gemini builds profile.json, tailored CV + cover letter in one click | BEHIND "UPLOAD", "1 CLICK", statements |
| 202–245 | powered by Gemini (free model, custom prompt), profile saved | statements, "Done." |
| 245–253 | "5 roles, 25 bullets, 18 projects, 66 skills" | **UI zoom ×1.85 on the log line** + stat statement (numbers in amber) |
| 268–290 | filter: C++, worldwide only, max age 10 days | BEHIND "FILTER", "C++"; **UI zoom ×1.5 on the filter row**; click sounds |
| 295–311 | console, search done, 7 jobs | zoom on console, BEHIND "7 JOBS" |
| 316–333 | apply on site, full-time senior, overview | statements |
| 338–342 | click Make CV + Cover Letter | **zoom ×1.9 on the button**, click sound, BEHIND "TAILORED" |
| 349–375 | it worked, CV saved, tailored folder | statements + labels |
| 409–420, 424–447 | cover letter praise, more features, apply flow | statements |
| 447–460 | repo is public, like/comment/follow | statements |
| 460.6–463 | sign-off | closing card |

## 2. Cut plan
- Start at the first spoken word (30.05 s); end at 463.0 s.
- 53 segments: every silence > 0.34 s is shortened to 0.20 s (cuts always fall inside silence, snapped to 60 fps frames, 8 ms audio crossfades). Net removal 17.7 s plus the 30 s silent opening.
- Jump-cut punch-ins: on alternate segments the **webcam only** scales to 105 %; the screen is never punched.

## 3. TYPOGRAPHY SYSTEM (defined before editing)
**Palette** – base deep navy `#0B0E14` (the empty bar is filled with a navy gradient `#0B0E14→#111620`), headline text warm off-white `#F4EFE6`, secondary soft grey `#9AA0AA`, **single accent amber `#FFB020`** used only for key words, numbers, small label squares and underline sweeps. No teal/cyan anywhere.

**Type** – Inter (800 for giant keywords, 700 for statements, 600 tracked caps for labels), JetBrains Mono 500 for typed commands. Tight tracking (−0.015 to −0.035 em) on display sizes, +0.16 em on caps labels.

**Placements** (chosen from the real negative space)
1. *Behind the head* – giant keyword (≈150–225 px) starts at the webcam's left and runs right across the black bar; a per-frame person matte (u2net_human_seg + guided-filter edge snap) is re-composited over it so head/shoulders sit in front. The room behind him dims ~50 % while the word is up. In the full-width intro the title is right of the face and tucked behind the hair/mic.
2. *Right of face* – two-line staggered statements in the black bar beside the webcam (left-aligned x=610).
3. *Centred* – intro captions below the full-width webcam, and the closing card.
4. *Small feature labels* – tracked caps with an amber square and an underline sweep, in the bar.
5. *Typing animation* – mono command with amber caret.

**Motion language** – ease-out-expo for everything entering (≈0.6 s); per-letter mask-rise for giant words (45 ms stagger); word-by-word mask-rise for statements (75 ms word / 160 ms line stagger); label wipe-in; amber underline sweep (ease-in-out cubic); exits are a short fade + 20 px slide (0.28 s). No bounce, glow, particles, glitch or shake.

**Rules** – never over the UI: all text lives in the black bar or on the webcam rectangle (and the dimmed closing card). One statement at a time. Words come from what he actually says (see transcript); wording is trimmed, never invented. Not every scene gets a keyword.

## 4. Sound
- Voice: mono mix-down, 75 Hz high-pass, FFT denoise (`afftdn`), −2.2 dB @280 Hz, +2.4 dB @3.2 kHz, +1.6 dB shelf @9 kHz, gentle 2.6:1 compression, limiter; two-pass `loudnorm` to −14 LUFS / −1.5 dBTP (whole mix).
- Procedural SFX (numpy, no assets): clicks at 6 detected UI clicks, soft whooshes on keyword entrances (quieter for statements), a tiny tick on labels, typed-key ticks only for the `python -I gui.py` callout and the clone command, light swishes at 6 big screen changes. No bass, risers, impacts. No music.
