"""
test_laser.py — Phase 6 standalone laser test.

Sequence:
    1. init() laser (verifies GPIO setup, leaves laser OFF)
    2. countdown 3, 2, 1
    3. fire for 1.0 second
    4. off
    5. cleanup (laser OFF, GPIO released)

How to run on the Pi (SSH is fine — no GUI needed):

    cd ~/pi && source venv/bin/activate
    python3 test_laser.py

What you should see:
    - Terminal logs the countdown
    - At "FIRING", the laser dot appears on whatever the laser is
      pointing at (point it at a wall, never at people or eyes)
    - After 1 second the dot disappears
    - Terminal logs cleanup, GPIO released

Safety reminder:
    The laser is 5 mW 650 nm — Class IIIa equivalent. Brief exposure
    relies on the blink reflex but DELIBERATE staring into the beam
    can damage the retina. Before running this test:
      - Point the laser at a wall, NOT at a person or pet
      - Do not look directly into the bare diode
      - Reflective surfaces (mirrors, glossy metal) scatter the beam
        unpredictably — keep the aim path matte

The try/finally guarantees the laser turns off even if the script is
interrupted with Ctrl+C, hits an exception, or otherwise exits abnormally.
"""

import logging
import sys
import time

import laser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

FIRE_DURATION_S: float = 1.0
COUNTDOWN_FROM: int = 3


def main() -> int:
    laser_dev = laser.init()

    try:
        for n in range(COUNTDOWN_FROM, 0, -1):
            log.info("Firing in %d...", n)
            time.sleep(1.0)

        log.info("FIRING — laser ON for %.1f s", FIRE_DURATION_S)
        laser.fire(laser_dev)
        time.sleep(FIRE_DURATION_S)
        laser.off(laser_dev)

        log.info("Fire sequence complete.")
        return 0

    finally:
        laser.cleanup(laser_dev)


if __name__ == "__main__":
    sys.exit(main())
