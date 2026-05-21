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

    # Target marker.
    if target is not None:
        cv2.circle(display, target, 8, (0, 255, 0), 2)
        cv2.putText(
            display, f"target {target}", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
        )
    else:
        cv2.putText(
            display, "no target — holding position", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1,
        )

    # Servo + PID status. Two rows: pan info, tilt info.
    pan = servo.current_pan()
    tilt = servo.current_tilt()

    if result is not None:
        cv2.putText(
            display,
            f"pan  {pan:6.1f}deg  err {result['pan_error']:+5d}px"
            f"  corr {result['pan_correction']:+6.2f}deg",
            (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
        )
        cv2.putText(
            display,
            f"tilt {tilt:6.1f}deg  err {result['tilt_error']:+5d}px"
            f"  corr {result['tilt_correction']:+6.2f}deg",
            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
        )
    else:
        cv2.putText(
            display, f"pan  {pan:6.1f}deg",
            (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
        )
        cv2.putText(
            display, f"tilt {tilt:6.1f}deg",
            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
        )


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
