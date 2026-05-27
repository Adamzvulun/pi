"""
calibrate_boresight.py — measure pixel offset between camera aim and laser dot.

Subprocess-launched from control_panel.py (via the "Boresight calibration..."
button). Opens a cv2 window with the live camera feed, fires the laser on
command, lets the operator confirm where the dot landed, and writes the
offset to config.py.

Why this is needed:
The camera and laser are physically offset on the tilt plate by a few
centimeters. They don't point at exactly the same spot. When the tracker
says "target is at frame center (320, 240)" and the system fires, the
laser dot lands at (320 + dx, 240 + dy) where (dx, dy) is the boresight
offset projected at the target's distance. Measuring (dx, dy) once at a
typical operating distance (~1.5m) lets the tracker compensate by shifting
the PID setpoint, so the laser hits the target instead of the camera's
exact aim point.

Workflow (each press of `f`):
    1. 3-second countdown overlay
    2. Laser fires briefly (~0.8s)
    3. A frame is captured while the laser is on
    4. Auto-detection finds the brightest red/saturated blob → that's the dot
    5. If auto-detection is off, operator clicks the actual dot
    6. Offset shown in real time; `s` saves to config.py

Keys (LIVE mode — looking at live feed):
    f         fire laser briefly + capture frame → REVIEW mode
    l         toggle continuous laser ON/OFF (for aiming the bracket)
    q         quit (no save)

Keys (REVIEW mode — looking at captured frame):
    mouse LMB click   place laser-dot marker at clicked position
    s         save offset to config.py + docs/calibration.md, then quit
    r         re-aim and re-fire (back to LIVE)
    q         quit without saving

Safety:
- Force laser OFF in finally block (even on exceptions / Ctrl+C / window close)
- Countdown gives operator time to look away if needed
- Continuous-ON ('l' key) only fires when explicitly toggled
- No auto-fire on startup — user has to press 'f'
"""

import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

import camera
import config
import laser

log = logging.getLogger(__name__)

WINDOW_NAME = "Boresight Calibration"

# Display colors (BGR)
CROSSHAIR_COLOR = (255, 255, 0)    # cyan — camera aim
DOT_MARKER_COLOR = (0, 0, 255)     # red  — detected/clicked laser dot
TEXT_COLOR = (255, 255, 255)
WARN_COLOR = (0, 0, 255)

# How long the laser stays on during the capture-fire sequence
FIRE_DURATION_S = 0.8
# Delay between laser-on and the frame grab — gives the auto-exposure time
# to stabilize on the new bright spot
CAPTURE_DELAY_S = 0.25
# Countdown duration before firing
COUNTDOWN_S = 3


# ---- Auto-detection of the laser dot --------------------------------------

def detect_laser_dot(frame: np.ndarray) -> Optional[Tuple[int, int]]:
    """
    Find the laser dot in a BGR frame. Returns (x, y) or None.

    Strategy is layered (saturated lasers wash out hue → check brightness too):
      1. Convert to HSV, look for very saturated AND very bright red pixels.
         Red wraps in OpenCV HSV — need two ranges (0-10 and 170-179).
      2. If nothing red matches, the dot likely saturated the sensor to white.
         Fall back to "extreme brightness anywhere" (V > 250 on a grayscale
         pass).
      3. Find contours, take the largest blob, return its centroid.

    Minimum contour area of 4 px filters out single-pixel noise.
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower1, upper1 = np.array([0, 80, 200]),   np.array([10, 255, 255])
    lower2, upper2 = np.array([170, 80, 200]), np.array([179, 255, 255])
    mask = cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    # Saturated-to-white fallback
    if int(mask.sum()) < 20:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)

    if int(mask.sum()) < 20:
        return None

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 4:
        return None

    m = cv2.moments(largest)
    if m["m00"] == 0:
        return None
    return int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])


# ---- Overlay rendering ----------------------------------------------------

def _put_text(img, text, pos, color=TEXT_COLOR, scale=0.6, thickness=2):
    """Draw text with a black drop-shadow for legibility on any background."""
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale,
                (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale,
                color, thickness, cv2.LINE_AA)


def draw_crosshair(img, cx, cy):
    cv2.line(img, (cx - 30, cy), (cx + 30, cy), CROSSHAIR_COLOR, 2)
    cv2.line(img, (cx, cy - 30), (cx, cy + 30), CROSSHAIR_COLOR, 2)
    cv2.circle(img, (cx, cy), 3, CROSSHAIR_COLOR, -1)


def draw_dot_marker(img, pos):
    cv2.drawMarker(img, pos, DOT_MARKER_COLOR, cv2.MARKER_CROSS, 24, 2)
    cv2.circle(img, pos, 14, DOT_MARKER_COLOR, 2)


def render_live(frame, laser_on):
    cx, cy = config.FRAME_CENTER_X, config.FRAME_CENTER_Y
    draw_crosshair(frame, cx, cy)
    _put_text(frame, "LIVE — aim crosshair at target", (10, 30))
    _put_text(frame, "f: fire & capture     l: toggle laser     q: quit",
              (10, 55), scale=0.55)
    if laser_on:
        _put_text(frame, "LASER ON", (frame.shape[1] - 160, 35),
                  color=WARN_COLOR, scale=0.8, thickness=2)
    return frame


def render_review(frame, dot_pos):
    cx, cy = config.FRAME_CENTER_X, config.FRAME_CENTER_Y
    draw_crosshair(frame, cx, cy)
    if dot_pos is not None:
        draw_dot_marker(frame, dot_pos)
        dx, dy = dot_pos[0] - cx, dot_pos[1] - cy
        _put_text(frame, f"Offset: dx={dx:+d}px  dy={dy:+d}px",
                  (10, frame.shape[0] - 50), scale=0.7)
    else:
        _put_text(frame, "No dot detected — click the laser dot to mark it",
                  (10, frame.shape[0] - 50), scale=0.6, color=WARN_COLOR)
    _put_text(frame, "REVIEW — click to relocate marker", (10, 30))
    _put_text(frame, "s: save & quit     r: re-fire     q: quit",
              (10, 55), scale=0.55)
    return frame


def render_countdown(frame, seconds_left):
    cx, cy = config.FRAME_CENTER_X, config.FRAME_CENTER_Y
    draw_crosshair(frame, cx, cy)
    _put_text(frame, f"FIRING IN {seconds_left}...",
              (cx - 140, cy + 90), color=WARN_COLOR, scale=1.2, thickness=3)
    return frame


# ---- config.py writer -----------------------------------------------------

def save_offset_to_config(dx: int, dy: int) -> Path:
    """
    Replace BORESIGHT_X_OFFSET / BORESIGHT_Y_OFFSET in config.py with the
    measured values. Preserves the surrounding comments and formatting.
    """
    config_path = Path(__file__).parent / "config.py"
    text = config_path.read_text(encoding="utf-8")

    text = re.sub(
        r"BORESIGHT_X_OFFSET\s*:\s*int\s*=\s*-?\d+",
        f"BORESIGHT_X_OFFSET: int = {dx}",
        text,
    )
    text = re.sub(
        r"BORESIGHT_Y_OFFSET\s*:\s*int\s*=\s*-?\d+",
        f"BORESIGHT_Y_OFFSET: int = {dy}",
        text,
    )

    config_path.write_text(text, encoding="utf-8")
    log.info("Wrote BORESIGHT_X_OFFSET=%+d  BORESIGHT_Y_OFFSET=%+d to %s",
             dx, dy, config_path)
    return config_path


# ---- Main loop ------------------------------------------------------------

class _State:
    """Tiny container so the mouse callback can mutate dot_pos."""
    def __init__(self):
        self.mode = "LIVE"               # "LIVE" or "REVIEW"
        self.dot_pos: Optional[Tuple[int, int]] = None
        self.captured_frame: Optional[np.ndarray] = None
        self.laser_on = False


def _make_mouse_cb(state: _State):
    def cb(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and state.mode == "REVIEW":
            state.dot_pos = (x, y)
            log.info("Marker placed at click: (%d, %d)", x, y)
    return cb


def _do_fire_and_capture(cap, laser_dev, state: _State) -> None:
    """Countdown → fire → grab frame → auto-detect → switch to REVIEW."""
    # Countdown
    for i in range(COUNTDOWN_S, 0, -1):
        f = camera.capture_frame(cap)
        f = render_countdown(f, i)
        cv2.imshow(WINDOW_NAME, f)
        cv2.waitKey(1000)

    log.info("Firing laser for ~%.1fs", FIRE_DURATION_S)
    laser.fire(laser_dev)
    state.laser_on = True
    try:
        # Let auto-exposure stabilize, then grab the frame
        time.sleep(CAPTURE_DELAY_S)
        state.captured_frame = camera.capture_frame(cap)
        # Brief extra on-time for visual confirmation
        time.sleep(max(0.0, FIRE_DURATION_S - CAPTURE_DELAY_S))
    finally:
        laser.off(laser_dev)
        state.laser_on = False

    state.dot_pos = detect_laser_dot(state.captured_frame)
    if state.dot_pos is None:
        log.warning("Auto-detection found no laser dot — click it manually.")
    else:
        log.info("Auto-detected laser dot at %s", state.dot_pos)
    state.mode = "REVIEW"


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    log.info("Boresight calibration starting...")
    cap = camera.init()
    laser_dev = laser.init()

    state = _State()

    try:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WINDOW_NAME, _make_mouse_cb(state))

        while True:
            if state.mode == "LIVE":
                frame = camera.capture_frame(cap)
                display = render_live(frame.copy(), state.laser_on)
            else:  # REVIEW
                display = render_review(state.captured_frame.copy(), state.dot_pos)

            cv2.imshow(WINDOW_NAME, display)
            key = cv2.waitKey(30) & 0xFF

            if key == ord('q'):
                log.info("Quitting without saving.")
                break

            if state.mode == "LIVE":
                if key == ord('f'):
                    _do_fire_and_capture(cap, laser_dev, state)
                elif key == ord('l'):
                    if state.laser_on:
                        laser.off(laser_dev)
                        state.laser_on = False
                    else:
                        laser.fire(laser_dev)
                        state.laser_on = True
            else:  # REVIEW
                if key == ord('r'):
                    state.mode = "LIVE"
                    state.captured_frame = None
                    state.dot_pos = None
                elif key == ord('s'):
                    if state.dot_pos is None:
                        log.warning("No dot marked — click the dot before saving.")
                        continue
                    cx, cy = config.FRAME_CENTER_X, config.FRAME_CENTER_Y
                    dx = state.dot_pos[0] - cx
                    dy = state.dot_pos[1] - cy
                    save_offset_to_config(dx, dy)
                    log.info("Saved. Update docs/calibration.md with the new offsets.")
                    break

            # Window close (X button)
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                log.info("Window closed.")
                break

    finally:
        # Belt-and-braces: even if something blew up, the laser must be off.
        try:
            laser.cleanup(laser_dev)
        except Exception:
            log.exception("Laser cleanup failed during shutdown")
        try:
            camera.release(cap)
        except Exception:
            log.exception("Camera release failed during shutdown")
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
