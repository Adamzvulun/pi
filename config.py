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
HSV_LOWER: np.ndarray = np.array([79, 76, 0])     # [H_min, S_min, V_min]
HSV_UPPER: np.ndarray = np.array([105, 255, 255]) # [H_max, S_max, V_max]

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

# ---- PID gains (Phase 5) --------------------------------------------------
# Two independent PID loops — one for pan (left-right), one for tilt (up-down).
# Input to each loop is pixel error (target_x - 320, target_y - 240).
# Output is a correction in degrees added to the current servo angle.
#
# These starting values are CONSERVATIVE — small Kp, no integral, light damping.
# Expect to tune them empirically in Task 5.4. The procedure is documented in
# docs/plan/phase-5-pid-tracking.md.
#
# IMPORTANT — sign:
# The relationship between "increase pan angle" and "camera looks rightward"
# depends on how the servo is physically mounted on the bracket. If the bracket
# tracks AWAY from the target instead of toward it, FLIP THE SIGN of the
# corresponding Kp. The PID library handles negative gains correctly.
KP_PAN: float = 0.05
KI_PAN: float = 0.0
KD_PAN: float = 0.01

KP_TILT: float = 0.05
KI_TILT: float = 0.0
KD_TILT: float = 0.01

# Maximum correction in degrees per PID update. Caps the swing if the target
# suddenly appears at a frame edge — without this, a +320 px error with
# Kp=0.05 would request a +16° jump on a single frame, which is jarring and
# risks overshoot.
PID_OUTPUT_LIMIT: float = 20.0
