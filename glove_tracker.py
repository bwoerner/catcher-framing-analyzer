import os
import urllib.request
from collections import deque
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from config import POSITION_SMOOTH_WINDOW

# ---------------------------------------------------------------------------
# Model download
# ---------------------------------------------------------------------------

MODEL_DIR  = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "pose_landmarker_full.task")
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_full/float16/latest/"
    "pose_landmarker_full.task"
)


def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        os.makedirs(MODEL_DIR, exist_ok=True)
        print("Downloading MediaPipe pose model (one-time)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")


# ---------------------------------------------------------------------------
# Landmark indices (same across API versions)
# ---------------------------------------------------------------------------

WRIST_IDX       = 15  # LEFT_WRIST
ELBOW_IDX       = 13  # LEFT_ELBOW
L_SHOULDER_IDX  = 11  # LEFT_SHOULDER
R_SHOULDER_IDX  = 12  # RIGHT_SHOULDER
L_HIP_IDX       = 23  # LEFT_HIP
R_HIP_IDX       = 24  # RIGHT_HIP


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class FrameLandmarks:
    frame_number: int
    wrist: tuple         # (x, y) px — left wrist / glove position
    elbow: tuple         # (x, y) px — left elbow
    left_shoulder: tuple
    right_shoulder: tuple
    left_hip: tuple
    right_hip: tuple

    @property
    def body_center(self):
        """Average of the 4 body frame points (shoulders + hips)."""
        points = [p for p in [self.left_shoulder, self.right_shoulder,
                               self.left_hip, self.right_hip] if p is not None]
        if not points:
            return None
        return (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_px(landmark, width, height):
    """Convert a normalised landmark to pixel coords, or None if low visibility."""
    if landmark is None or landmark.visibility < 0.3:
        return None
    return (int(landmark.x * width), int(landmark.y * height))


def _smooth(values, window):
    """Rolling average over a list of (x, y) tuples (Nones pass through)."""
    smoothed = []
    buf = deque(maxlen=window)
    for v in values:
        if v is not None:
            buf.append(v)
        if buf:
            smoothed.append((
                sum(p[0] for p in buf) / len(buf),
                sum(p[1] for p in buf) / len(buf),
            ))
        else:
            smoothed.append(None)
    return smoothed


# ---------------------------------------------------------------------------
# Main tracking function
# ---------------------------------------------------------------------------

def track_video(video_path):
    """
    Run MediaPipe Pose on every frame of video_path.
    Returns a list of FrameLandmarks (one per frame) with smoothed positions.
    """
    _ensure_model()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)

    BaseOptions          = mp.tasks.BaseOptions
    PoseLandmarker       = mp.tasks.vision.PoseLandmarker
    PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
    VisionRunningMode    = mp.tasks.vision.RunningMode

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    raw = {k: [] for k in ["wrist", "elbow", "left_shoulder",
                            "right_shoulder", "left_hip", "right_hip"]}
    frame_numbers = []
    frame_idx = 0

    with PoseLandmarker.create_from_options(options) as landmarker:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp_ms = int((frame_idx / fps) * 1000)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                                data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            lm = result.pose_landmarks[0] if result.pose_landmarks else None

            def get(idx):
                return _to_px(lm[idx] if lm else None, width, height)

            raw["wrist"].append(get(WRIST_IDX))
            raw["elbow"].append(get(ELBOW_IDX))
            raw["left_shoulder"].append(get(L_SHOULDER_IDX))
            raw["right_shoulder"].append(get(R_SHOULDER_IDX))
            raw["left_hip"].append(get(L_HIP_IDX))
            raw["right_hip"].append(get(R_HIP_IDX))
            frame_numbers.append(frame_idx)
            frame_idx += 1

    cap.release()

    smoothed = {k: _smooth(v, POSITION_SMOOTH_WINDOW) for k, v in raw.items()}

    return [
        FrameLandmarks(
            frame_number   = frame_numbers[i],
            wrist          = smoothed["wrist"][i],
            elbow          = smoothed["elbow"][i],
            left_shoulder  = smoothed["left_shoulder"][i],
            right_shoulder = smoothed["right_shoulder"][i],
            left_hip       = smoothed["left_hip"][i],
            right_hip      = smoothed["right_hip"][i],
        )
        for i in range(len(frame_numbers))
    ]
