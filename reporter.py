import os

import cv2

from config import (
    OUTPUT_SUFFIX,
    OVERLAY_MARGIN, OVERLAY_FONT_SCALE, OVERLAY_FONT_THICKNESS,
    COLOR_ZONE, COLOR_GLOVE, COLOR_PATH, COLOR_SKELETON,
    COLOR_OVERLAY_BG, COLOR_OVERLAY_TEXT,
)

FONT = cv2.FONT_HERSHEY_SIMPLEX


def _ipt(pt):
    """Convert a float (x, y) tuple to int, as required by OpenCV drawing functions."""
    return (int(pt[0]), int(pt[1]))

# Connections between the 6 stored landmarks for the skeleton overlay
SKELETON_CONNECTIONS = [
    ("left_shoulder",  "right_shoulder"),  # across shoulders
    ("left_shoulder",  "elbow"),           # upper arm
    ("elbow",          "wrist"),           # forearm
    ("left_shoulder",  "left_hip"),        # left torso
    ("right_shoulder", "right_hip"),       # right torso
    ("left_hip",       "right_hip"),       # across hips
]


# ---------------------------------------------------------------------------
# Per-frame drawing helpers
# ---------------------------------------------------------------------------

def _draw_zone(frame, profile):
    x, y, w, h = profile.zone_rect
    cv2.rectangle(frame, (x, y), (x + w, y + h), COLOR_ZONE, 2)


def _draw_skeleton(frame, fl):
    pts = {
        "wrist":          fl.wrist,
        "elbow":          fl.elbow,
        "left_shoulder":  fl.left_shoulder,
        "right_shoulder": fl.right_shoulder,
        "left_hip":       fl.left_hip,
        "right_hip":      fl.right_hip,
    }
    for a, b in SKELETON_CONNECTIONS:
        pa, pb = pts.get(a), pts.get(b)
        if pa is not None and pb is not None:
            cv2.line(frame, _ipt(pa), _ipt(pb), COLOR_SKELETON, 2)
    for pt in pts.values():
        if pt is not None:
            cv2.circle(frame, _ipt(pt), 4, COLOR_SKELETON, -1)


def _draw_glove(frame, wrist):
    if wrist is not None:
        cv2.circle(frame, _ipt(wrist), 8, COLOR_GLOVE, -1)


def _draw_trail(frame, trail):
    for i in range(1, len(trail)):
        if trail[i - 1] is not None and trail[i] is not None:
            cv2.line(frame, _ipt(trail[i - 1]), _ipt(trail[i]), COLOR_PATH, 2)


def _draw_metrics_panel(frame, result):
    """
    Draw a two-column metrics panel in the top-left corner.
    Uses font-aware column widths so values align regardless of label length.
    """
    m     = OVERLAY_MARGIN
    scale = OVERLAY_FONT_SCALE
    thick = OVERLAY_FONT_THICKNESS
    pad   = 10

    header = "FRAMING ANALYSIS"
    rows = [
        ("Glove Distance", f"{result.glove_distance_in:.1f} in"),
        ("Glove Speed",    f"{result.glove_speed_in_s:.1f} in/s"),
        ("Direction",      result.direction),
        ("Hold Time",      f"{result.hold_time_s:.1f} s"),
        ("Elbow Movement", f"{result.elbow_movement_in:.1f} in  {result.elbow_rating}"),
        ("Body Stability", f"{result.body_stability_in:.1f} in  {result.body_rating}"),
    ]

    line_h = int(scale * 28) + 6

    header_w    = cv2.getTextSize(header, FONT, scale, thick)[0][0]
    max_label_w = max(cv2.getTextSize(lbl, FONT, scale, thick)[0][0] for lbl, _ in rows)
    max_value_w = max(cv2.getTextSize(val, FONT, scale, thick)[0][0] for _, val in rows)

    col_gap = 14
    panel_w = max(header_w, max_label_w + col_gap + max_value_w) + pad * 2
    panel_h = (1 + len(rows)) * line_h + 8 + pad * 2

    # Background
    cv2.rectangle(frame, (m, m), (m + panel_w, m + panel_h), COLOR_OVERLAY_BG, -1)

    # Header
    cv2.putText(frame, header,
                (m + pad, m + pad + line_h - 4),
                FONT, scale, COLOR_OVERLAY_TEXT, thick, cv2.LINE_AA)

    # Separator line
    sep_y = m + pad + line_h + 3
    cv2.line(frame,
             (m + pad, sep_y), (m + panel_w - pad, sep_y),
             COLOR_OVERLAY_TEXT, 1)

    # Metric rows — label in left column, value in right column
    value_x = m + pad + max_label_w + col_gap
    for i, (label, value) in enumerate(rows):
        y = sep_y + 6 + (i + 1) * line_h - 4
        cv2.putText(frame, label, (m + pad, y),
                    FONT, scale, COLOR_OVERLAY_TEXT, thick, cv2.LINE_AA)
        cv2.putText(frame, value, (value_x, y),
                    FONT, scale, COLOR_OVERLAY_TEXT, thick, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Main output function
# ---------------------------------------------------------------------------

def write_tracked_video(video_path, frames, result, profile):
    """
    Write an annotated output video alongside the original.

    Overlays per frame:
    - Strike zone rectangle
    - Simplified 6-point skeleton
    - Glove dot
    - Post-catch glove path trail (grows from catch frame to settle frame,
      then holds for the remainder of the video)
    - Metrics panel in top-left corner

    Returns the output file path.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    base, ext = os.path.splitext(video_path)
    output_path = base + OUTPUT_SUFFIX + ext

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    trail = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        fl = frames[frame_idx] if frame_idx < len(frames) else None

        _draw_zone(frame, profile)

        if fl is not None:
            _draw_skeleton(frame, fl)
            _draw_glove(frame, fl.wrist)

        # Accumulate trail from catch to settle; hold full trail afterwards
        if fl is not None and fl.wrist is not None:
            if result.catch_frame <= frame_idx <= result.settle_frame:
                trail.append(fl.wrist)

        _draw_trail(frame, trail)
        _draw_metrics_panel(frame, result)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()

    return output_path
