# Catcher Framing Analyzer - Build Plan

**Stack:** Python, OpenCV, MediaPipe, NumPy, Matplotlib

---

## Workflow Overview

1. Run the tool pointed at a **folder of videos**
2. Select or create a **named calibration profile** (defines the strike zone for this camera angle)
3. For each video, an **interactive playback window** opens — user presses a key to mark each catch frame
4. Tool processes all marked pitches using MediaPipe glove tracking
5. Outputs a `{filename}_tracked.{ext}` annotated video per input file, saved alongside the original

---

## Step 1 - Project Setup
- Create project structure and `requirements.txt`
- Install dependencies: `opencv-python`, `mediapipe`, `numpy`, `matplotlib`
- Set up CLI entry point (`main.py`)

**Files to create:**
- `main.py` — entry point, wires everything together
- `requirements.txt` — dependencies
- `config.py` — constants (velocity threshold, max hold duration, supported video extensions, etc.)

---

## Step 2 - Video Loading
- Accept a folder path as CLI argument
- Scan folder for supported video files (mp4, mov, avi)
- Read each video with OpenCV (`cv2.VideoCapture`)
- Extract FPS and frame count from video metadata

**Files to create:**
- `video_loader.py` — folder scanning, video reading, metadata extraction

---

## Step 3 - Calibration Profiles
- Named profiles that store strike zone corner coordinates
- Profiles saved to a local JSON file (`profiles.json`)
- At startup, user can:
  - Select an existing profile
  - Create a new profile (triggers interactive calibration)
  - Edit an existing profile (re-run calibration)
- One profile applies to the entire batch of videos being processed

**Interactive calibration:**
- Display first frame of the first video
- User clicks 4 corners of the strike zone
- Zone saved to the selected profile name

**Files to create:**
- `calibration.py` — profile load/save, interactive calibration UI
- `profiles.json` — persisted calibration profiles (gitignored)

---

## Step 4 - Catch Frame Marking
- For each video, open an interactive playback window
- User controls:
  - `Space` — play/pause
  - `→` / `←` — step forward/backward one frame
  - `M` — mark current frame as a catch frame
  - `U` — unmark last marked frame
  - `Enter` — done marking, proceed to processing
  - `Q` — skip this video
- Marked catch frames displayed as overlay on the video timeline
- Returns list of catch frame numbers for processing

**Logic lives in:** `video_loader.py` or dedicated `marker.py`

---

## Step 5 - Glove Detection & Tracking (MediaPipe)
- Use **MediaPipe Pose** for body orientation and to locate the catching arm
- Use **MediaPipe Hands** for precise glove/palm position
- For each frame, extract (x, y) position of the catching hand landmark
- Smooth positions with a rolling average to reduce noise

**Files to create:**
- `glove_tracker.py` — MediaPipe setup, per-frame landmark extraction, position smoothing

---

## Step 6 - Post-Catch Movement Analysis
- Starting from each marked catch frame, track glove position forward
- **Stop condition:** glove velocity drops below threshold (defined in `config.py`) — glove has settled
- **Max cap:** 2 seconds (converted to frames using video FPS at runtime)
- Compute:
  - Glove path from catch to settle
  - Direction vector: toward or away from strike zone center
  - Total displacement magnitude
  - Classification: `"framed"` / `"neutral"` / `"gave away"`

**Files to create:**
- `framing_analysis.py` — velocity calculation, path analysis, zone proximity math, pitch classification

---

## Step 7 - Framing Score Per Pitch
- Score each pitch based on:
  - Catch location relative to zone edges (border pitches = higher framing value)
  - Post-catch movement direction and magnitude
- Output per-pitch score and classification

**Logic lives in:** `framing_analysis.py`

---

## Step 8 - Annotated Video Output
- For each input video, produce `{filename}_tracked.{ext}` saved in the same folder
- Full video is processed first, then output is written with all values known upfront

**Body/glove overlay (on every frame):**
- MediaPipe skeleton (pose landmarks)
- Glove position dot
- Post-catch glove path trail (catch frame onward)
- Strike zone rectangle (from calibration profile)

**Metrics panel — top left corner, every frame:**
```
FRAMING ANALYSIS
────────────────────────
Glove Distance   2.3 in
Glove Speed      4.1 in/s
Direction        Toward
Hold Time        0.8 s
Elbow Movement   1.1 in
Body Stability   0.6 in
```

**Pixel-to-inches conversion:**
- Anchored to home plate width = 17 inches
- Pixel width of calibrated strike zone used to derive pixels-per-inch ratio
- Approximate, not exact — acceptable for coaching feedback

**Metric definitions:**
- `Glove Distance` — total glove displacement from catch frame to settle point
- `Glove Speed` — peak glove velocity during framing movement (in/s)
- `Direction` — `Toward` or `Away` relative to strike zone center
- `Hold Time` — seconds from catch frame to glove settle
- `Elbow Movement` — total elbow landmark displacement from catch to settle
- `Body Stability` — total shoulder/torso landmark displacement from catch to settle (less = better)

**Files to create:**
- `reporter.py` — frame annotation, metrics overlay, video writing

---

## File Structure (Target)

```
catcher app/
├── main.py
├── config.py
├── requirements.txt
├── video_loader.py
├── calibration.py
├── glove_tracker.py
├── framing_analysis.py
├── reporter.py
├── profiles.json        # gitignored — saved calibration profiles
└── PLAN.md
```

---

## Build Order

1. `requirements.txt` + `config.py`
2. `video_loader.py` (folder scan + video reading)
3. `calibration.py` (profiles + interactive zone calibration)
4. `video_loader.py` — catch frame marking UI
5. `glove_tracker.py` (MediaPipe glove tracking)
6. `framing_analysis.py` (post-catch analysis + scoring)
7. `reporter.py` (annotated video output)
8. `main.py` (wires everything together)

---

## Decisions Made

| Decision | Choice |
|---|---|
| Strike zone definition | Interactive calibration, saved as named profiles |
| Calibration scope | One profile per batch; profiles reusable across sessions |
| Glove detection | MediaPipe Pose + Hands |
| Pitch segmentation | Manual — user marks catch frames during interactive playback |
| Catch frame detection | User presses `M` key during video playback |
| Post-catch tracking window | Dynamic — track until glove velocity < threshold; 2s max cap |
| Batch input | Folder of video files |
| Output | Annotated video: `{filename}_tracked.{ext}`, saved alongside original |
| Metrics overlay | Top left corner, visible on every frame |
| Metrics | Glove Distance (in), Glove Speed (in/s), Direction, Hold Time (s), Elbow Movement (in), Body Stability (in) |
| Pixels-to-inches | Anchored to home plate width (17 in) via calibrated strike zone |

---

## Config Values (to tune during development)

- `GLOVE_VELOCITY_THRESHOLD` — px/frame below which glove is considered settled
- `MAX_HOLD_SECONDS` — maximum post-catch tracking window (default: 2.0)
- `SUPPORTED_EXTENSIONS` — video file types to scan for (default: mp4, mov, avi)
- `POSITION_SMOOTH_WINDOW` — rolling average window for glove position smoothing
