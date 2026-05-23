"""
test_tracking.py — Phase 5 end-to-end PID tracking test (no laser).

Closes the loop for the first time: camera → detector → PID → servos.
Use this script to verify the loop runs and to tune PID gains in config.py.

Run on the Pi over VNC (it opens an OpenCV window):

    cd ~/pi && source venv/bin/activate
    python3 test_tracking.py

What you see:
    - The live camera feed in one window.
    - A red CROSS at the frame center (the target should be driven HERE).
    - A green CIRCLE at the detected target centroid (if any).
    - Overlay text showing current pan/tilt angles, pixel error,
      and the latest correction in degrees.

Controls:
    q — quit cleanly (servo cleanup centers the bracket, camera released).

On startup, servo.init() snaps both servos to their calibrated centers.
The DS3225 + LM2596 can handle the snap. Stay clear of the bracket's
sweep arc until it settles.

Behavior to watch for during tuning:
    GOOD  — target moves slowly → bracket follows → error converges → motion stops
    GOOD  — target moves fast and leaves FOV → bracket coasts in the last
            direction for up to COAST_MAX_FRAMES; overlay reads
            "COASTING (N frames left)" in orange
    BAD   — bracket tracks AWAY from target → flip sign of KP_PAN / KP_TILT
    BAD   — bracket oscillates around the target → reduce Kp (try half)
    BAD   — bracket reaches target but keeps drifting → too much I, or Kd negative
    BAD   — bracket settles slightly off-center forever → add a tiny Ki (0.001)
    BAD   — bracket lags far behind a moving target → increase Kp (try double)

The procedure is documented step-by-step in docs/plan/phase-5-pid-tracking.md.
"""

import logging
import sys

import cv2

import camera
import config
import detector
import servo
import tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

WINDOW_NAME = "tracking"


def _draw_overlay(display, target, result):
    """Draw the diagnostic overlay onto the display image (in place)."""
    # Frame-center crosshair — where we want the target to land.
    cv2.drawMarker(
        display, (config.FRAME_CENTER_X, config.FRAME_CENTER_Y),
        (0, 0, 255), cv2.MARKER_CROSS, markerSize=30, thickness=1,
    )

    # Target marker / status text.
    if target is not None:
        # Cyan circle when in deadband (locked), green when actively tracking.
        in_dead = result is not None and result.get("in_deadband", False)
        circle_color = (255, 255, 0) if in_dead else (0, 255, 0)
        cv2.circle(display, target, 8, circle_color, 2)

        status = "LOCKED (deadband)" if in_dead else "tracking"
        text_color = (255, 255, 0) if in_dead else (0, 255, 0)
        cv2.putText(
            display, f"target {target} — {status}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1,
        )
    elif result is not None and result.get("coasting"):
        # Target lost but we're still moving in the last direction.
        # Orange text + countdown so it's obvious from across the room.
        remaining = result.get("coast_remaining", 0)
        cv2.putText(
            display,
            f"target lost — COASTING ({remaining} frames left)",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1,
        )
    elif result is not None and result.get("recentering"):
        # Coast failed to find the target; bracket is ramping back to
        # PAN_CENTER / TILT_CENTER so the camera has its widest FOV ready.
        cv2.putText(
            display,
            "target lost — RECENTERING to home",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 105, 255), 1,
        )
    else:
        cv2.putText(
            display, "no target — holding position", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
        )

    # Servo + PID status. Two rows: pan info, tilt info.
    # Layout depends on the tracker state: no result (held), coasting (no
    # meaningful error), or normal tracking (have pixel error).
    pan = servo.current_pan()
    tilt = servo.current_tilt()

    if result is None:
        # No target this frame and not coasting — bracket holding position.
        pan_line = f"pan  {pan:6.1f}deg"
        tilt_line = f"tilt {tilt:6.1f}deg"
        line_color = (200, 200, 200)
    elif result.get("coasting"):
        # Coasting — pan_error/tilt_error are None on purpose. Show the
        # decaying correction so it's obvious what the bracket is doing.
        pan_line = (
            f"pan  {pan:6.1f}deg  COAST corr {result['pan_correction']:+6.2f}deg"
        )
        tilt_line = (
            f"tilt {tilt:6.1f}deg  COAST corr {result['tilt_correction']:+6.2f}deg"
        )
        line_color = (0, 165, 255)  # orange — matches the status text above
    elif result.get("recentering"):
        # Recentering — show the step size used this frame.
        pan_line = (
            f"pan  {pan:6.1f}deg  RECENTER step {result['pan_correction']:+5.2f}deg"
        )
        tilt_line = (
            f"tilt {tilt:6.1f}deg  RECENTER step {result['tilt_correction']:+5.2f}deg"
        )
        line_color = (180, 105, 255)  # purple — matches the status text above
    else:
        # Normal tracking (active or in-deadband). Pixel error is a real int.
        pan_line = (
            f"pan  {pan:6.1f}deg  err {result['pan_error']:+5d}px"
            f"  corr {result['pan_correction']:+6.2f}deg"
        )
        tilt_line = (
            f"tilt {tilt:6.1f}deg  err {result['tilt_error']:+5d}px"
            f"  corr {result['tilt_correction']:+6.2f}deg"
        )
        line_color = (255, 255, 255)

    cv2.putText(display, pan_line, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1)
    cv2.putText(display, tilt_line, (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, line_color, 1)


def main() -> int:
    log.info("Initializing servos (will snap to center)...")
    kit = servo.init()

    log.info("Initializing camera...")
    cam = camera.init()

    log.info("Initializing PID controllers...")
    pan_pid, tilt_pid = tracker.init()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    log.info("Tracking. Click the window, press 'q' to quit.")

    try:
        while True:
            frame = camera.capture_frame(cam)
            target = detector.detect(frame)
            result = tracker.update(pan_pid, tilt_pid, kit, target)

            display = frame.copy()
            _draw_overlay(display, target, result)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                log.info("Quit requested.")
                break

        return 0
    finally:
        # Order: stop sending PID corrections (by exiting the loop),
        # then center the servos, then release the camera.
        log.info("Shutting down...")
        tracker.stop(kit)
        camera.release(cam)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    sys.exit(main())
