import cv2

from config import COLOR_ZONE


def mark_catch_frame(video_path, profile):
    """
    Open an interactive playback window for video_path.
    User marks the single catch frame for this pitch.
    Returns the catch frame number, or None if skipped.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: could not open {video_path}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_delay = max(1, int(1000 / fps))  # ms per frame for real-speed playback

    current_frame = 0
    marked_frame = None
    playing = False
    need_seek = True  # only seek when jumping; sequential reads during playback

    cv2.namedWindow("Mark Catch Frame", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Mark Catch Frame", 1280, 720)

    while True:
        if need_seek:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            need_seek = False

        ret, frame = cap.read()
        if not ret:
            if playing:
                # End of video — loop back to the beginning
                current_frame = 0
                need_seek = True
            else:
                current_frame = max(0, current_frame - 1)
                need_seek = True
            continue

        current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

        display = frame.copy()

        # Draw strike zone
        x, y, w, h = profile.zone_rect
        cv2.rectangle(display, (x, y), (x + w, y + h), COLOR_ZONE, 2)

        # Instructions
        instructions = "Space: play/pause  |  A/D: step frame  |  M: mark catch  |  Enter: confirm  |  Q: skip"
        cv2.putText(display, instructions, (20, display.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.putText(display, instructions, (20, display.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)

        # Frame counter
        frame_label = f"Frame: {current_frame} / {total_frames - 1}"
        cv2.putText(display, frame_label, (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(display, frame_label, (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 1)

        # Marked frame indicator
        if marked_frame is not None:
            mark_label = f"CATCH FRAME: {marked_frame}"
            cv2.putText(display, mark_label, (20, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)

        cv2.imshow("Mark Catch Frame", display)

        key = cv2.waitKey(frame_delay if playing else 0)

        if playing and key == -1:
            # No key pressed — continue sequential playback (no seek needed)
            continue

        char = key & 0xFF

        if char == 32:  # Space — play/pause
            playing = not playing

        elif char == ord('a') or char == ord('A'):  # A — step back one frame
            playing = False
            current_frame = max(0, current_frame - 1)
            need_seek = True

        elif char == ord('d') or char == ord('D'):  # D — step forward one frame
            playing = False
            current_frame = min(current_frame + 1, total_frames - 1)
            need_seek = True

        elif char == ord('m') or char == ord('M'):  # Mark
            marked_frame = current_frame
            playing = False

        elif char == 13:  # Enter — confirm
            if marked_frame is not None:
                cv2.destroyWindow("Mark Catch Frame")
                cap.release()
                return marked_frame
            # Flash a reminder if no frame marked yet
            cv2.putText(display, "Mark a catch frame first (press M)",
                        (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
            cv2.imshow("Mark Catch Frame", display)
            cv2.waitKey(1000)

        elif char == ord('q') or char == ord('Q'):  # Skip
            cv2.destroyWindow("Mark Catch Frame")
            cap.release()
            return None
