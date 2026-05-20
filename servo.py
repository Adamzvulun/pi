"""
servo.py — owner module for the pan-tilt servo hardware.

This is the ONLY module in the project that may import adafruit_servokit
or talk to the PCA9685 directly. Every other file (camera, tracker, main,
test scripts going forward) interacts with the servos exclusively through
the public functions defined here.

Why this matters:
- Single point of safety enforcement. move_pan() and move_tilt() clamp every
  requested angle to the calibrated physical limits. As long as nothing
  bypasses these functions, the bracket cannot be driven into a hard stop.
- Single source of hardware truth. If the bracket is ever recalibrated, the
  four limit constants in this file are the only thing that needs to change.
- Decouples high-level code from low-level library quirks (pulse widths,
  actuation_range, channel numbers, I2C address).

Public API:
    init()             → ServoKit (also moves servos to center)
    move_pan(kit, deg) → actual angle commanded (after clamp)
    move_tilt(kit, deg) → actual angle commanded (after clamp)
    center(kit)        → moves both servos to center
    cleanup(kit)       → centers and leaves servos in a known state
    current_pan()      → last commanded pan angle (None before init)
    current_tilt()     → last commanded tilt angle (None before init)
"""

import logging
import time
from typing import Optional

from adafruit_servokit import ServoKit

# ---- Calibrated angle limits ----------------------------------------------
# Measured 2026-05-20 with calibrate_servo.py against the current pan-tilt
# bracket assembly. If the bracket is ever disassembled, re-mounted, or its
# cables re-routed, RE-RUN calibrate_servo.py and update these four numbers.
# See docs/calibration.md for the full record.

PAN_MIN: float = 50.0
PAN_MAX: float = 220.0
TILT_MIN: float = 115.0
TILT_MAX: float = 205.0

# Centers are computed, not hardcoded — this makes asymmetric ranges
# (like tilt's 115-205, centered at 160 not 135) automatically correct.
PAN_CENTER: float = (PAN_MIN + PAN_MAX) / 2    # 135.0
TILT_CENTER: float = (TILT_MIN + TILT_MAX) / 2  # 160.0

# ---- Hardware configuration -----------------------------------------------
# Per CLAUDE.md — DS3225-specific values. Do not change unless you have
# verified them against the servo datasheet.

PCA9685_ADDRESS: int = 0x40
PAN_CHANNEL: int = 0
TILT_CHANNEL: int = 1

# DS3225 needs 500-2500 µs pulses over a 270° range. ServoKit defaults to
# 1000-2000 µs / 180°, which would give incorrect angles.
PULSE_MIN_US: int = 500
PULSE_MAX_US: int = 2500
ACTUATION_RANGE_DEG: int = 270

# Ramping parameters — match test_servo.py and calibrate_servo.py so motion
# characteristics stay consistent across all scripts in the project.
RAMP_RESOLUTION_DEG: float = 2.0
RAMP_DELAY_S: float = 0.05

# ---- Module state ---------------------------------------------------------
# We track each servo's last commanded angle here because the PCA9685 has
# no position readback. ramp_to needs to know where we're starting from.

_pan_current: Optional[float] = None
_tilt_current: Optional[float] = None

log = logging.getLogger(__name__)


# ---- Internal helpers -----------------------------------------------------

def _configure_channel(kit: ServoKit, channel: int) -> None:
    """Apply DS3225-specific pulse range and actuation range to a channel."""
    kit.servo[channel].set_pulse_width_range(PULSE_MIN_US, PULSE_MAX_US)
    kit.servo[channel].actuation_range = ACTUATION_RANGE_DEG


def _ramp(kit: ServoKit, channel: int, current: float, target: float) -> float:
    """
    Smoothly move a servo from `current` angle to `target` angle.

    Instant jumps cause visible jerk and current spikes; stepping in small
    increments with short sleeps spreads the motion out and is gentler on
    the gearbox and the PSU. Returns the final commanded angle so the caller
    can update its position tracker.
    """
    if abs(target - current) < RAMP_RESOLUTION_DEG:
        # Tiny move — just go directly.
        kit.servo[channel].angle = target
        return target

    direction = 1 if target > current else -1
    angle = current
    while abs(target - angle) > RAMP_RESOLUTION_DEG:
        angle += direction * RAMP_RESOLUTION_DEG
        kit.servo[channel].angle = angle
        time.sleep(RAMP_DELAY_S)
    # Final precise positioning — guarantee we land exactly on target.
    kit.servo[channel].angle = target
    return target


# ---- Public API -----------------------------------------------------------

def init() -> ServoKit:
    """
    Initialize the PCA9685 and configure both servos. Then move them to
    their calibrated centers and return the ServoKit instance.

    IMPORTANT: this function snaps the servos to center on the very first
    move because we have no way to know where they started. If the servos
    were left far from center by a previous script, expect a sudden motion
    here. The DS3225 can handle this, but it draws a current spike during
    the snap. The LM2596 (3A) and external PSU can sustain this.

    The returned ServoKit must be passed to all subsequent function calls.

    Raises:
        OSError: I2C communication failed (likely wiring problem).
    """
    global _pan_current, _tilt_current

    log.info("Initializing PCA9685 at 0x%02x", PCA9685_ADDRESS)
    kit = ServoKit(channels=16, address=PCA9685_ADDRESS)

    _configure_channel(kit, PAN_CHANNEL)
    _configure_channel(kit, TILT_CHANNEL)

    # First-ever PWM commands. We cannot ramp because there's no known
    # starting angle. The servos will snap from wherever they happened to
    # be powered up at to PAN_CENTER / TILT_CENTER.
    log.info("Centering servos: pan→%.1f°, tilt→%.1f°",
             PAN_CENTER, TILT_CENTER)
    kit.servo[PAN_CHANNEL].angle = PAN_CENTER
    kit.servo[TILT_CHANNEL].angle = TILT_CENTER

    _pan_current = PAN_CENTER
    _tilt_current = TILT_CENTER

    # Brief settling delay so the snap motion completes before the caller
    # issues any follow-up commands.
    time.sleep(0.5)

    return kit


def move_pan(kit: ServoKit, angle: float) -> float:
    """
    Move pan to `angle`, clamped to the safe physical range [PAN_MIN, PAN_MAX].

    This is the SAFETY-CRITICAL function for pan. The clamp here is what
    prevents tracking code (or any caller) from driving the bracket into
    a hard stop. Do not bypass this function.

    Returns the actual angle commanded after clamping. If your tracker
    needs to know whether its request was clamped (so it can stop
    integrating in that direction, for example), compare the return
    value to your input.
    """
    global _pan_current

    if _pan_current is None:
        raise RuntimeError("servo.init() must be called before move_pan()")

    clamped = max(PAN_MIN, min(PAN_MAX, angle))
    if clamped != angle:
        log.warning(
            "Pan request %.1f° clamped to %.1f° (limits %.1f°-%.1f°)",
            angle, clamped, PAN_MIN, PAN_MAX,
        )

    _pan_current = _ramp(kit, PAN_CHANNEL, _pan_current, clamped)
    return _pan_current


def move_tilt(kit: ServoKit, angle: float) -> float:
    """
    Move tilt to `angle`, clamped to the safe physical range
    [TILT_MIN, TILT_MAX]. Same safety contract as move_pan.
    """
    global _tilt_current

    if _tilt_current is None:
        raise RuntimeError("servo.init() must be called before move_tilt()")

    clamped = max(TILT_MIN, min(TILT_MAX, angle))
    if clamped != angle:
        log.warning(
            "Tilt request %.1f° clamped to %.1f° (limits %.1f°-%.1f°)",
            angle, clamped, TILT_MIN, TILT_MAX,
        )

    _tilt_current = _ramp(kit, TILT_CHANNEL, _tilt_current, clamped)
    return _tilt_current


def center(kit: ServoKit) -> None:
    """Smoothly move both servos to their calibrated center positions."""
    log.info("Centering servos: pan→%.1f°, tilt→%.1f°",
             PAN_CENTER, TILT_CENTER)
    move_pan(kit, PAN_CENTER)
    move_tilt(kit, TILT_CENTER)


def cleanup(kit: ServoKit) -> None:
    """
    Shutdown the servo subsystem cleanly. Centers both servos and leaves
    them holding position.

    Note: the PCA9685 has no clean "release" — it will keep sending the
    last commanded PWM pulse until power is removed. Leaving the servos
    at center means the next script that calls init() will see minimal
    initial movement.

    Always call this in a try/finally block so it runs even on errors
    or Ctrl+C. Catches and logs its own exceptions so it cannot mask
    the original error.
    """
    log.info("Shutting down servos — centering")
    try:
        center(kit)
    except Exception:
        # Don't re-raise — cleanup is called from finally blocks and must
        # not mask the original exception that triggered shutdown.
        log.exception("Error during servo cleanup")


def current_pan() -> Optional[float]:
    """Return the last commanded pan angle, or None if init() hasn't run."""
    return _pan_current


def current_tilt() -> Optional[float]:
    """Return the last commanded tilt angle, or None if init() hasn't run."""
    return _tilt_current
