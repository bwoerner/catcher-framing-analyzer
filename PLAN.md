# Catcher Framing Analyzer - Build Plan

**Stack:** Python, OpenCV, MediaPipe Pose, NumPy, Matplotlib

---

## Workflow Overview

1. Run the tool pointed at the top-level **`videos/` folder**
2. Tool scans for **subfolders** — each subfolder represents one camera setup/session
3. **Skip any subfolder where all videos already have a `_tracked` output** — only process new or unfinished folders
4. For each new subfolder:
   - If a profile matching the subfolder name exists → load it automatically
   - If no matching profile exists → trigger interactive calibration and save under the subfolder name
5. For each unprocessed video, an **interactive playback window** opens — user marks the catch frame
6. Tool processes the catch frame using MediaPipe Pose glove tracking
7. Outputs a `{filename}_tracked.{ext}` annotated video saved alongside the original in the subfolder

---

## Step 1 - Project Setup ✅
- Create project structure and `requirements.txt`
- Install dependencies: `opencv-python`, `mediapipe`, `numpy`, `matplotlib`
- Set up CLI entry point (`main.py`)

**Files to create:**
- `main.py` — entry point, wires everything together
- `requirements.txt` — dependencies
- `config.py` — constants (velocity threshold, max hold duration, supported video extensions, etc.)

**Completed:**
- Created `requirements.txt` and installed all dependencies via `python -m pip install -r requirements.txt`
- Created `config.py` with all tunable constants: tracking thresholds, measurement values, video extensions, output suffix, overlay colors and font settings
- Created `main.py` skeleton — accepts an optional folder path argument, defaults to `./videos/`, validates folder exists, exits with error if not found
- Created `videos/` folder as the default input location — contents gitignored, folder tracked via `.gitkeep`
- Updated `.gitignore` to ignore video files inside `videos/` while keeping the folder tracked

---

## Step 2 - Video Loading ✅
- Scan top-level `videos/` folder for subfolders — each subfolder = one camera setup/session
- For each subfolder, scan for supported video files (mp4, mov, avi)
- Skip videos that already have a `_tracked` output file — only process new ones
- Read each video with OpenCV (`cv2.VideoCapture`)
- Extract FPS and frame count from video metadata

**Files to create:**
- `video_loader.py` — subfolder scanning, video reading, metadata extraction, processed file detection

**Completed:**
- Created `video_loader.py` with three functions:
  - `scan_folder(folder_path)` — returns sorted list of video paths, handles upper and lowercase extensions via `filename.lower()`
  - `get_video_info(video_path)` — opens video and returns a `VideoInfo` dataclass with `fps`, `frame_count`, `width`, `height`, `duration_seconds`, and `filename`
  - `read_frame(cap, frame_number)` — seeks to a specific frame and returns it (utility needed by later modules)
- Tested with `IMG_5217.MOV` — 30fps, 135 frames, 1920x1080, 4.5s duration
- **Needs update:** add subfolder scanning and `_tracked` skip logic (to be done when wiring `main.py`)

---

## Step 3 - Calibration Profiles ✅
- Profiles are named after their subfolder — auto-loaded when the tool processes that subfolder
- If no matching profile exists for a subfolder, interactive calibration is triggered automatically
- Profiles saved to a local JSON file (`profiles.json`)
- Terminal UI also allows manually selecting, creating, or editing profiles

**Interactive calibration:**
- Display first frame of the first video in the subfolder
- User clicks the two front corners of home plate
- Strike zone derived automatically: width = plate width, height = width × 1.5, bottom = 18in above plate
- Zone saved under the subfolder name

**Files to create:**
- `calibration.py` — profile load/save, interactive calibration UI
- `profiles.json` — persisted calibration profiles (gitignored)

**Completed:**
- User clicks two front corners of home plate — zone derived automatically (not 4 manual clicks)
- `Profile` dataclass stores plate corners and derives `zone_rect`, `pixels_per_inch`, and `plate_width_px`
- Zone bottom sits 18 inches above plate level (`STRIKE_ZONE_BOTTOM_OFFSET_INCHES = 18.0` in config)
- Zone height = plate width × 1.5 (`STRIKE_ZONE_HEIGHT_RATIO = 1.5` in config)
- Calibration window opens at 1280×720, previews derived zone after both clicks, R to reset, Esc to cancel
- Profiles saved/loaded from `profiles.json` — save/load roundtrip tested successfully

---

## Step 4 - Catch Frame Marking
- Each video contains one pitch — user marks one catch frame per video
- For each video, open an interactive playback window
- User controls:
  - `Space` — play/pause
  - `→` / `←` — step forward/backward one frame
  - `M` — mark current frame as the catch frame (pressing again moves the mark)
  - `Enter` — confirm mark and proceed to processing
  - `Q` — skip this video
- Marked catch frame displayed as overlay indicator on the frame
- Returns single catch frame number for processing

**Files to create:**
- `marker.py` — interactive playback window, catch frame marking UI

---

## Step 5 - Glove Detection & Tracking (MediaPipe)
- Use **MediaPipe Pose only** — Hands dropped due to unreliability with catcher's mitt
- Glove assumed to always be on the **left hand** (hardcoded)
- Primary glove position = **left wrist landmark** from Pose
- Also extract per frame:
  - Left elbow landmark (for Elbow Movement metric)
  - Left/right shoulder landmarks averaged (for Body Stability metric)
- Smooth all positions with a rolling average to reduce noise

**Files to create:**
- `glove_tracker.py` — MediaPipe Pose setup, per-frame landmark extraction, position smoothing

---

## Step 6 - Post-Catch Movement Analysis
- Starting from the marked catch frame, track glove position forward
- **Stop condition:** glove velocity drops below threshold (defined in `config.py`) — glove has settled
- **Max cap:** 2 seconds (converted to frames using video FPS at runtime)
- Compute:
  - Glove path from catch to settle
  - Direction: `Toward` or `Away` relative to the nearest strike zone edge
  - Total displacement magnitude
  - Elbow displacement from catch to settle
  - Shoulder/torso displacement from catch to settle

**Files to create:**
- `framing_analysis.py` — velocity calculation, path analysis, zone proximity math, direction determination

---

## Step 7 - Annotated Video Output
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
- `Direction` — `Toward` or `Away` relative to the nearest strike zone edge
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
├── marker.py
├── glove_tracker.py
├── framing_analysis.py
├── reporter.py
├── profiles.json        # gitignored — saved calibration profiles
├── videos/              # top-level input folder (gitignored)
│   ├── field-cam-A/     # example subfolder — one per camera setup
│   └── practice-1/      # example subfolder
└── PLAN.md
```

---

## Build Order

1. `requirements.txt` + `config.py`
2. `video_loader.py` (folder scan + video reading)
3. `calibration.py` (profiles + interactive zone calibration)
4. `marker.py` (catch frame marking UI)
5. `glove_tracker.py` (MediaPipe Pose landmark extraction)
6. `framing_analysis.py` (post-catch analysis + metrics)
7. `reporter.py` (annotated video output)
8. `main.py` (wires everything together)

---

## Decisions Made

| Decision | Choice |
|---|---|
| Strike zone definition | Interactive calibration, saved as named profiles |
| Calibration scope | One profile per batch; profiles reusable across sessions |
| Glove detection | MediaPipe Pose only — left wrist landmark (Hands dropped, unreliable with mitt) |
| Catching hand | Always left hand (hardcoded) |
| Pitch segmentation | Manual — user marks one catch frame per video during interactive playback |
| Catch frame marking | Press `M` to mark, press again to move the mark; `Enter` to confirm |
| Post-catch tracking window | Dynamic — track until glove velocity < threshold; 2s max cap |
| Direction reference | Nearest strike zone edge (not center) |
| Overall score | None — 6 individual metrics only |
| Batch input | Top-level `videos/` folder containing subfolders per camera setup |
| Skip logic | Subfolders where all videos have `_tracked` output are skipped automatically |
| Profile linking | Profile name matches subfolder name — auto-loaded, calibration triggered if missing |
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
