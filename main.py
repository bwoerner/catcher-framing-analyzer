import argparse
import os
import sys

from video_loader import scan_subfolders, scan_folder, get_video_info
from calibration import load_profiles, calibrate, save_profiles, Profile
from marker import mark_catch_frame

DEFAULT_VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "videos")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Catcher Framing Analyzer — process a folder of pitch videos"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=DEFAULT_VIDEO_FOLDER,
        help="Path to top-level folder containing subfolders of videos (default: ./videos)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: folder not found: {args.folder}")
        sys.exit(1)

    print("Catcher Framing Analyzer")
    print(f"Scanning: {args.folder}\n")

    subfolders = scan_subfolders(args.folder)
    if not subfolders:
        print("No subfolders with unprocessed videos found.")
        sys.exit(0)

    print(f"Found {len(subfolders)} subfolder(s) to process.\n")

    for subfolder in subfolders:
        name = os.path.basename(subfolder)
        print(f"=== {name} ===")

        # Load or create calibration profile
        profiles = load_profiles()
        if name in profiles:
            profile = profiles[name]
            print(f"Profile '{profile.name}' loaded — zone rect: {profile.zone_rect}")
        else:
            print(f"No profile found for '{name}' — starting calibration...")
            videos = scan_folder(subfolder, skip_tracked=True)
            result = calibrate(videos[0])
            if result is None:
                print("Calibration cancelled — skipping this folder.\n")
                continue
            plate_left, plate_right = result
            profile = Profile(name=name, plate_left=plate_left, plate_right=plate_right)
            profiles[name] = profile
            save_profiles(profiles)
            print(f"Profile '{name}' saved — zone rect: {profile.zone_rect}")

        # Step 4 — mark catch frame for each unprocessed video
        videos = scan_folder(subfolder, skip_tracked=True)
        print(f"{len(videos)} unprocessed video(s):")
        for v in videos:
            info = get_video_info(v)
            print(f"\n  {info.filename} — {info.fps:.0f}fps, {info.frame_count} frames, {info.duration_seconds:.1f}s")
            catch_frame = mark_catch_frame(v, profile)
            if catch_frame is None:
                print(f"  Skipped.")
                continue
            print(f"  Catch frame marked: {catch_frame}")

        # TODO: Step 5 — glove_tracker.py (MediaPipe tracking)
        # TODO: Step 6 — framing_analysis.py (metrics)
        # TODO: Step 7 — reporter.py (annotated video output)

        print()


if __name__ == "__main__":
    main()
