"""
calibrate_servo.py — interactive tool to find safe pan-tilt bracket limits.

Purpose: discover the four physical angle limits — PAN_MIN, PAN_MAX,
TILT_MIN, TILT_MAX — by manually stepping each servo through its range
and marking the angle just before any sign of mechanical strain.

The output of this script is the four numbers that will be hardcoded into
servo.py (Task 3.4) as the safety clamps for all future code.

Calibration philosophy:
- The script never moves on its own. Every move is explicitly requested.
- Each move is small (default 5°) and ramped smoothly.
- The user is the safety system. They watch and listen for strain
  (cable tension, parts touching, motor straining) and stop BEFORE damage.

This script imports adafruit_servokit directly — same allowance as
test_servo.py — because servo.py does not exist yet.
"""

import logging
import sys
import time
from typing import List, Optional, Tuple

from adafruit_servokit import ServoKit

# ---- Configuration ---------------------------------------------------------

PCA9685_ADDRESS = 0x40
PAN_CHANNEL = 0
TILT_CHANNEL = 1

# DS3225 specs (per CLAUDE.md)
PULSE_MIN = 500
PULSE_MAX = 2500
ACTUATION_RANGE = 270

# Electrical limits — we DO let the user move anywhere in this range during
# calibration. The whole point is to discover the smaller physical limits.
ANGLE_MIN = 0
ANGLE_MAX = 270

# Ramping
RAMP_RESOLUTION = 2.0
RAMP_DELAY = 0.05

# Default user-facing step size for + / - commands.
DEFAULT_STEP = 5.0

# Logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


# ---- Exceptions ------------------------------------------------------------

class UserQuit(Exception):
    """Raised when the user types 'q' to bail out of calibration entirely."""


# ---- Helpers ---------------------------------------------------------------

def configure_servo(kit: ServoKit, channel: int) -> None:
    """Apply DS3225 pulse range and actuation range to one channel."""
    kit.servo[channel].set_pulse_width_range(PULSE_MIN, PULSE_MAX)
    kit.servo[channel].actuation_range = ACTUATION_RANGE


def ramp_to(kit: ServoKit, channel: int, current: float, target: float) -> float:
    """
    Smoothly move a servo from current → target in small ramped steps.
    Returns the final commanded angle (which the caller must keep tracking,
    because the PCA9685 cannot read back position).
    """
    target = max(ANGLE_MIN, min(ANGLE_MAX, target))
    if abs(target - current) < RAMP_RESOLUTION:
        kit.servo[channel].angle = target
        return target
    direction = 1 if target > current else -1
    angle = current
    while abs(target - angle) > RAMP_RESOLUTION:
        angle += direction * RAMP_RESOLUTION
        kit.servo[channel].angle = angle
        time.sleep(RAMP_DELAY)
    kit.servo[channel].angle = target
    return target


def prompt_estimate(name: str) -> float:
    """Loop until the user gives a valid 0-270 angle estimate."""
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


def print_commands() -> None:
    """Print the command reference for the per-servo calibration loop."""
    print("Commands:")
    print("  +N       move +N degrees (e.g. '+5')")
    print("  -N       move -N degrees (e.g. '-10')")
    print("  +        move +<step> degrees (default 5)")
    print("  -        move -<step> degrees")
    print("  =N       jump directly to absolute angle N (use carefully)")
    print("  step N   change default step size to N (e.g. 'step 2' for fine work)")
    print("  s        mark the CURRENT angle as a limit")
    print("  ?        show current angle and recorded marks")
    print("  help     show this list again")
    print("  done     finish this servo (need 2+ marks)")
    print("  q        quit entirely (no auto-move)")


# ---- Per-servo calibration loop -------------------------------------------

def calibrate_one_servo(
    kit: ServoKit,
    channel: int,
    name: str,
    start_angle: float,
) -> Tuple[Optional[Tuple[float, float]], float]:
    """
    Interactive calibration for one servo.

    Args:
        kit:         ServoKit instance
        channel:     PCA9685 channel (0=pan, 1=tilt)
        name:        human-readable name for the prompts ("pan" / "tilt")
        start_angle: where the servo currently is (caller tracks this)

    Returns:
        (limits, final_angle):
            limits = (min_angle, max_angle) if user typed 'done' with >=2 marks
            limits = None if user typed 'done' (shouldn't happen) or skipped
            final_angle = the last commanded angle on this servo

    Raises:
        UserQuit: if the user typed 'q' to abort everything
    """
    print()
    print(f"=== Calibrating {name.upper()} (channel {channel}) ===")
    print(f"Current angle: {start_angle}°")
    print()
    print_commands()

    current = start_angle
    step = DEFAULT_STEP
    marked: List[float] = []

    while True:
        try:
            raw = input(f"\n[{name} @ {current}°, step={step}°, marks={marked}] > ").strip().lower()
        except EOFError:
            # Treat EOF (Ctrl+D) as 'q' to be safe.
            raise UserQuit()

        if not raw:
            continue

        # ---- Quit / done / informational --------------------------------
        if raw == "q":
            raise UserQuit()

        if raw == "done":
            if len(marked) < 2:
                print(f"Need at least 2 marks before 'done'. You have {len(marked)}.")
                print("Use 's' to mark the current angle as a limit.")
                continue
            lo, hi = min(marked), max(marked)
            print(f"{name.capitalize()} limits: min={lo}°, max={hi}°")
            return ((lo, hi), current)

        if raw == "?":
            print(f"  Current angle:  {current}°")
            print(f"  Marks recorded: {marked if marked else '(none yet)'}")
            print(f"  Step size:      {step}°")
            continue

        if raw in ("help", "h"):
            print_commands()
            continue

        if raw == "s":
            marked.append(current)
            print(f"Marked {current}° as limit #{len(marked)} for {name}.")
            continue

        # ---- 'step N' to change default step size ------------------------
        if raw.startswith("step"):
            parts = raw.split()
            if len(parts) != 2:
                print("Usage: step N  (e.g. 'step 2')")
                continue
            try:
                new_step = float(parts[1])
            except ValueError:
                print("step N — N must be a number.")
                continue
            if not (0 < new_step <= 50):
                print("step must be between 0 and 50.")
                continue
            step = new_step
            print(f"Step size = {step}°")
            continue

        # ---- Movement commands ------------------------------------------
        target: Optional[float] = None

        if raw == "+":
            target = current + step
        elif raw == "-":
            target = current - step
        elif raw.startswith("+"):
            try:
                target = current + float(raw[1:])
            except ValueError:
                print(f"Cannot parse: {raw!r}. Type 'help' for commands.")
                continue
        elif raw.startswith("-"):
            try:
                target = current - float(raw[1:])
            except ValueError:
                print(f"Cannot parse: {raw!r}. Type 'help' for commands.")
                continue
        elif raw.startswith("="):
            try:
                target = float(raw[1:])
            except ValueError:
                print(f"Cannot parse: {raw!r}. Type 'help' for commands.")
                continue
        else:
            print(f"Unknown command: {raw!r}. Type 'help' for commands.")
            continue

        # Clamp to electrical range (and warn if we did).
        clamped = max(ANGLE_MIN, min(ANGLE_MAX, target))
        if clamped != target:
            print(f"Target {target}° clamped to {clamped}° (servo electrical limit).")
            target = clamped

        if target == current:
            print(f"Already at {current}°.")
            continue

        # Execute the ramp. ramp_to returns the new current angle.
        current = ramp_to(kit, channel, current, target)
        print(f"Now at: {current}°")


# ---- Main ------------------------------------------------------------------

def main() -> int:
    print("== calibrate_servo.py ==\n")
    print("Goal: find the safe physical angle limits of your pan-tilt bracket.")
    print()
    print("SAFETY:")
    print("  1. With power OFF, pre-position both bracket axes to roughly the")
    print("     middle of their physical range (eyeball it).")
    print("  2. Power the external 5V PSU and the Pi.")
    print("  3. WATCH AND LISTEN during every move. Stop one step BEFORE you")
    print("     see cable tension, parts touching, or hear motor straining.")
    print()

    ack = input("Type 'ready' when set up (anything else aborts): ").strip().lower()
    if ack != "ready":
        print("Aborted.")
        return 0

    print()
    print("ESTIMATE starting angles (best guess, 0-270):")
    pan_est = prompt_estimate("Pan ")
    tilt_est = prompt_estimate("Tilt")

    print()
    print(f"I will now send pulse for pan={pan_est}° and tilt={tilt_est}°.")
    print("Brackets may twitch. If motion is LARGE, hit Ctrl+C and re-estimate.")
    input("Press Enter to proceed: ")

    try:
        kit = ServoKit(channels=16, address=PCA9685_ADDRESS)
    except Exception as exc:
        log.error(f"Failed to initialize PCA9685 at 0x{PCA9685_ADDRESS:02x}: {exc}")
        log.error("Run `i2cdetect -y 1` and confirm '40' appears in the grid.")
        return 1

    configure_servo(kit, PAN_CHANNEL)
    configure_servo(kit, TILT_CHANNEL)

    # First commands cannot ramp — we have no known prior position.
    log.info(f"Sending pan = {pan_est}°")
    kit.servo[PAN_CHANNEL].angle = pan_est
    time.sleep(0.5)
    log.info(f"Sending tilt = {tilt_est}°")
    kit.servo[TILT_CHANNEL].angle = tilt_est
    time.sleep(0.5)

    # Track each servo's current angle across calibration sessions.
    pan_current = pan_est
    tilt_current = tilt_est
    pan_limits: Optional[Tuple[float, float]] = None
    tilt_limits: Optional[Tuple[float, float]] = None

    try:
        while True:
            print("\n--- Select servo to (re)calibrate ---")
            print("  0    = pan")
            print("  1    = tilt")
            print("  done = finish calibration and print results")
            choice = input("> ").strip().lower()

            if choice == "done":
                break
            elif choice == "0":
                pan_limits, pan_current = calibrate_one_servo(
                    kit, PAN_CHANNEL, "pan", pan_current
                )
            elif choice == "1":
                tilt_limits, tilt_current = calibrate_one_servo(
                    kit, TILT_CHANNEL, "tilt", tilt_current
                )
            else:
                print("Choose 0, 1, or 'done'.")

    except UserQuit:
        print("\nQuit requested. Exiting with whatever was marked so far.")
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting with whatever was marked so far.")

    # ---- Final summary -----------------------------------------------------
    print()
    print("=" * 50)
    print("Calibration complete")
    print("=" * 50)
    print("Recorded limits:")

    if pan_limits:
        print(f"  PAN_MIN  = {pan_limits[0]}")
        print(f"  PAN_MAX  = {pan_limits[1]}")
    else:
        print(f"  PAN_MIN  = (not calibrated)")
        print(f"  PAN_MAX  = (not calibrated)")

    if tilt_limits:
        print(f"  TILT_MIN = {tilt_limits[0]}")
        print(f"  TILT_MAX = {tilt_limits[1]}")
    else:
        print(f"  TILT_MIN = (not calibrated)")
        print(f"  TILT_MAX = (not calibrated)")

    print()
    print("Write these four numbers down. They will be hardcoded into servo.py")
    print("(Task 3.4) as the safety clamps for all future tracking code.")
    print()
    print("Servos left at their last commanded positions:")
    print(f"  pan  = {pan_current}°")
    print(f"  tilt = {tilt_current}°")
    print("Power-cycle the PSU or re-run the script if you need to move them.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
