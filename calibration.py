import json
import math
import os
from dataclasses import dataclass

import cv2

from config import HOME_PLATE_WIDTH_INCHES, STRIKE_ZONE_HEIGHT_RATIO, STRIKE_ZONE_BOTTOM_OFFSET_INCHES, COLOR_ZONE

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")


@dataclass
class Profile:
    name: str
    plate_left: tuple   # (x, y) — left front corner of home plate
    plate_right: tuple  # (x, y) — right front corner of home plate

    @property
    def plate_width_px(self):
        """Pixel distance between the two plate corners."""
        dx = self.plate_right[0] - self.plate_left[0]
        dy = self.plate_right[1] - self.plate_left[1]
        return math.hypot(dx, dy)

    @property
    def pixels_per_inch(self):
        return self.plate_width_px / HOME_PLATE_WIDTH_INCHES

    @property
    def zone_rect(self):
        """
        Return (x, y, w, h) strike zone rectangle derived from plate corners.
        Width matches plate width, height = width * STRIKE_ZONE_HEIGHT_RATIO.
        Bottom of zone sits STRIKE_ZONE_BOTTOM_OFFSET_INCHES above the plate level.
        """
        cx = (self.plate_left[0] + self.plate_right[0]) / 2
        cy = (self.plate_left[1] + self.plate_right[1]) / 2
        w = int(self.plate_width_px)
        h = int(w * STRIKE_ZONE_HEIGHT_RATIO)
        bottom_offset_px = STRIKE_ZONE_BOTTOM_OFFSET_INCHES * self.pixels_per_inch
        x = int(cx - w / 2)
        y = int(cy - h - bottom_offset_px)
        return x, y, w, h

    def to_dict(self):
        return {
            "name": self.name,
            "plate_left": list(self.plate_left),
            "plate_right": list(self.plate_right),
        }

    @staticmethod
    def from_dict(d):
        return Profile(
            name=d["name"],
            plate_left=tuple(d["plate_left"]),
            plate_right=tuple(d["plate_right"]),
        )


# ---------------------------------------------------------------------------
# Profile persistence
# ---------------------------------------------------------------------------

def load_profiles():
    """Load all profiles from profiles.json. Returns dict of name -> Profile."""
    if not os.path.exists(PROFILES_PATH):
        return {}
    with open(PROFILES_PATH, "r") as f:
        data = json.load(f)
    return {p["name"]: Profile.from_dict(p) for p in data}


def save_profiles(profiles):
    """Save profiles dict to profiles.json."""
    with open(PROFILES_PATH, "w") as f:
        json.dump([p.to_dict() for p in profiles.values()], f, indent=2)


# ---------------------------------------------------------------------------
# Interactive calibration
# ---------------------------------------------------------------------------

def _calibrate_window(frame):
    """
    Show frame in an OpenCV window.
    User clicks the left then right front corners of home plate.
    Returns (plate_left, plate_right) or None if cancelled.
    """
    clicks = []
    labels = ["Left front corner of plate", "Right front corner of plate"]

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 2:
            clicks.append((x, y))

    cv2.namedWindow("Calibrate — Home Plate", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Calibrate — Home Plate", 1280, 720)
    cv2.setMouseCallback("Calibrate — Home Plate", mouse_callback)

    while True:
        display = frame.copy()

        # Current instruction
        step = len(clicks)
        instruction = labels[step] if step < 2 else "Press Enter to confirm  |  R to reset  |  Esc to cancel"
        cv2.putText(display, instruction, (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, instruction, (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)

        # Draw clicked plate corners
        for i, (x, y) in enumerate(clicks):
            cv2.circle(display, (x, y), 6, (0, 165, 255), -1)
            corner_label = "L" if i == 0 else "R"
            cv2.putText(display, corner_label, (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)

        # Preview derived strike zone once both corners are clicked
        if len(clicks) == 2:
            profile = Profile(name="preview", plate_left=clicks[0], plate_right=clicks[1])
            x, y, w, h = profile.zone_rect
            cv2.rectangle(display, (x, y), (x + w, y + h), COLOR_ZONE, 2)
            cv2.putText(display, "Strike Zone", (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_ZONE, 1)

        cv2.imshow("Calibrate — Home Plate", display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord('r') or key == ord('R'):
            clicks.clear()
        elif key == 13 and len(clicks) == 2:  # Enter
            cv2.destroyWindow("Calibrate — Home Plate")
            return clicks[0], clicks[1]
        elif key == 27:  # Esc
            cv2.destroyWindow("Calibrate — Home Plate")
            return None


def calibrate(video_path):
    """Open first frame of video and run interactive plate calibration. Returns (left, right) or None."""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print(f"Error: could not read first frame of {video_path}")
        return None
    return _calibrate_window(frame)


# ---------------------------------------------------------------------------
# Profile selection UI (terminal)
# ---------------------------------------------------------------------------

def select_profile(video_path):
    """
    Terminal UI to select or create a calibration profile.
    Returns a Profile, or None if the user quits.
    """
    profiles = load_profiles()

    while True:
        print("\n--- Calibration Profiles ---")
        if profiles:
            for i, name in enumerate(profiles, 1):
                print(f"  {i}. {name}")
        else:
            print("  (no profiles saved)")

        print("\n  N. New profile")
        if profiles:
            print("  E. Edit existing profile")
        print("  Q. Quit")

        choice = input("\nSelect a profile or action: ").strip()

        if choice.upper() == 'Q':
            return None

        if choice.upper() == 'N':
            name = input("Enter a name for the new profile: ").strip()
            if not name:
                print("Profile name cannot be empty.")
                continue
            result = calibrate(video_path)
            if result is None:
                print("Calibration cancelled.")
                continue
            plate_left, plate_right = result
            profile = Profile(name=name, plate_left=plate_left, plate_right=plate_right)
            profiles[name] = profile
            save_profiles(profiles)
            print(f"Profile '{name}' saved.")
            return profile

        if choice.upper() == 'E' and profiles:
            name = input("Enter the name of the profile to edit: ").strip()
            if name not in profiles:
                print(f"Profile '{name}' not found.")
                continue
            result = calibrate(video_path)
            if result is None:
                print("Calibration cancelled.")
                continue
            plate_left, plate_right = result
            profiles[name] = Profile(name=name, plate_left=plate_left, plate_right=plate_right)
            save_profiles(profiles)
            print(f"Profile '{name}' updated.")
            return profiles[name]

        if choice.isdigit():
            idx = int(choice) - 1
            names = list(profiles.keys())
            if 0 <= idx < len(names):
                return profiles[names[idx]]
            print("Invalid selection.")
            continue

        print("Invalid input, please try again.")
