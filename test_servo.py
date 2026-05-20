"""
test_servo.py — small motion test for the pan-tilt servos.

Purpose: confirm the chain Pi → I2C → PCA9685 → DS3225 servo motion works.
This is intentionally a SMALL move check — we do not yet know the bracket's
physical angle limits, so we keep all motion close to whatever angle the user
estimates the servos are currently at.

Why this script exists separately from calibrate_servo.py:
- It's a 30-second sanity check before doing the long calibration.
- If this fails, calibration cannot work either.

This script imports adafruit_servokit directly. That is allowed here only
because servo.py does not exist yet (it will be created in Task 3.4 with the
calibrated limits from calibrate_servo.py). After servo.py exists, no other
file in the project may import adafruit_servokit directly.
"""

import logging
import sys
import time

from adafruit_servokit import ServoKit

# ---- Configuration ---------------------------------------------------------

# Hardware (per CLAUDE.md)
PCA9685_ADDRESS = 0x40
PAN_CHANNEL = 0
TILT_CHANNEL = 1

# DS3225 servo specs (per CLAUDE.md). These MUST be set or angles will be wrong.
# ServoKit defaults to 1000-2000 µs / 180° range, which is incorrect for DS3225.
PULSE_MIN = 500        # µs — DS3225 minimum pulse
PULSE_MAX = 2500       # µs — DS3225 maximum pulse
ACTUATION_RANGE = 270  # degrees — DS3225 full electrical range

# Servo electrical limits (NOT the physical bracket limits — those are unknown
# until calibration is done).
ANGLE_MIN = 0
ANGLE_MAX = 270

# Ramping parameters — small steps with short sleeps make motion smooth and
# reduce peak current draw on the PSU.
RAMP_RESOLUTION = 2.0  # degrees per ramp sub-step
RAMP_DELAY = 0.05      # seconds between ramp sub-steps

# Test sweep amplitude. We do not know the bracket's limits yet, so we stay
# within ±10° of the user's estimated starting angle. This is well inside any
# reasonable pan-tilt bracket's physical range.
TEST_AMPLITUDE = 10.0

# Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


# ---- Helpers ---------------------------------------------------------------

def configure_servo(kit: ServoKit, channel: int) -> None:
    """
    Apply DS3225-specific configuration to a single PCA9685 channel.

    Without these calls, ServoKit assumes a generic 180° servo with a
    1000-2000 µs pulse range, and the angles in our code would be wrong.
    """
    kit.servo[channel].set_pulse_width_range(PULSE_MIN, PULSE_MAX)
    kit.servo[channel].actuation_range = ACTUATION_RANGE


def ramp_to(kit: ServoKit, channel: int, current: float, target: float) -> float:
    """
    Smoothly move a servo from `current` angle to `target` angle.

    The servo library only supports absolute angle commands. To get smooth
    motion (instead of an instant snap), we issue a series of small absolute
    commands stepping from current toward target, with a short sleep between
    each. The returned value is the final angle commanded — the caller
    must use this to track the servo's position (since the PCA9685 has no
    way to read back).

    Args:
        kit:     the ServoKit instance
        channel: PCA9685 channel number (0=pan, 1=tilt)
        current: where the servo is right now (we have to trust this)
        target:  where we want the servo to be

    Returns:
        the final angle commanded (== target unless clamped)
    """
    # Safety clamp to the electrical limits. We CANNOT clamp to physical bracket
    # limits because those are still unknown at this stage of the project.
    target = max(ANGLE_MIN, min(ANGLE_MAX, target))

    # If the move is tiny, just do it in one shot.
    if abs(target - current) < RAMP_RESOLUTION:
        kit.servo[channel].angle = target
        return target

    direction = 1 if target > current else -1
    angle = current
    # Step toward target until we're within one resolution unit.
    while abs(target - angle) > RAMP_RESOLUTION:
        angle += direction * RAMP_RESOLUTION
        kit.servo[channel].angle = angle
        time.sleep(RAMP_DELAY)
    # Final precise positioning — guarantees we land exactly on target.
    kit.servo[channel].angle = target
    return target


def prompt_estimate(name: str) -> float:
    """
    Ask the user to eyeball-estimate a servo's current angle. Loops until
    a valid number in [0, 270] is entered. We need this because the PCA9685
    cannot tell us where the servo is — only the user can see the bracket.
    """
    while True:
        raw = input(f"  {name} estimate (0-270): ").strip()
        try:
            value = float(raw)
        except ValueError:
            print("  Not a number. Try again.")
            continue
        if not (ANGLE_MIN <= value <= ANGLE_MAX):
            print(f"  Must be between {ANGLE_MIN} and {ANGLE_MAX}. Try again.")
            continue
        return value


# ---- Main ------------------------------------------------------------------

def main() -> int:
    print("== test_servo.py ==\n")
    print("Before continuing:")
    print("  1. Pre-position both bracket axes to roughly the middle of their")
    print("     physical range (eyeball it).")
    print("  2. Make sure the external 5V PSU is on and the PCA9685 V+ rail")
    print("     is powered.")
    print()
    print("ESTIMATE the current angle of each servo (your best guess, 0-270).")
    print("This is just our internal starting reference — accuracy is not")
    print("critical, but the closer to truth, the smaller the initial twitch.")
    print()

    pan_est = prompt_estimate("Pan ")
    tilt_est = prompt_estimate("Tilt")

    print()
    print(f"I will now send pulse for pan={pan_est}° and tilt={tilt_est}°.")
    print("The bracket may twitch slightly. If motion is LARGE, hit Ctrl+C")
    print("immediately, manually reposition, and re-estimate.")
    input("Press Enter to proceed: ")

    # Connect to the PCA9685 over I2C. If this fails, the most likely causes
    # are I2C not enabled, wrong wiring, or no shared ground.
    try:
        kit = ServoKit(channels=16, address=PCA9685_ADDRESS)
    except Exception as exc:
        log.error(f"Failed to initialize PCA9685 at 0x{PCA9685_ADDRESS:02x}: {exc}")
        log.error("Run `i2cdetect -y 1` and confirm '40' appears in the grid.")
        return 1

    configure_servo(kit, PAN_CHANNEL)
    configure_servo(kit, TILT_CHANNEL)

    try:
        # ---- First commands (no ramping possible) -------------------------
        # We have no idea where the servo is, so we just send the estimate.
        # Whatever actually happens, we trust that current == estimate going
        # forward (we have no other reference).
        log.info(f"Sending pan = {pan_est}°")
        kit.servo[PAN_CHANNEL].angle = pan_est
        time.sleep(0.5)

        log.info(f"Sending tilt = {tilt_est}°")
        kit.servo[TILT_CHANNEL].angle = tilt_est
        time.sleep(0.5)

        # ---- Small test motion on pan only --------------------------------
        # Tilt stays at its estimated position throughout. We only sweep pan
        # to keep the test deliberate and minimal.
        log.info(f"Pan: ramp to {pan_est - TEST_AMPLITUDE}°")
        pan_now = ramp_to(kit, PAN_CHANNEL, pan_est, pan_est - TEST_AMPLITUDE)
        time.sleep(0.5)

        log.info(f"Pan: ramp to {pan_est + TEST_AMPLITUDE}°")
        pan_now = ramp_to(kit, PAN_CHANNEL, pan_now, pan_est + TEST_AMPLITUDE)
        time.sleep(0.5)

        log.info(f"Pan: ramp back to {pan_est}°")
        pan_now = ramp_to(kit, PAN_CHANNEL, pan_now, pan_est)
        time.sleep(0.5)

        print()
        print("Test complete. Both servos are at the estimated start positions.")
        print("If pan visibly swept right then left and returned, the chain is")
        print("working end-to-end. You can now run calibrate_servo.py to find")
        print("the safe physical angle limits.")
        return 0

    except KeyboardInterrupt:
        # Important: do NOT auto-move the servos on Ctrl+C. We don't know
        # where 'safe' is yet. Just stop and let the user reposition manually.
        print()
        print("Interrupted. Servos left at last commanded position.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
