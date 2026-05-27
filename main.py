"""
main.py — full laser tracker demo: tracking + firing.

This is the integrated end-to-end loop that brings every module of the
project together for a live demonstration:

    camera.capture_frame
      → detector.detect           (HSV thresholding on the target color)
      → tracker.update            (PID corrections, boresight-compensated,
                                   with coast + recenter behaviors)
      → servo.move_pan / move_tilt (clamped to calibrated limits)
      → laser.fire / laser.off    (operator-gated, with safety arm)

Run it on the Pi over VNC (it opens an OpenCV window):

    cd ~/pi && source venv/bin/activate
    python3 main.py

Or — recommended — from the control panel's "Run full demo" button,
which handles the GPIO hand-off cleanly.

UI states (a state machine — the top banner of the window always reflects
the current state):

    DISARMED  (gray)
        Tracking is live, the bracket follows the target, but the laser
        is locked OFF. This is the default at launch — the operator must
        deliberately arm the laser before any shot is possible.

    ARMED  (amber)
        Laser is ready to fire. The system is still tracking. Press F to
        fire, but the safety check (target LOCKED) still blocks the shot
        if the target isn't centered.

    LOCKED + ARMED  (pulsing green banner reading "LOCKED — PRESS F")
        Target is inside the deadband, meaning the pan/tilt error is small
        enough that the laser will land on the target. Pressing F now
        actually fires.

    FIRING  (red strobe)
        Laser pin is HIGH. Lasts FIRE_DURATION_S (0.5 s by default). The
        loop keeps running — camera and tracking continue — but no other
        fire command can be issued.

    COOLDOWN  (blue, with countdown)
        Laser just fired and is OFF. A short cooldown blocks rapid re-fires
        so the operator and demo audience can see what happened. After
        COOLDOWN_S (1 s) the state returns to ARMED.

Keyboard controls:
    a       toggle arm / disarm (laser safety)
    f       fire (requires ARMED + LOCKED + not in cooldown)
    q       quit cleanly (laser OFF, servos centered, camera released)

Safety:
    The laser is OFF on launch and on exit (try/finally + laser.cleanup).
    Arming is a deliberate keystroke. Firing requires arm + lock — random
    keypresses cannot accidentally fire.
"""

import logging
import math
import sys
import time
from typing import Optional

import cv2

import camera
import config
import detector
import laser
import servo
import tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


WINDOW_NAME = "Laser Tracker — Live Demo"

# State machine constants
S_DISARMED = "DISARMED"
S_ARMED    = "ARMED"
S_FIRING   = "FIRING"
S_COOLDOWN = "COOLDOWN"

# Timing
FIRE_DURATION_S: float = 0.5
COOLDOWN_S:      float = 1.0


# ---- Overlay rendering ----------------------------------------------------

def _put_text_centered(img, text, y, font_scale=1.0, color=(255, 255, 255),
                       thickness=2, shadow=True):
    """Draw text horizontally centered on the image at row y."""
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX,
                                  font_scale, thickness)
    x = (img.shape[1] - tw) // 2
    if shadow:
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, font_scale,
                    (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, font_scale,
                color, thickness, cv2.LINE_AA)


def _draw_banner(display, state, locked, cooldown_remaining):
    """Top banner — color and text depend on state."""
    h, w = display.shape[:2]
    banner_h = 56
    now = time.monotonic()

    if state == S_DISARMED:
        bg = (60, 60, 60)
        text = "DISARMED  —  press A to arm laser"
        fg = (220, 220, 220)
        scale = 0.85
    elif state == S_ARMED:
        if locked:
            # Pulsing green for "ready to fire"
            pulse = (math.sin(now * 6.0) + 1) / 2  # 0..1
            green = int(160 + 80 * pulse)
            bg = (0, green, 0)
            text = "★ LOCKED — PRESS F TO FIRE ★"
            fg = (255, 255, 255)
            scale = 0.95
        else:
            bg = (0, 165, 220)   # amber-ish
            text = "ARMED  —  acquiring target..."
            fg = (0, 0, 0)
            scale = 0.85
    elif state == S_FIRING:
        # Strobe: alternate between two reds at ~10 Hz
        strobe = int(now * 10) % 2
        bg = (0, 0, 220) if strobe else (0, 0, 100)
        text = "★  FIRING  ★"
        fg = (255, 255, 255)
        scale = 1.05
    elif state == S_COOLDOWN:
        bg = (140, 90, 30)   # cool blue-teal
        text = f"COOLDOWN  {cooldown_remaining:.1f}s"
        fg = (255, 255, 255)
        scale = 0.85
    else:
        bg = (0, 0, 0)
        text = state
        fg = (255, 255, 255)
        scale = 0.8

    cv2.rectangle(display, (0, 0), (w, banner_h), bg, -1)
    _put_text_centered(display, text, 40, font_scale=scale, color=fg, thickness=2)


def _draw_aim_and_target(display, target, in_deadband):
    """Cyan crosshair at the boresight-corrected aim point. Target marker."""
    # The crosshair should mark the pixel where the laser will land — i.e.,
    # frame_center + boresight_offset.
    aim_x = config.FRAME_CENTER_X + config.BORESIGHT_X_OFFSET
    aim_y = config.FRAME_CENTER_Y + config.BORESIGHT_Y_OFFSET
    cv2.drawMarker(display, (aim_x, aim_y), (255, 255, 0),
                   cv2.MARKER_CROSS, markerSize=28, thickness=2)
    cv2.circle(display, (aim_x, aim_y), 3, (255, 255, 0), -1)

    if target is not None:
        target_color = (0, 255, 0) if in_deadband else (0, 200, 255)
        cv2.circle(display, target, 14, target_color, 2)
        # tiny cross inside the circle
        cv2.line(display, (target[0] - 6, target[1]),
                 (target[0] + 6, target[1]), target_color, 1)
        cv2.line(display, (target[0], target[1] - 6),
                 (target[0], target[1] + 6), target_color, 1)


def _draw_info_strip(display, target, result):
    """Bottom strip with pan/tilt angles, pixel error, key legend."""
    h, w = display.shape[:2]
    strip_h = 60
    cv2.rectangle(display, (0, h - strip_h), (w, h), (28, 28, 28), -1)

    pan = servo.current_pan()
    tilt = servo.current_tilt()

    if result is not None and result.get("pan_error") is not None:
        info = (f"pan {pan:6.1f}°    tilt {tilt:6.1f}°    "
                f"err ({result['pan_error']:+4d}, {result['tilt_error']:+4d}) px")
    elif result is not None and result.get("coasting"):
        info = f"pan {pan:6.1f}°    tilt {tilt:6.1f}°    COASTING"
    elif result is not None and result.get("recentering"):
        info = f"pan {pan:6.1f}°    tilt {tilt:6.1f}°    RECENTERING"
    else:
        if target is None:
            info = f"pan {pan:6.1f}°    tilt {tilt:6.1f}°    no target"
        else:
            info = f"pan {pan:6.1f}°    tilt {tilt:6.1f}°    holding"

    cv2.putText(display, info, (14, h - 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    legend = "[A] arm  /  [F] fire  /  [Q] quit"
    (lw, _), _ = cv2.getTextSize(legend, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.putText(display, legend, (w - lw - 14, h - 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1, cv2.LINE_AA)

    # Boresight readout — small, lower-left. Helps the audience see that
    # the system is compensating for the camera-laser physical offset.
    bs = (f"boresight  dx={config.BORESIGHT_X_OFFSET:+d}  "
          f"dy={config.BORESIGHT_Y_OFFSET:+d}")
    cv2.putText(display, bs, (14, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1, cv2.LINE_AA)


# ---- Main loop ------------------------------------------------------------

def main() -> int:
    log.info("=== LASER TRACKER — FULL DEMO ===")
    log.info("Initializing servos...")
    kit = servo.init()
    log.info("Initializing camera...")
    cam = camera.init()
    log.info("Initializing PID controllers...")
    pan_pid, tilt_pid = tracker.init()
    log.info("Initializing laser (locked OFF)...")
    laser_dev = laser.init()

    state = S_DISARMED
    t_fire_start: float = 0.0
    cooldown_until: float = 0.0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 720)

    log.info("Demo running. A = arm, F = fire (when LOCKED), Q = quit.")

    try:
        while True:
            now = time.monotonic()

            # -------- State transitions driven by time --------
            if state == S_FIRING and now - t_fire_start >= FIRE_DURATION_S:
                laser.off(laser_dev)
                cooldown_until = now + COOLDOWN_S
                state = S_COOLDOWN
                log.info("Fire complete — cooling down for %.1fs.", COOLDOWN_S)
            elif state == S_COOLDOWN and now >= cooldown_until:
                state = S_ARMED
                log.info("Cooldown done — ARMED.")

            # -------- Capture + detect + track ----------------
            frame = camera.capture_frame(cam)
            target = detector.detect(frame)
            result = tracker.update(pan_pid, tilt_pid, kit, target)
            locked = result is not None and result.get("in_deadband", False)

            # -------- Draw everything onto a copy of the frame
            display = frame.copy()
            cooldown_remaining = max(0.0, cooldown_until - now)
            _draw_banner(display, state, locked, cooldown_remaining)
            _draw_aim_and_target(display, target, locked)
            _draw_info_strip(display, target, result)
            cv2.imshow(WINDOW_NAME, display)

            # -------- Handle key input ------------------------
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                log.info("Quit requested.")
                break
            elif key == ord('a'):
                if state == S_DISARMED:
                    state = S_ARMED
                    log.warning("★ LASER ARMED ★")
                elif state == S_ARMED:
                    state = S_DISARMED
                    log.info("Laser DISARMED.")
                else:
                    log.info("Cannot toggle arm during %s.", state)
            elif key == ord('f'):
                if state != S_ARMED:
                    log.warning("Fire ignored — state is %s (must be ARMED).", state)
                elif not locked:
                    log.warning("Fire ignored — target NOT LOCKED.")
                else:
                    log.warning("★ FIRE ★ — laser ON for %.2fs", FIRE_DURATION_S)
                    laser.fire(laser_dev)
                    t_fire_start = now
                    state = S_FIRING

            # User closed the window via the X button
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                log.info("Window closed.")
                break

        return 0

    finally:
        # Order matters: laser off FIRST (most safety-critical), then
        # release servos (which will re-center), then camera.
        log.info("Shutting down...")
        try:
            laser.cleanup(laser_dev)
        except Exception:
            log.exception("Laser cleanup failed")
        try:
            tracker.stop(kit)
        except Exception:
            log.exception("Tracker stop failed")
        try:
            camera.release(cam)
        except Exception:
            log.exception("Camera release failed")
        cv2.destroyAllWindows()
        log.info("Shutdown complete.")


if __name__ == "__main__":
    sys.exit(main())
