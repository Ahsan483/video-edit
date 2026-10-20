"""The edit decision list. All times are SOURCE seconds (the renderer maps them through the cut map).

Copy is limited to English terms the creator actually says (he speaks Urdu with English tech words), plus
feature names that are literally on screen.  Layout names:
  behind  : big keyword behind the head (person matte); webcam eases down so the crown tucks over the text
  top     : statement in the black band above the screen recording
  bottom  : caption line in the black band under the webcam
  side_l / side_r : stacks beside the face
  type    : typed command (bottom band)
  eyebrow : small tracked label naming the feature (top band)
  zoom    : feature-focused UI zoom inside the screen band (cx, cy in band px, scale)
"""

# ---- behind-head keywords: (t0, t1, text, accent_word_or_None) --------------
BEHIND = [
    (0.95, 3.10, "JOB HUNTER", None),
    (3.20, 6.10, "REMOTE JOBS", None),
    (14.70, 17.60, "FREE MODELS", "FREE"),
    (29.60, 32.50, "PYTHON", None),
    (66.90, 69.70, "ALL SITES", None),
    (99.80, 101.65, "RECRUITER", None),
    (101.70, 103.40, "OR CEO", None),
    (146.00, 149.30, "TAILORED CV", None),
    (154.70, 157.30, "COVER LETTER", None),
    (170.90, 174.80, "90\u201395%", "90\u201395%"),
    (194.40, 199.80, "ALIGNED", None),
    (213.60, 216.60, "GITHUB", None),
    (263.90, 266.30, "GMAIL", None),
]

# ---- top-band statements: (t0, t1, text, accent_word_or_None) ---------------
TOP = [
    (6.60, 10.90, "Pakistanis can apply", "Pakistanis"),
    (17.90, 21.60, "No paid stuff.", None),
    (121.80, 126.60, "Make CV + Cover Letter", "CV"),
    (149.40, 153.90, "PDF · ATS format", "ATS"),
    (202.90, 205.10, "Senior Data Engineer", None),
    (218.20, 222.20, "jobhunter", None),
    (237.40, 240.80, "Every 30 minutes", "30"),
    (266.40, 269.20, "See you in the next video.", None),
]

# ---- bottom-band captions: (t0, t1, text, accent_word_or_None) ---------------
BOTTOM = [
    (15.30, 17.60, "Gemini free models", "Gemini"),
    (23.40, 29.00, "AI searches jobs from your prompt", "AI"),
    (37.90, 41.50, "Only open to Pakistan", "Pakistan"),
    (41.60, 44.80, "Apply from anywhere", None),
    (59.60, 62.20, "Filter. Search.", None),
    (78.60, 83.20, "Ready = their email", "Ready"),
    (84.60, 88.00, "Compose an email", None),
    (91.80, 95.00, "My resume. My profile.", None),
    (115.70, 119.60, "Read the job description", None),
    (126.40, 129.20, "Upload your CV first", None),
    (159.80, 162.60, "Tailored CV + cover letter", None),
    (166.00, 169.40, "First name · Last name", None),
    (205.30, 208.00, "All Python jobs", "Python"),
    (220.30, 222.60, "Link below the video", None),
    (230.10, 233.40, "Run it locally", None),
    (241.40, 246.60, "Your filter, applied automatically", None),
    (259.40, 263.60, "Automatic email drafts", "email"),
]

# ---- side stacks: (t0, t1, side, [(line_time, text, size, color)]) -----------
SIDE = [
    (33.00, 36.80, "r", [(33.0, "10", 170, "white"), (33.5, "DAYS", 60, "soft")]),
    (45.30, 50.60, "r", [(45.3, "Anywhere", 52, "white"), (46.4, "Worldwide", 52, "white"), (47.6, "APAC", 52, "teal")]),
    (55.80, 57.90, "r", [(55.8, "$1000", 92, "white"), (56.2, "PER TASK", 40, "soft")]),
    (74.90, 77.40, "l", [(74.9, "APPLY", 78, "white"), (75.1, "ON SITE", 60, "soft")]),
    (77.00, 80.80, "r", [(77.0, "READY", 78, "teal")]),
    (109.50, 112.90, "l", [(109.5, "POSTED", 62, "white"), (110.1, "TODAY", 62, "teal")]),
]

# ---- typed command: (t0, t1, text) -------------------------------------------
TYPED = [(12.00, 15.10, "$ git clone jobhunter")]

# ---- eyebrow labels (top band): (t0, t1, text) -------------------------------
EYEBROW = [
    (12.00, 15.10, "GITHUB REPO"),
    (28.60, 32.60, "KEYWORD"),
    (32.90, 36.90, "MAX AGE"),
    (37.60, 44.80, "PAKISTAN FILTER"),
    (44.90, 50.70, "LOCATIONS"),
    (52.70, 57.90, "SALARY"),
    (58.40, 62.20, "SAVE & SEARCH"),
    (74.60, 80.90, "RESULTS"),
    (106.40, 113.50, "APPLY ON SITE"),
    (136.00, 142.00, "ONE BUTTON"),
    (181.80, 190.00, "ONE FILTER · EVERY SITE"),
    (236.00, 242.60, "AUTO-RUN"),
]

# ---- UI zooms inside the 1080x613 screen band: (t0, t1, cx, cy, scale) -------
ZOOMS = [
    (28.80, 32.80, 215, 100, 1.9),     # keywords field
    (32.90, 37.20, 870, 100, 2.3),     # max age
    (37.50, 42.60, 955, 100, 2.4),     # only open to Pakistan
    (44.90, 52.60, 470, 235, 2.0),     # location column
    (52.80, 57.80, 585, 235, 2.3),     # salary column
    (58.50, 61.00, 1000, 100, 2.4),    # save & search
    (61.40, 70.00, 540, 480, 1.5),     # search log (terminal)
    (74.60, 80.60, 110, 220, 1.9),     # status column
    (106.40, 113.60, 330, 260, 1.5),   # posted column / rows
    (114.20, 119.60, 850, 260, 1.6),   # job description pane
    (121.40, 127.00, 900, 150, 2.3),   # make cv + cover letter button
    (135.70, 142.60, 900, 150, 2.3),   # click -> generation
    (236.00, 242.70, 960, 60, 2.5),    # auto-run toggle
]

# ---- click / typing SFX anchored to real UI events (source seconds) ----------
CLICKS = [61.12, 75.75, 77.067, 106.80, 107.85, 110.117, 110.967, 112.05, 113.383,
          139.60, 195.95, 198.417, 202.133, 208.50]
