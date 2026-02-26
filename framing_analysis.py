import math
from dataclasses import dataclass

from config import (GLOVE_VELOCITY_THRESHOLD, MAX_HOLD_SECONDS,
                    ELBOW_GOOD_THRESHOLD, ELBOW_OK_THRESHOLD,
                    BODY_GOOD_THRESHOLD, BODY_OK_THRESHOLD)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

def _rate(value, good_threshold, ok_threshold):
    """Return 'Good', 'OK', or 'Needs Work' based on thresholds (lower is better)."""
    if value <= good_threshold:
        return "Good"
    elif value <= ok_threshold:
        return "OK"
    else:
        return "Needs Work"


@dataclass
class FramingResult:
    catch_frame: int
    settle_frame: int
    hold_time_s: float          # seconds from catch to settle
    glove_path: list            # [(x, y)] positions from catch to settle
    glove_distance_in: float    # net displacement catch→settle in inches
    glove_speed_in_s: float     # peak glove speed in inches/second
    direction: str              # "Toward" or "Away"
    elbow_movement_in: float    # elbow net displacement in inches
    elbow_rating: str           # Good / OK / Needs Work
    body_stability_in: float    # avg 4-point body frame displacement in inches
    body_rating: str            # Good / OK / Needs Work


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dist(a, b):
    """Euclidean distance between two (x, y) points."""
    if a is None or b is None:
        return 0.0
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _inside_zone(pos, zone_rect):
    """Return True if pos is inside zone_rect."""
    zx, zy, zw, zh = zone_rect
    return zx <= pos[0] <= zx + zw and zy <= pos[1] <= zy + zh


def _zone_center(zone_rect):
    zx, zy, zw, zh = zone_rect
    return (zx + zw / 2, zy + zh / 2)


def _nearest_zone_edge(pos, zone_rect):
    """Return the point on the nearest edge of zone_rect to pos."""
    zx, zy, zw, zh = zone_rect
    px, py = pos
    nearest_x = max(zx, min(px, zx + zw))
    nearest_y = max(zy, min(py, zy + zh))
    return (nearest_x, nearest_y)


def _direction(catch_pos, settle_pos, zone_rect):
    """
    Return 'Toward' or 'Away' based on where the glove started:
    - Outside zone: reference is the nearest zone edge
    - Inside zone:  reference is the zone center (holding it there is good framing)
    """
    if catch_pos is None or settle_pos is None:
        return "Unknown"

    if _inside_zone(catch_pos, zone_rect):
        reference = _zone_center(zone_rect)
    else:
        reference = _nearest_zone_edge(catch_pos, zone_rect)

    move_vec = (settle_pos[0] - catch_pos[0], settle_pos[1] - catch_pos[1])
    zone_vec = (reference[0] - catch_pos[0], reference[1] - catch_pos[1])

    dot = move_vec[0] * zone_vec[0] + move_vec[1] * zone_vec[1]
    return "Toward" if dot >= 0 else "Away"


def _body_displacement(frames, catch_idx, settle_idx):
    """
    Average displacement of the 4 body frame points from catch to settle.
    Returns displacement in pixels.
    """
    catch_f  = frames[catch_idx]
    settle_f = frames[settle_idx]

    points = [
        (catch_f.left_shoulder,  settle_f.left_shoulder),
        (catch_f.right_shoulder, settle_f.right_shoulder),
        (catch_f.left_hip,       settle_f.left_hip),
        (catch_f.right_hip,      settle_f.right_hip),
    ]

    dists = [_dist(c, s) for c, s in points if c is not None and s is not None]
    return sum(dists) / len(dists) if dists else 0.0


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------

def analyze(frames, catch_frame, fps, profile):
    """
    Analyse glove movement from catch_frame forward until the glove settles.

    Args:
        frames:      list of FrameLandmarks (full video, from glove_tracker)
        catch_frame: int — index of the catch frame
        fps:         float — video frame rate
        profile:     Profile — calibration profile (for zone_rect + pixels_per_inch)

    Returns:
        FramingResult, or None if insufficient data.
    """
    max_frames = int(MAX_HOLD_SECONDS * fps)
    ppi = profile.pixels_per_inch  # pixels per inch
    zone_rect = profile.zone_rect

    # Build the analysis window
    end_idx = min(catch_frame + max_frames, len(frames))
    window = frames[catch_frame:end_idx]

    if not window:
        return None

    # Find settle frame — first frame where glove velocity < threshold
    settle_idx = len(window) - 1  # default to end of window
    for i in range(1, len(window)):
        prev_wrist = window[i - 1].wrist
        curr_wrist = window[i].wrist
        velocity_px = _dist(prev_wrist, curr_wrist)
        if velocity_px < GLOVE_VELOCITY_THRESHOLD:
            settle_idx = i
            break

    settle_frame = catch_frame + settle_idx
    hold_time_s  = settle_idx / fps

    # Glove path
    glove_path = [f.wrist for f in window[:settle_idx + 1] if f.wrist is not None]

    # Net glove displacement (catch → settle) in inches
    catch_wrist  = window[0].wrist
    settle_wrist = window[settle_idx].wrist
    glove_dist_px = _dist(catch_wrist, settle_wrist)
    glove_distance_in = glove_dist_px / ppi

    # Peak glove speed in inches/second
    peak_speed_px_per_frame = 0.0
    for i in range(1, settle_idx + 1):
        v = _dist(window[i - 1].wrist, window[i].wrist)
        if v > peak_speed_px_per_frame:
            peak_speed_px_per_frame = v
    glove_speed_in_s = (peak_speed_px_per_frame * fps) / ppi

    # Direction
    direction = _direction(catch_wrist, settle_wrist, zone_rect)

    # Elbow displacement (catch → settle) in inches
    elbow_dist_px = _dist(window[0].elbow, window[settle_idx].elbow)
    elbow_movement_in = elbow_dist_px / ppi

    # Body stability — avg 4-point displacement in inches
    body_disp_px = _body_displacement(frames, catch_frame, settle_frame)
    body_stability_in = body_disp_px / ppi

    return FramingResult(
        catch_frame       = catch_frame,
        settle_frame      = settle_frame,
        hold_time_s       = hold_time_s,
        glove_path        = glove_path,
        glove_distance_in = glove_distance_in,
        glove_speed_in_s  = glove_speed_in_s,
        direction         = direction,
        elbow_movement_in = elbow_movement_in,
        elbow_rating      = _rate(elbow_movement_in, ELBOW_GOOD_THRESHOLD, ELBOW_OK_THRESHOLD),
        body_stability_in = body_stability_in,
        body_rating       = _rate(body_stability_in, BODY_GOOD_THRESHOLD, BODY_OK_THRESHOLD),
    )
