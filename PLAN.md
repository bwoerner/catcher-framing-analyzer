# Catcher Framing Analyzer - Build Plan

**Stack:** Python, OpenCV, NumPy, Matplotlib

---

## Step 1 - Project Setup
- Create project structure and `requirements.txt`
- Install dependencies: `opencv-python`, `numpy`, `matplotlib`
- Set up a simple CLI entry point (`main.py`)

**Files to create:**
- `main.py` — entry point
- `requirements.txt` — dependencies
- `config.py` — constants (strike zone dimensions, thresholds, etc.)

---

## Step 2 - Video Loading & Frame Extraction
- Accept an MP4 file path as CLI argument
- Use OpenCV (`cv2.VideoCapture`) to read the video
- Extract frames at configurable intervals or around detected events
- Store frames in memory or temp directory for processing

**Files to create:**
- `video_loader.py` — handles video reading and frame extraction

---

## Step 3 - Strike Zone Definition
- Define the strike zone as a rectangle in frame coordinate space
- Support two modes:
  - **Hardcoded** — fixed pixel bounds based on known camera angle
  - **Interactive calibration** — user clicks corners at startup to define zone

**Files to create:**
- `strike_zone.py` — zone definition, coordinate helpers, draw overlay

---

## Step 4 - Glove Detection & Tracking
- Use OpenCV color masking or contour detection to locate the catcher's glove
- Track glove center position across a sliding window of frames around the catch
- Filter out noise with bounding box smoothing

**Files to create:**
- `glove_tracker.py` — detection logic, frame-by-frame position tracking

---

## Step 5 - Catch Point Identification
- Detect the frame where the ball contacts the glove (motion/velocity change in glove position)
- Record glove (x, y) coordinates at that exact frame

**Logic lives in:** `glove_tracker.py`

---

## Step 6 - Post-Catch Movement Analysis
- Measure glove displacement across N frames after the catch point
- Compute direction vector: toward or away from strike zone center
- Flag as "steal" (glove pulled toward zone) or "give away" (glove moves away)

**Files to create:**
- `framing_analysis.py` — movement vector math, zone proximity calculations

---

## Step 7 - Framing Score Per Pitch
- Score each pitch based on:
  - Catch location relative to zone edges (closer to edge = higher framing value)
  - Post-catch movement direction and magnitude
- Output a per-pitch score and classification (e.g., "framed", "neutral", "gave away")

**Logic lives in:** `framing_analysis.py`

---

## Step 8 - Summary Stats & Report
- Aggregate all pitches into overall metrics:
  - Framing grade (A–F or 0–100)
  - Called strikes added (estimated)
  - Average glove drift (px or normalized)
  - Framing percentage by zone region
- Output options:
  - Print summary to terminal
  - Save CSV of per-pitch data
  - Save annotated frame images showing glove path and zone

**Files to create:**
- `reporter.py` — stats aggregation, CSV export, annotated frame output

---

## File Structure (Target)

```
catcher app/
├── main.py
├── config.py
├── requirements.txt
├── video_loader.py
├── strike_zone.py
├── glove_tracker.py
├── framing_analysis.py
├── reporter.py
├── output/          # CSVs and annotated frames saved here
└── PLAN.md
```

---

## Build Order

1. `requirements.txt` + `config.py`
2. `video_loader.py`
3. `strike_zone.py`
4. `glove_tracker.py`
5. `framing_analysis.py`
6. `reporter.py`
7. `main.py` (wires everything together)

---

## Decisions Made

- **Strike zone:** Interactive calibration — user clicks to define zone corners at startup
- **Glove detection:** MediaPipe Pose + Hands — Pose for body orientation, Hands for precise glove position
- **Post-catch tracking window:** Dynamic — track glove until velocity drops below a threshold (glove has settled), max cap of 2 seconds. Convert seconds → frames at runtime using the video's actual FPS, defined in `config.py`
- **Output:** Annotated output video saved to the same directory as the input, named `{original_filename}_tracked.{ext}`
