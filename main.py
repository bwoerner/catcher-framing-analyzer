import argparse
import os
import sys

from video_loader import scan_subfolders, scan_folder, get_video_info
from calibration import load_profiles, calibrate, save_profiles, Profile
from marker import mark_catch_frame
from glove_tracker import track_video
from framing_analysis import analyze

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
            cal_result = calibrate(videos[0])
            if cal_result is None:
                print("Calibration cancelled — skipping this folder.\n")
                continue
            plate_left, plate_right = cal_result
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
                print("  Skipped.")
                continue
            print(f"  Catch frame marked: {catch_frame}")

            # Step 5 — track full video with MediaPipe Pose
            print("  Tracking landmarks...")
            frames = track_video(v)

            # Step 6 — analyse post-catch movement
            result = analyze(frames, catch_frame, fps=info.fps, profile=profile)
            if result is None:
                print("  Analysis failed — insufficient data.")
                continue

            print("  --- Framing Analysis ---")
            print(f"  Glove Distance:  {result.glove_distance_in:.2f} in")
            print(f"  Glove Speed:     {result.glove_speed_in_s:.2f} in/s")
            print(f"  Direction:       {result.direction}")
            print(f"  Hold Time:       {result.hold_time_s:.2f} s")
            print(f"  Elbow Movement:  {result.elbow_movement_in:.2f} in  ({result.elbow_rating})")
            print(f"  Body Stability:  {result.body_stability_in:.2f} in  ({result.body_rating})")

        # TODO: Step 7 — reporter.py (annotated video output)

        print()


if __name__ == "__main__":
    main()
