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
# Tuned 2026-05-23 against the actual hardware (LifeCam HD-3000 on the
# 3D-printed tilt mount, blue plastic bag target, overhead lighting).
# Tuning history is in docs/calibration.md.
#
# Brief context: Kp depends entirely on whether servo.py is called with
# ramp=True (calibration) or ramp=False (tracking). The ramp itself acts
# as a rate-limiter, so the "right" Kp for ramped operation (~0.05) is
# very different from the right value for un-ramped operation (~0.017).
# tracker.update() calls with ramp=False, so the values below assume
# un-ramped tracking. If you ever revert to ramped tracking, Kp must
# come back up.
KP_PAN: float = 0.017
KI_PAN: float = 0.0
# Kd amplifies frame-to-frame detector centroid jitter into bracket
# motion. P-only is sufficient for the slow-moving targets this project
# handles.
KD_PAN: float = 0.0

KP_TILT: float = 0.017
KI_TILT: float = 0.0
KD_TILT: float = 0.0

# Maximum correction in degrees per PID update. Since tracking calls servos
# with ramp=False (immediate motion), a 20° single-frame jump would be jarring
# and could overload the LM2596 with current spikes. 10° caps per-frame swing
# at a more reasonable amount; the DS3225's mechanical slew rate (~1°/12 ms)
# means even 10° takes ~120 ms to physically complete, so the next frame's
# correction picks up from a more recent state.
PID_OUTPUT_LIMIT: float = 10.0

# When the target's pixel error is within this distance of frame center on
# BOTH axes, the tracker holds position instead of issuing tiny corrections.
# Prevents jiggle from detector centroid jitter — in practice the LifeCam +
# blue plastic bag combination jitters ~8-12 px frame-to-frame, so 15 catches
# the centroid solidly. Matches FIRE_PIXEL_THRESHOLD so the fire-when-centered
# logic in Phase 8 will trigger exactly when the tracker is in its hold state.
TRACKING_DEADBAND_PX: int = 15

# ---- Coast mode (Phase 5 extension) ---------------------------------------
# When the detector loses the target mid-track (e.g. user moves it faster
# than the bracket can keep up and it leaves the FOV), continue applying
# the LAST PID correction for a short window so the bracket keeps moving
# in the same direction and might re-acquire. Without this, the bracket
# would freeze the instant detection fails and never catch a fast target.
#
# Only coasts if the last correction was non-trivial (above
# COAST_MIN_CORRECTION_DEG). If the target was stationary in the deadband
# and then disappeared, holding position is correct — coasting in some
# stale direction would be wrong.

# How many frames to coast before giving up. ~1 second at 30 fps.
COAST_MAX_FRAMES: int = 30

# Multiplicative decay applied to the coast correction each frame.
# 0.95 means after 30 frames the correction is ~22% of its starting value,
# so the bracket eases to a stop rather than slamming into a limit.
COAST_DECAY: float = 0.95

# Last correction must exceed this (degrees, absolute value on either axis)
# for coast mode to kick in. Below this threshold we treat the loss as
# "target was basically stationary, hold position."
COAST_MIN_CORRECTION_DEG: float = 0.1

# ---- Post-coast recenter (Phase 5 extension) ------------------------------
# After a coast window expires without re-acquiring the target — or after
# the bracket runs into a servo limit during coast — automatically ramp
# back to PAN_CENTER / TILT_CENTER. Without this, a fast diagonal target
# would leave the bracket parked in a corner staring at the wall with no
# hope of seeing the target again. The recenter is done non-blocking, a
# few degrees per frame, so a target reappearing mid-recenter is picked
# up immediately by normal tracking.

# Master enable. Set to False to keep the bracket wherever coast left it.
RECENTER_AFTER_COAST: bool = True

# Max degrees of motion per frame during recenter. Smaller = smoother but
# slower return; larger = faster but more visible step motion. 2° at 30 fps
# gives ~60°/sec recenter speed — full PAN range (170°) recovered in ~3 s.
RECENTER_STEP_DEG: float = 2.0

# ---- Laser firing (Phase 8) -----------------------------------------------
# How long the laser stays ON per fire command in main.py. The original
# spec was 0.5s — too short to be visually clear in a demo. 2.5s is long
# enough for an audience to see the dot land, register that it hit the
# target, and follow what just happened, without being so long that it
# stresses the GPIO pin (laser module is ~10-15 mA, well within the
# pin's safe sourcing limit even for sustained on-time).
LASER_FIRE_DURATION_S: float = 2.5

# Lockout after each fire — prevents trigger-spam during the demo. Long
# enough that audience sees state transitions clearly, short enough that
# you can take a follow-up shot without losing the moment.
LASER_COOLDOWN_S: float = 1.0

# Widened deadband available to tracker.update() via deadband_override.
# Was used during laser FIRING/COOLDOWN to absorb auto-exposure jitter,
# but with AE disabled in camera.init() (see CAMERA_EXPOSURE below) the
# jitter is gone and we don't actually need this anymore. Kept as a
# tuning knob — if AE control turns out to be unreliable on a future
# camera, main.py can opt back in.
FIRE_DEADBAND_PX: int = 40

# ---- Camera exposure ------------------------------------------------------
# The LifeCam HD-3000's auto-exposure reacts to the laser dot when it
# appears in the frame — it drops the overall gain, which dims the blue
# target's pixel values and shifts the HSV-detected centroid by 10-30 px
# from frame to frame. That AE-driven jitter is what made the bracket
# "dance" during firing. Solution: disable AE entirely and set a fixed
# exposure value. With a stable image, the target's HSV signature stays
# put, the centroid stops jittering, and normal-tight tracking works
# even while the laser is on.
#
# V4L2/uvcvideo backend convention for CAP_PROP_AUTO_EXPOSURE:
#   1 = manual mode  (the value we want)
#   3 = aperture priority / auto
#
# CAMERA_EXPOSURE is the V4L2 "exposure_absolute" value. The LifeCam
# HD-3000 typically accepts 5-2047. Lower = darker / faster shutter,
# higher = brighter / slower. 250 is a reasonable starting point for
# normal indoor room lighting; tune empirically:
#   - if the image looks too dark, raise it (try 400-600)
#   - if too bright / blown out, lower it (try 100-150)
# After changing the exposure significantly, re-run tune_detector.py
# because the target's HSV signature shifts with exposure.
CAMERA_DISABLE_AUTO_EXPOSURE: bool = True
CAMERA_EXPOSURE: int = 250

# ---- Boresight offsets (Phase 7B) -----------------------------------------
# Pixel delta between the camera's frame center (320, 240) and the actual
# point where the laser dot lands. Camera and laser are physically offset
# on the tilt plate by a few centimeters — at ~1.5m target distance this
# translates to a pixel offset that the tracker needs to compensate for.
#
# Without compensation: target is centered in camera → laser misses by the
# camera-to-laser offset projected onto the target plane.
# With compensation: tracker biases the PID setpoint by these values so the
# laser ends up on the target, not the camera's exact aim.
#
# Sign convention: positive dx means the laser dot is RIGHT of the camera
# center (in pixel space). Positive dy means the laser dot is BELOW center.
# Measured + written automatically by calibrate_boresight.py. The values
# below are placeholders (0, 0) — re-run the calibrator after mounting the
# laser to get the real numbers. Recorded in docs/calibration.md.
BORESIGHT_X_OFFSET: int = 0
BORESIGHT_Y_OFFSET: int = 0
