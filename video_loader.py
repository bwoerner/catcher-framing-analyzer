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


def scan_subfolders(root_path):
    """
    Scan root_path for subfolders. Return a list of subfolder paths
    that have at least one unprocessed video (no _tracked output yet).
    """
    pending = []
    for name in sorted(os.listdir(root_path)):
        subfolder = os.path.join(root_path, name)
        if not os.path.isdir(subfolder) or name.startswith('.'):
            continue
        unprocessed = scan_folder(subfolder, skip_tracked=True)
        if unprocessed:
            pending.append(subfolder)
    return pending


def scan_folder(folder_path, skip_tracked=False):
    """
    Return a sorted list of video file paths found in folder_path.
    If skip_tracked=True, exclude videos that already have a _tracked output.
    """
    from config import OUTPUT_SUFFIX
    videos = []
    from config import OUTPUT_SUFFIX
    for filename in sorted(os.listdir(folder_path)):
        if not filename.lower().endswith(SUPPORTED_EXTENSIONS):
            continue
        # Skip files that are themselves _tracked outputs
        name, _ = os.path.splitext(filename)
        if name.endswith(OUTPUT_SUFFIX):
            continue
        if skip_tracked and _is_processed(folder_path, filename):
            continue
        videos.append(os.path.join(folder_path, filename))
    return videos


def _is_processed(folder_path, filename):
    """Return True if a _tracked output file exists for this video."""
    from config import OUTPUT_SUFFIX
    name, ext = os.path.splitext(filename)
    tracked_name = f"{name}{OUTPUT_SUFFIX}{ext}"
    return os.path.exists(os.path.join(folder_path, tracked_name))


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
