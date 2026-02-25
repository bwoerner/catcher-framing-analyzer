import argparse
import os
import sys


DEFAULT_VIDEO_FOLDER = os.path.join(os.path.dirname(__file__), "videos")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Catcher Framing Analyzer — process a folder of pitch videos"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=DEFAULT_VIDEO_FOLDER,
        help="Path to folder containing video files (default: ./videos)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: folder not found: {args.folder}")
        sys.exit(1)

    print(f"Catcher Framing Analyzer")
    print(f"Input folder: {args.folder}")
    print("(not yet implemented)")


if __name__ == "__main__":
    main()
