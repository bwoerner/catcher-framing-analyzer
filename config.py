# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------

# Glove velocity (px/frame) below which the glove is considered settled
GLOVE_VELOCITY_THRESHOLD = 2.0

# Maximum post-catch window in seconds before forcing a settle
MAX_HOLD_SECONDS = 2.0

# Rolling average window size for smoothing landmark positions (frames)
POSITION_SMOOTH_WINDOW = 5

# ---------------------------------------------------------------------------
# Calibration / measurement
# ---------------------------------------------------------------------------

# Real-world width of home plate in inches — used for px-to-inches conversion
HOME_PLATE_WIDTH_INCHES = 17.0

# Strike zone height as a multiplier of plate width (approx 1.5x for average batter)
STRIKE_ZONE_HEIGHT_RATIO = 1.5

# How far the bottom of the strike zone sits above the plate level (inches)
STRIKE_ZONE_BOTTOM_OFFSET_INCHES = 18.0

# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------

# Supported input video extensions
SUPPORTED_EXTENSIONS = (".mp4", ".mov", ".avi")

# Suffix appended to output video filenames
OUTPUT_SUFFIX = "_tracked"

# ---------------------------------------------------------------------------
# Qualitative rating thresholds (inches)
# ---------------------------------------------------------------------------

# Elbow movement: how much the elbow moves from catch to settle
ELBOW_GOOD_THRESHOLD       = 3.0   # < 3 in  → Good
ELBOW_OK_THRESHOLD         = 6.0   # 3–6 in  → OK,  > 6 in → Needs Work

# Body stability: average 4-point body frame displacement from catch to settle
BODY_GOOD_THRESHOLD        = 2.0   # < 2 in  → Good
BODY_OK_THRESHOLD          = 3.5   # 2–3.5 in → OK,  > 3.5 in → Needs Work

# ---------------------------------------------------------------------------
# Overlay
# ---------------------------------------------------------------------------

# Metrics panel position (pixels from edge)
OVERLAY_MARGIN = 20

# Font scale and thickness for overlay text
OVERLAY_FONT_SCALE = 0.6
OVERLAY_FONT_THICKNESS = 1

# Colors (BGR)
COLOR_ZONE = (0, 255, 0)             # Strike zone rectangle — green
COLOR_GLOVE = (0, 165, 255)          # Glove dot — orange
COLOR_PATH = (255, 255, 0)           # Glove path trail — cyan
COLOR_SKELETON = (200, 200, 200)     # Pose skeleton — light grey
COLOR_OVERLAY_BG = (0, 0, 0)         # Metrics panel background — black
COLOR_OVERLAY_TEXT = (255, 255, 255) # Metrics panel text — white
