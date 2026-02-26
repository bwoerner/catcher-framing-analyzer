# Catcher Framing Analyzer

A Python tool for analyzing catcher framing technique from practice videos. It tracks glove and body movement using MediaPipe Pose and produces annotated output videos with framing metrics overlaid.

---

## What It Does

For each pitch video, the tool:
1. Lets you mark the catch frame interactively
2. Tracks the catcher's glove, elbow, and body using MediaPipe Pose
3. Measures post-catch glove movement from the catch to when the glove settles
4. Outputs an annotated video with the strike zone, body skeleton, glove path, and metrics panel

---

## Metrics

| Metric | Description |
|---|---|
| Glove Distance | Total glove displacement from catch to settle (inches) |
| Glove Speed | Peak glove velocity during framing movement (in/s) |
| Direction | `Toward` or `Away` relative to nearest strike zone edge |
| Hold Time | Seconds from catch frame to glove settling |
| Elbow Movement | Elbow displacement from catch to settle (inches) |
| Body Stability | Average displacement of shoulders + hips from catch to settle (inches) |

Elbow Movement and Body Stability include a qualitative rating: **Good**, **OK**, or **Needs Work**.

---

## Setup

**Requirements:** Python 3.9+

```bash
pip install -r requirements.txt
```

The MediaPipe pose model (~25 MB) is downloaded automatically on first run to the `models/` folder.

---

## Usage

### Folder structure

Organize videos in subfolders under `videos/` — one subfolder per camera setup or session:

```
videos/
├── field-cam-A/
│   ├── pitch_01.mp4
│   └── pitch_02.mp4
└── practice-2-23/
    └── IMG_5217.MOV
```

### Run

```bash
python main.py
```

Or point it at a different folder:

```bash
python main.py /path/to/videos
```

### First run for a new session folder

The tool will open a calibration window showing the first frame of the first video. Click the **left** then **right** front corners of home plate. The strike zone is derived automatically and the profile is saved under the subfolder name for future runs.

### Marking catch frames

For each video, an interactive playback window opens:

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `A` / `D` | Step backward / forward one frame |
| `M` | Mark current frame as the catch frame |
| `Enter` | Confirm and process |
| `Q` | Skip this video |

### Output

An annotated video is saved alongside the original:
```
pitch_01_tracked.mp4
```

Already-processed videos (with a `_tracked` file present) are skipped automatically on subsequent runs.

---

## Configuration

All tunable values are in `config.py`:

| Constant | Default | Description |
|---|---|---|
| `GLOVE_VELOCITY_THRESHOLD` | `2.0` px/frame | Velocity below which glove is considered settled |
| `MAX_HOLD_SECONDS` | `2.0` s | Maximum post-catch tracking window |
| `POSITION_SMOOTH_WINDOW` | `5` frames | Rolling average window for landmark smoothing |
| `HOME_PLATE_WIDTH_INCHES` | `17.0` in | Real-world plate width for px-to-inches conversion |
| `STRIKE_ZONE_HEIGHT_RATIO` | `1.5` | Zone height as a multiple of plate width |
| `STRIKE_ZONE_BOTTOM_OFFSET_INCHES` | `18.0` in | Height of zone bottom above plate level |
| `ELBOW_GOOD_THRESHOLD` | `3.0` in | Elbow movement threshold for "Good" rating |
| `ELBOW_OK_THRESHOLD` | `6.0` in | Elbow movement threshold for "OK" rating |
| `BODY_GOOD_THRESHOLD` | `2.0` in | Body stability threshold for "Good" rating |
| `BODY_OK_THRESHOLD` | `3.5` in | Body stability threshold for "OK" rating |

---

## Notes

- Glove is assumed to always be the **left hand** (hardcoded for standard catching stance)
- Pixel-to-inches conversion is anchored to home plate width (17 in) — approximate but sufficient for coaching feedback
- Calibration profiles are saved to `profiles.json` and reused automatically for any future session in the same subfolder
