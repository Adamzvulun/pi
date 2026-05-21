"""
config.py — single source of truth for all tuned/calibrated constants.

Import from here wherever you need frame geometry or detection parameters.
Never hardcode these values inline in other modules.

Servo limits live in servo.py — they are hardware-specific to the DS3225
and PCA9685, not detection-tuning values. Everything else tuned empirically
lives here.

Will grow to include:
    KP, KI, KD          — PID gains (Phase 5)
    BORESIGHT_X_OFFSET  — pixel delta between camera aim and laser dot (Phase 7)
    BORESIGHT_Y_OFFSET  — (Phase 7)
"""

import numpy as np

# ---- Frame geometry -------------------------------------------------------
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480
FRAME_CENTER_X: int = FRAME_WIDTH // 2   # 320
FRAME_CENTER_Y: int = FRAME_HEIGHT // 2  # 240

# ---- HSV target range -----------------------------------------------------
# PLACEHOLDER values — replace after running tune_detector.py (Task 4.4).
#
# Pick a bright, solid-colored target that isn't red. Red wraps in OpenCV
# HSV (Hue near 0 AND near 179) so a single inRange call can't cleanly
# capture it. Good choices: bright orange, tennis-ball yellow-green, blue.
#
# After tuning, record the final values and the target object description
# in docs/calibration.md.
HSV_LOWER: np.ndarray = np.array([0, 100, 100])   # [H_min, S_min, V_min]
HSV_UPPER: np.ndarray = np.array([30, 255, 255])  # [H_max, S_max, V_max]

# ---- Detection tuning -----------------------------------------------------
# Smallest contour area (in pixels) that counts as "the target." Anything
# below this is treated as background noise and ignored. 200px is a
# reasonable starting point — equivalent to a ~14×14 px blob. Raise if
# detector picks up tiny color specks in the background; lower if your
# target appears small in the frame.
MIN_CONTOUR_AREA: int = 200

# Laser fires only when pixel error is below this threshold on both axes.
# Prevents firing while the servos are still settling.
FIRE_PIXEL_THRESHOLD: int = 15
