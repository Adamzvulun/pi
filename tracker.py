"""
tracker.py — closed-loop PID tracking glue.

Sits between detector.py and servo.py. Takes a target pixel position from
the detector, computes the error from frame center, runs two independent
PID controllers (one per axis), and commands servo movement to drive the
error toward zero.

This is the ONLY module in the project that uses simple_pid. If the
control strategy ever changes (different controller, kalman filter,
ML-based), it changes here — callers just see `update(...)`.

Public API:
    init()                                  → (pan_pid, tilt_pid)
    update(pan_pid, tilt_pid, kit, target)  → result dict or None
    stop(kit)                               → cleans up servos

How the loop works:
    target_x, target_y = target_pos              # from detector.detect()
    pan_error  = target_x - FRAME_CENTER_X       # +ve = target right of center
    tilt_error = target_y - FRAME_CENTER_Y       # +ve = target BELOW center
                                                 # (OpenCV y increases downward)
    pan_correction  = pan_pid(pan_error)         # degrees to add to current pan
    tilt_correction = tilt_pid(tilt_error)       # degrees to add to current tilt
    servo.move_pan(kit, current_pan + pan_correction)    # clamped by servo.py
    servo.move_tilt(kit, current_tilt + tilt_correction)

When target is None (detector found nothing), update() does nothing —
the bracket holds its last commanded position. No PID state is updated
either, so when the target reappears the integral doesn't have stale
accumulation from the no-target gap.

Sign convention / mounting caveat:
    simple_pid computes error = setpoint - process_value. We use
    setpoint=0 and feed in (target - center). For positive Kp, the
    correction sign comes out OPPOSITE to the error sign. Whether that
    matches our bracket's mechanical orientation is unknown until we
    test — if the bracket tracks AWAY from the target on first run,
    flip the sign of KP_PAN or KP_TILT in config.py.
"""

import logging
from typing import Dict, Optional, Tuple

from simple_pid import PID

import config
import servo

log = logging.getLogger(__name__)


def init() -> Tuple[PID, PID]:
    """
    Create the two PID controllers using gains from config.py.

    setpoint=0 because we feed the controller the error directly
    (target - center), and the goal is to drive that error to zero.

    output_limits caps the per-update correction so a sudden far-corner
    target doesn't request a huge single-step swing. The clamp matches
    PID_OUTPUT_LIMIT in config.py.
    """
    pan_pid = PID(
        config.KP_PAN, config.KI_PAN, config.KD_PAN,
        setpoint=0,
        output_limits=(-config.PID_OUTPUT_LIMIT, config.PID_OUTPUT_LIMIT),
    )
    tilt_pid = PID(
        config.KP_TILT, config.KI_TILT, config.KD_TILT,
        setpoint=0,
        output_limits=(-config.PID_OUTPUT_LIMIT, config.PID_OUTPUT_LIMIT),
    )
    log.info(
        "PID init — pan Kp=%.3f Ki=%.3f Kd=%.3f, tilt Kp=%.3f Ki=%.3f Kd=%.3f, "
        "output limit ±%.1f°",
        config.KP_PAN, config.KI_PAN, config.KD_PAN,
        config.KP_TILT, config.KI_TILT, config.KD_TILT,
        config.PID_OUTPUT_LIMIT,
    )
    return pan_pid, tilt_pid


def update(
    pan_pid: PID,
    tilt_pid: PID,
    kit,
    target_pos: Optional[Tuple[int, int]],
) -> Optional[Dict]:
    """
    One iteration of the tracking loop. Call once per camera frame.

    target_pos is the detector's output. If it's None (no target this
    frame), this function returns None and does NOT update PID state —
    we don't want the integral or derivative term polluted by phantom
    "zero error" samples while we're not seeing the target.

    Returns a result dict on success so the caller can log/visualize:
        pan_error, tilt_error     — in pixels
        pan_correction, tilt_correction — in degrees
        pan_angle, tilt_angle     — actual angle commanded (after clamp)
    """
    if target_pos is None:
        return None

    target_x, target_y = target_pos
    pan_error = target_x - config.FRAME_CENTER_X
    tilt_error = target_y - config.FRAME_CENTER_Y

    # Always run the PID — keeps its internal time-tracking and derivative
    # state consistent across frames. We may or may not USE the correction.
    pan_correction = pan_pid(pan_error)
    tilt_correction = tilt_pid(tilt_error)

    # Deadband: if the target is already very close to frame center on
    # BOTH axes, hold position instead of nudging the servos. Detector
    # centroid jitter (~2-3 px frame-to-frame) would otherwise drive the
    # bracket to micro-correct forever, producing visible jiggle.
    in_deadband = (
        abs(pan_error) < config.TRACKING_DEADBAND_PX
        and abs(tilt_error) < config.TRACKING_DEADBAND_PX
    )

    if in_deadband:
        return {
            "pan_error": pan_error,
            "tilt_error": tilt_error,
            "pan_correction": 0.0,
            "tilt_correction": 0.0,
            "pan_angle": servo.current_pan(),
            "tilt_angle": servo.current_tilt(),
            "in_deadband": True,
        }

    # current_pan / current_tilt are set by servo.init(), which any caller
    # is expected to have called first. servo.move_* will raise if not.
    new_pan = servo.current_pan() + pan_correction
    new_tilt = servo.current_tilt() + tilt_correction

    actual_pan = servo.move_pan(kit, new_pan)
    actual_tilt = servo.move_tilt(kit, new_tilt)

    return {
        "pan_error": pan_error,
        "tilt_error": tilt_error,
        "pan_correction": pan_correction,
        "tilt_correction": tilt_correction,
        "pan_angle": actual_pan,
        "tilt_angle": actual_tilt,
        "in_deadband": False,
    }


def stop(kit) -> None:
    """Shutdown — delegates to servo.cleanup so the bracket re-centers."""
    servo.cleanup(kit)
