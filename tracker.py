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


# ---- Coast-mode state -----------------------------------------------------
# When the target is being tracked normally, we remember the last PID
# correction (degrees per axis). If the target then disappears, update()
# continues applying those corrections for up to COAST_MAX_FRAMES so the
# bracket keeps chasing instead of freezing. Configurable from config.py.

_last_pan_correction: float = 0.0
_last_tilt_correction: float = 0.0
_coast_frames_remaining: int = 0
# After coast expires (or hits servo limits) without re-acquiring, set
# this so subsequent update() calls drive the bracket back to center
# until either the target reappears or we're already centered.
_recentering: bool = False


def _reset_coast() -> None:
    """Forget the last correction so an immediate target-loss won't coast.
    Called when the tracker has no reason to coast (e.g. target is in the
    deadband — it was stationary, holding position is the right behavior)."""
    global _last_pan_correction, _last_tilt_correction, _coast_frames_remaining
    _last_pan_correction = 0.0
    _last_tilt_correction = 0.0
    _coast_frames_remaining = 0


def _reset_recenter() -> None:
    """Cancel any in-progress recenter (e.g. because the target just
    reappeared and normal tracking should resume immediately)."""
    global _recentering
    _recentering = False


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
    global _last_pan_correction, _last_tilt_correction, _coast_frames_remaining
    global _recentering

    # ---- Target lost branch -----------------------------------------------
    if target_pos is None:
        # First try: coast (if the last tracking step gave us a direction).
        last_was_meaningful = (
            abs(_last_pan_correction) >= config.COAST_MIN_CORRECTION_DEG
            or abs(_last_tilt_correction) >= config.COAST_MIN_CORRECTION_DEG
        )
        if _coast_frames_remaining > 0 and last_was_meaningful:
            requested_pan = servo.current_pan() + _last_pan_correction
            requested_tilt = servo.current_tilt() + _last_tilt_correction
            actual_pan = servo.move_pan(kit, requested_pan, ramp=False)
            actual_tilt = servo.move_tilt(kit, requested_tilt, ramp=False)

            # If both axes were clamped by servo.py (the bracket physically
            # can't go any further in the coast direction), there's no
            # point spending more frames here — exit coast early and let
            # the recenter logic take over next frame.
            pan_clamped = abs(actual_pan - requested_pan) > 0.5
            tilt_clamped = abs(actual_tilt - requested_tilt) > 0.5
            if pan_clamped and tilt_clamped:
                log.debug("Coast hit servo limits on both axes — stopping coast.")
                _coast_frames_remaining = 0
            else:
                # Decay correction so the bracket eases to a stop rather
                # than slamming into a limit.
                _last_pan_correction *= config.COAST_DECAY
                _last_tilt_correction *= config.COAST_DECAY
                _coast_frames_remaining -= 1

                return {
                    "pan_error": None,
                    "tilt_error": None,
                    "pan_correction": _last_pan_correction,
                    "tilt_correction": _last_tilt_correction,
                    "pan_angle": actual_pan,
                    "tilt_angle": actual_tilt,
                    "in_deadband": False,
                    "coasting": True,
                    "coast_remaining": _coast_frames_remaining,
                    "recentering": False,
                }

        # Coast unavailable (or just ended). If recenter is enabled and we
        # were doing something useful before the loss (we'd have non-zero
        # correction history or active recenter flag), drive back to center.
        if config.RECENTER_AFTER_COAST and not _recentering:
            # First frame after a failed coast — flip into recenter mode if
            # we'd been actively tracking (a coast attempt happened) or
            # we're not already at center.
            current_pan = servo.current_pan()
            current_tilt = servo.current_tilt()
            already_centered = (
                abs(current_pan - servo.PAN_CENTER) < 1.0
                and abs(current_tilt - servo.TILT_CENTER) < 1.0
            )
            if last_was_meaningful and not already_centered:
                log.info("Coast ended without re-acquisition — recentering bracket.")
                _recentering = True
            _reset_coast()

        if _recentering:
            current_pan = servo.current_pan()
            current_tilt = servo.current_tilt()
            pan_delta = servo.PAN_CENTER - current_pan
            tilt_delta = servo.TILT_CENTER - current_tilt

            # Done if within one step of center on both axes.
            if (abs(pan_delta) < config.RECENTER_STEP_DEG
                    and abs(tilt_delta) < config.RECENTER_STEP_DEG):
                log.info("Recenter complete — holding at center.")
                # Snap precisely to center, then exit recenter mode.
                servo.move_pan(kit, servo.PAN_CENTER, ramp=False)
                servo.move_tilt(kit, servo.TILT_CENTER, ramp=False)
                _recentering = False
                return None

            # Move one step toward center on each axis.
            step = config.RECENTER_STEP_DEG
            pan_step = max(-step, min(step, pan_delta))
            tilt_step = max(-step, min(step, tilt_delta))
            actual_pan = servo.move_pan(kit, current_pan + pan_step, ramp=False)
            actual_tilt = servo.move_tilt(kit, current_tilt + tilt_step, ramp=False)
            return {
                "pan_error": None,
                "tilt_error": None,
                "pan_correction": pan_step,
                "tilt_correction": tilt_step,
                "pan_angle": actual_pan,
                "tilt_angle": actual_tilt,
                "in_deadband": False,
                "coasting": False,
                "recentering": True,
            }

        # Nothing to do — bracket holds wherever it was.
        return None

    # ---- Target acquired branch — normal PID tracking ---------------------
    # If we'd been recentering after a failed coast, drop that — the
    # target's back and PID should drive the bracket directly.
    if _recentering:
        log.info("Target re-acquired during recenter — resuming PID tracking.")
        _reset_recenter()

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
        # Target was stationary in the deadband — if it disappears now we
        # should NOT coast off in some old direction. Clear coast state.
        _reset_coast()
        return {
            "pan_error": pan_error,
            "tilt_error": tilt_error,
            "pan_correction": 0.0,
            "tilt_correction": 0.0,
            "pan_angle": servo.current_pan(),
            "tilt_angle": servo.current_tilt(),
            "in_deadband": True,
            "coasting": False,
            "recentering": False,
        }

    # current_pan / current_tilt are set by servo.init(), which any caller
    # is expected to have called first. servo.move_* will raise if not.
    new_pan = servo.current_pan() + pan_correction
    new_tilt = servo.current_tilt() + tilt_correction

    # ramp=False because the ramp's 50 ms/2° sleeps inside servo.py would
    # block this loop for hundreds of milliseconds per correction. Without
    # ramping, the PWM command changes instantly and the loop returns to
    # capture the next frame immediately. The DS3225's own mechanical
    # slew rate (~1°/12 ms) provides natural smoothing.
    actual_pan = servo.move_pan(kit, new_pan, ramp=False)
    actual_tilt = servo.move_tilt(kit, new_tilt, ramp=False)

    # Save state so we can coast if the target disappears next frame.
    _last_pan_correction = pan_correction
    _last_tilt_correction = tilt_correction
    _coast_frames_remaining = config.COAST_MAX_FRAMES

    return {
        "pan_error": pan_error,
        "tilt_error": tilt_error,
        "pan_correction": pan_correction,
        "tilt_correction": tilt_correction,
        "pan_angle": actual_pan,
        "tilt_angle": actual_tilt,
        "in_deadband": False,
        "coasting": False,
        "recentering": False,
    }


def stop(kit) -> None:
    """Shutdown — delegates to servo.cleanup so the bracket re-centers."""
    servo.cleanup(kit)
