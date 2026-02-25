import os
from dataclasses import dataclass

import cv2

from config import SUPPORTED_EXTENSIONS


@dataclass
class VideoInfo:
    path: str
    fps: float
    frame_count: int
    width: int
    height: int

    @property
    def filename(self):
        return os.path.basename(self.path)

    @property
    def duration_seconds(self):
        return self.frame_count / self.fps if self.fps > 0 else 0


def scan_folder(folder_path):
    """Return a sorted list of video file paths found in folder_path."""
    videos = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(SUPPORTED_EXTENSIONS):
            videos.append(os.path.join(folder_path, filename))
    return videos


def get_video_info(video_path):
    """Open a video file and return a VideoInfo with its metadata."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cap.release()

    return VideoInfo(
        path=video_path,
        fps=fps,
        frame_count=frame_count,
        width=width,
        height=height,
    )


def read_frame(cap, frame_number):
    """Seek to frame_number and return that frame, or None if unavailable."""
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    return frame if ret else None
