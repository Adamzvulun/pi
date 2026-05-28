"""
tune_detector.py — interactive HSV-range tuner for the color detector.

How to use (must run on the Pi over VNC — opens OpenCV windows):

    1. VNC into LaserPi
    2. Open a terminal in the Pi desktop
    3. cd ~/pi && source venv/bin/activate
    4. python3 tune_detector.py
    5. Point the webcam at your target object with realistic lighting
    6. Drag the six trackbars until the MASK window shows the target as
       a clean white blob on a black background — no other white pixels
    7. Press 's' to print the current values to the terminal
    8. Hand-edit config.py — paste the printed HSV_LOWER and HSV_UPPER
       lines, replacing the placeholders
    9. Also record the final values and a description of the target
       object in docs/calibration.md

Controls:
    s — print the current HSV values to the terminal
    q — quit

This script does NOT write to config.py automatically. Hand-editing
prevents accidents (a runaway slider during shutdown could overwrite
good values), and forces you to consciously commit the calibration.

Why two windows:
    'feed'  shows the live BGR camera image with a green dot at the
            detected centroid (if any) — verifies the tuning is finding
            the right thing
    'mask'  shows the binary mask after blur + HSV thresh + erode/dilate
            — what detect() actually operates on. Want this clean.
"""

import logging
import sys

import cv2
import numpy as np

import camera

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# --- Trackbar definitions ---------------------------------------------------
# OpenCV's createTrackbar takes a maximum value. Hue in OpenCV is 0-179
# (half the usual 0-359 so it fits in a byte). Saturation and Value are 0-255.

_CONTROL_WINDOW = "controls"
_FEED_WINDOW = "feed"
_MASK_WINDOW = "mask"

# Default trackbar positions — wide-open ranges so any target shows up
# initially. User narrows them in from there.
_DEFAULTS = {
    "H_min": 0,   "H_max": 179,
    "S_min": 0,   "S_max": 255,
    "V_min": 0,   "V_max": 255,
}
_MAXES = {
    "H_min": 179, "H_max": 179,
    "S_min": 255, "S_max": 255,
    "V_min": 255, "V_max": 255,
}

# Match detector.py's pipeline exactly so what we see here is what
# detect() will see at runtime.
_BLUR_KERNEL = (5, 5)
_MORPH_ITERATIONS = 2
_MIN_AREA = 200  # mirrors config.MIN_CONTOUR_AREA — kept local so this
                 # tool stays independent of detector.py


def _noop(_value: int) -> None:
    """Trackbar callback that does nothing — we poll values each frame."""
    pass


def _read_trackbars() -> tuple[np.ndarray, np.ndarray]:
    """Read all six trackbars and return (HSV_LOWER, HSV_UPPER) arrays."""
    h_min = cv2.getTrackbarPos("H_min", _CONTROL_WINDOW)
    h_max = cv2.getTrackbarPos("H_max", _CONTROL_WINDOW)
    s_min = cv2.getTrackbarPos("S_min", _CONTROL_WINDOW)
    s_max = cv2.getTrackbarPos("S_max", _CONTROL_WINDOW)
    v_min = cv2.getTrackbarPos("V_min", _CONTROL_WINDOW)
    v_max = cv2.getTrackbarPos("V_max", _CONTROL_WINDOW)
    return (
        np.array([h_min, s_min, v_min]),
        np.array([h_max, s_max, v_max]),
    )


def _process(frame: np.ndarray, lower: np.ndarray, upper: np.ndarray):
    """
    Run the detector pipeline with the current slider values and return
    (mask, centroid). centroid is (cx, cy) or None.

    This duplicates detector.build_mask intentionally — detector.py reads
    from config.py, but here we want the LIVE slider values, not the
    saved ones.
    """
    blurred = cv2.GaussianBlur(frame, _BLUR_KERNEL, 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=_MORPH_ITERATIONS)
    mask = cv2.dilate(mask, None, iterations=_MORPH_ITERATIONS)

    centroid = None
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) >= _MIN_AREA:
            m = cv2.moments(largest)
            if m["m00"] != 0:
                centroid = (int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"]))

    return mask, centroid


def _print_values(lower: np.ndarray, upper: np.ndarray) -> None:
    """Print HSV values in a copy-pasteable format for config.py."""
    print()
    print("=" * 60)
    print("Current HSV range — paste into config.py:")
    print()
    print(f"HSV_LOWER: np.ndarray = np.array([{lower[0]}, {lower[1]}, {lower[2]}])"
          "   # [H_min, S_min, V_min]")
    print(f"HSV_UPPER: np.ndarray = np.array([{upper[0]}, {upper[1]}, {upper[2]}])"
          "  # [H_max, S_max, V_max]")
    print()
    print("Also record in docs/calibration.md along with target description")
    print("and lighting conditions.")
    print("=" * 60)
    print()


def main() -> int:
    cam = camera.init()
    try:
        cv2.namedWindow(_CONTROL_WINDOW, cv2.WINDOW_NORMAL)
        cv2.namedWindow(_FEED_WINDOW, cv2.WINDOW_NORMAL)
        cv2.namedWindow(_MASK_WINDOW, cv2.WINDOW_NORMAL)

        # Create all six trackbars on the control window.
        for name, default in _DEFAULTS.items():
            cv2.createTrackbar(name, _CONTROL_WINDOW, default, _MAXES[name], _noop)

        log.info("Tuner running. 's' = print values, 'q' = quit.")

        while True:
            frame = camera.capture_frame(cam)
            lower, upper = _read_trackbars()
            mask, centroid = _process(frame, lower, upper)

            # Draw centroid overlay on the live feed so you can confirm
            # detection is finding the actual target.
            display = frame.copy()
            if centroid is not None:
                cv2.circle(display, centroid, 8, (0, 255, 0), 2)
                cv2.putText(
                    display, f"{centroid}", (centroid[0] + 12, centroid[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
                )

            cv2.imshow(_FEED_WINDOW, display)
            cv2.imshow(_MASK_WINDOW, mask)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                log.info("Quit requested.")
                break
            if key == ord("s"):
                _print_values(lower, upper)

            # Detect window close (X button). cv2.imshow silently recreates
            # a window with the same name if it's gone, which made the
            # windows appear to "pop back up" when the user closed them.
            # Check all three; if any was closed, quit cleanly.
            for w in (_CONTROL_WINDOW, _FEED_WINDOW, _MASK_WINDOW):
                if cv2.getWindowProperty(w, cv2.WND_PROP_VISIBLE) < 1:
                    log.info("Window '%s' closed — exiting.", w)
                    return 0

        return 0
    finally:
        camera.release(cam)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    sys.exit(main())
