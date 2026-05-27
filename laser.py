"""
laser.py — owner module for the laser hardware on GPIO18.

This is the ONLY module in the project that may drive GPIO18 / import
`gpiozero` for the laser pin. Every other file (test_laser, main,
future tracking integration) controls the laser exclusively through
the public functions defined here.

Why this matters:
- Single point of safety enforcement. `init()` explicitly drives the
  pin LOW before returning so the laser is OFF the instant the module
  is set up. `cleanup()` is guaranteed to turn it off again.
- The MOSFET gate has a 100kΩ pulldown so a floating GPIO holds the
  laser OFF — but we don't rely solely on that. The module also
  commands LOW explicitly.

Public API:
    init()            → laser_dev (gpiozero.LED, OFF)
    fire(laser_dev)   → drives GPIO18 HIGH (laser ON)
    off(laser_dev)    → drives GPIO18 LOW  (laser OFF)
    cleanup(laser_dev) → turns OFF, closes the device

NAMING — critical: the variable holding the device object MUST be
`laser_dev`, never `laser`. Writing `laser = laser.init()` works once
but then `laser.cleanup(...)` fails because the name `laser` now
points at the device, not the module. CLAUDE.md flags this.

Safety pattern — always wrap usage in try/finally:

    laser_dev = laser.init()
    try:
        # ... do things, possibly laser.fire(laser_dev), laser.off(laser_dev) ...
    finally:
        laser.cleanup(laser_dev)

The `finally` block guarantees the laser turns off even if an
exception is raised, Ctrl+C is pressed, or the loop exits unexpectedly.
"""

import logging
import time

from gpiozero import LED

log = logging.getLogger(__name__)

# Physical pin 12 on the 40-pin header = BCM GPIO18.
# Currently driven directly at 3.3V from GPIO18 into a 3V laser module
# with internal current limiter. Earlier hardware revision used an
# IRLZ44N MOSFET driver (220Ω gate + 100kΩ pulldown on a 5V supply);
# that path was abandoned when the bare diode failed and the project
# switched to a self-driven 3V module. CLAUDE.md / problem 002 record
# the transition.
LASER_PIN: int = 18

# When a parent process (e.g. control_panel.py) releases the laser pin
# right before launching a subprocess that re-claims it, the lgpio
# release isn't always visible to a child process started within a few
# milliseconds. Retry a small number of times with backoff before giving
# up — turns a race into a non-issue.
_INIT_RETRIES: int = 5
_INIT_RETRY_DELAY_S: float = 0.15


def init() -> LED:
    """
    Set up GPIO18 as an output and explicitly drive it LOW so the
    laser starts OFF.

    `gpiozero.LED` defaults to active_high=True and initial_value=False,
    which means the pin is configured as output, low, on construction —
    we still call .off() to make the intent explicit and defend against
    any future gpiozero default change.

    Retries on `lgpio.error: 'GPIO busy'` — that error can occur briefly
    when a parent process has just released the pin (its kernel claim
    hasn't fully propagated yet). After _INIT_RETRIES attempts the
    underlying exception is re-raised so the caller sees a real failure
    if the pin is permanently held.

    Returns the device object. Pass it to every other function in this
    module. Keep the variable name `laser_dev` (never `laser`).
    """
    last_exc = None
    for attempt in range(1, _INIT_RETRIES + 1):
        try:
            laser_dev = LED(LASER_PIN)
            laser_dev.off()
            log.info("Laser initialized on GPIO%d (OFF)", LASER_PIN)
            return laser_dev
        except Exception as exc:  # lgpio.error in practice, but be permissive
            last_exc = exc
            msg = str(exc).lower()
            if "busy" not in msg and "in use" not in msg:
                # Not a contention error — fail fast.
                raise
            log.warning("GPIO%d busy on attempt %d/%d — retrying in %.2fs",
                        LASER_PIN, attempt, _INIT_RETRIES, _INIT_RETRY_DELAY_S)
            time.sleep(_INIT_RETRY_DELAY_S)
    # All retries exhausted — re-raise the last error so caller sees it.
    assert last_exc is not None
    raise last_exc


def fire(laser_dev: LED) -> None:
    """Drive GPIO18 HIGH — laser ON. Caller is responsible for timing."""
    laser_dev.on()
    log.info("Laser ON")


def off(laser_dev: LED) -> None:
    """Drive GPIO18 LOW — laser OFF. Always safe to call."""
    laser_dev.off()
    log.info("Laser OFF")


def cleanup(laser_dev: LED) -> None:
    """
    Shutdown the laser subsystem cleanly. Forces the laser OFF and
    closes the underlying device, releasing the GPIO line.

    Catches and logs its own exceptions so it cannot mask the original
    error that triggered shutdown (this is called from `finally` blocks).
    """
    try:
        laser_dev.off()
    except Exception:
        log.exception("Error driving laser pin LOW during cleanup")

    try:
        laser_dev.close()
    except Exception:
        log.exception("Error closing laser device during cleanup")

    log.info("Laser cleanup complete (GPIO%d released)", LASER_PIN)
