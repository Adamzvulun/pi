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

from gpiozero import LED

log = logging.getLogger(__name__)

# Physical pin 12 on the 40-pin header = BCM GPIO18.
# Active HIGH through the IRLZ44N MOSFET gate (220Ω in series, 100kΩ
# pulldown to GND on the gate to keep the laser OFF when the GPIO is
# floating or undriven).
LASER_PIN: int = 18


def init() -> LED:
    """
    Set up GPIO18 as an output and explicitly drive it LOW so the
    laser starts OFF.

    `gpiozero.LED` defaults to active_high=True and initial_value=False,
    which means the pin is configured as output, low, on construction —
    we still call .off() to make the intent explicit and defend against
    any future gpiozero default change.

    Returns the device object. Pass it to every other function in this
    module. Keep the variable name `laser_dev` (never `laser`).
    """
    laser_dev = LED(LASER_PIN)
    laser_dev.off()
    log.info("Laser initialized on GPIO%d (OFF)", LASER_PIN)
    return laser_dev


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
