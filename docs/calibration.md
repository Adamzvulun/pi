# Calibration Record

This file is the source of truth for tuned/calibrated values measured
on the actual hardware. If anything is recalibrated, update both the
relevant code constant AND the entry below (with a new date).

---

## Servo angle limits — 2026-05-20

Measured with `calibrate_servo.py` after the pan-tilt bracket was
reassembled with both servos held at electrical 135°. Limits represent
the safe physical range of the bracket including a ~5° safety margin
backed off from the strain point on each end.

| Constant   | Value | Notes |
|------------|-------|-------|
| `PAN_MIN`  | 50.0  | Hard stop / cable strain begins ~45° |
| `PAN_MAX`  | 220.0 | Hard stop / cable strain begins ~225° |
| `TILT_MIN` | 115.0 | Downward travel limit |
| `TILT_MAX` | 205.0 | Upward travel limit |
| `PAN_CENTER`  | 135.0 | computed: (50 + 220) / 2 |
| `TILT_CENTER` | 160.0 | computed: (115 + 205) / 2 — asymmetric due to spline mesh |

**Range:** pan = 170° of travel, tilt = 90° of travel.

These values are hardcoded in `servo.py`. Any code that calls
`servo.move_pan()` or `servo.move_tilt()` is automatically clamped to
this range — the clamp is the single safety enforcement preventing the
bracket from being driven into a hard stop.

If the bracket is ever disassembled and remounted, these numbers will
likely change — rerun `calibrate_servo.py` and update both `servo.py`
and this file.

---

## HSV target range — 2026-05-22

Measured with `tune_detector.py` on the Microsoft LifeCam HD-3000 USB webcam.

| Constant     | Value                              |
|--------------|------------------------------------|
| `HSV_LOWER`  | `np.array([79, 76, 0])`            |
| `HSV_UPPER`  | `np.array([105, 255, 255])`        |

**Range covered:** Hue 79–105 (blue band in OpenCV's 0–179 hue space), Saturation 76–255 (floor drops greys / washed-out background), Value 0–255 (full brightness range — no V floor or ceiling needed under this lighting).

**Target object:** folded 10×20 cm blue plastic bag.

**Lighting:** overhead ceiling lighting only (no direct daylight, no desk lamp).

**Smoke-test result:** `detector.detect()` returned `(385, 288)` with the target held in front of the camera — a sensible coordinate inside the 640×480 frame.

Values live in `config.py`. If the target object, lighting, or camera position changes, rerun `tune_detector.py` and update both files.

## PID gains — 2026-05-23

Tuned with `test_tracking.py` on the Pi. Camera (LifeCam HD-3000) 3D-printed-mounted to the tilt plate. Target was the same folded 10×20 cm blue plastic bag used for the HSV calibration above, under overhead ceiling lighting.

| Constant                | Value | Notes |
|-------------------------|-------|-------|
| `KP_PAN` / `KP_TILT`    | 0.017 | Final tuned value |
| `KI_PAN` / `KI_TILT`    | 0.0   | Not needed — P-only is sufficient |
| `KD_PAN` / `KD_TILT`    | 0.0   | Removed — Kd amplified detector centroid jitter |
| `PID_OUTPUT_LIMIT`      | 10.0  | Degrees per axis per update; caps single-frame swing |
| `TRACKING_DEADBAND_PX`  | 15    | Hold position when both axis errors within this many pixels |

**Tuning history (so the rationale survives future sessions):**

| Setting               | Outcome |
|-----------------------|---------|
| Kp = 0.05, Kd = 0.01 (placeholders), `servo.move_*` ramped 2°/50 ms | Tracking "worked" but bracket jiggled on a stationary target. Ramp was the real rate-limiter — masking that Kp was hot. |
| Added a deadband (8 px), kept ramping | Jiggle persisted because detector centroid bounced ±10 px in/out of the 8 px window. |
| Disabled ramping in `tracker.update()` (added `ramp=False` to `servo.move_pan`/`move_tilt`); deadband → 15; Kd → 0 | Camera lag (250 ms/correction) disappeared, but Kp = 0.05 now caused bracket to oscillate between calibrated limits — once the ramp throttle was gone, the PID was actually getting the snap it requested. |
| Kp → 0.01, output limit → 10° | Stable, smooth, but slow to react to fast-moving targets. |
| Kp → 0.02 | Slightly jittery. |
| **Kp → 0.017** | Sweet spot — fast enough to follow, calm enough on a stationary target. |

**Why these values are right for THIS setup:** Kp depends on camera frame rate, lens degrees-per-pixel, and the speed of typical target motion. If any of those change (faster camera, narrower FOV lens, faster targets), retune. The deadband and Kd choices are more universal — Kd = 0 should hold for any detector-noise-dominated setup, and the deadband should always be ≥ the detector centroid's frame-to-frame jitter range.

Values live in `config.py`. Any retune updates both files.

## Boresight offset — 2026-05-27

| Constant              | Value |
|-----------------------|-------|
| `BORESIGHT_X_OFFSET`  | 0     |
| `BORESIGHT_Y_OFFSET`  | 0     |

**How alignment was achieved:** the laser module is taped on top of the
camera lens with the laser's emission axis manually aligned to the
camera's optical axis. With both pointing in the same direction and
mounted ~1 cm apart vertically, the laser dot lands at the camera's
frame center on a target ~1.5 m away. No software compensation needed.

**`calibrate_boresight.py` was built but the measured offsets are zero**
because physical alignment was good enough. The tool is documented in
`docs/plan/phase-7-mounting.md` and remains available — if the laser
mount ever drifts or is rebuilt, run it (Boresight calibration… button
in the control panel) at the operating distance, and the resulting
offsets will be written to `config.py` automatically.

**`tracker.py` does NOT currently apply the boresight offsets** — the
addition of `BORESIGHT_X_OFFSET / Y_OFFSET` to the pixel error was
removed once Adam confirmed physical alignment was tight. The values
exist in `config.py` as a future hook; re-introducing them is a one-
line change in `tracker.update()` if compensation is ever needed.

## Camera exposure (locked) — 2026-05-27

| Constant                      | Value |
|-------------------------------|-------|
| `CAMERA_DISABLE_AUTO_EXPOSURE`| True  |
| `CAMERA_EXPOSURE`             | 250   |

The LifeCam HD-3000's auto-exposure was disabled because it caused the
HSV detector centroid to jitter ~10–30 px between frames whenever the
laser fired — the AE reduced overall gain in response to the bright
laser dot, which dimmed the blue target and shifted its detected
position. The bracket "danced" chasing the phantom motion.

With AE off and exposure locked, the image stays stable during firing,
the detector centroid is rock-solid, and normal 15 px deadband
tracking works while the laser is on.

**Value 250** is V4L2's `exposure_absolute` unit (LifeCam range 5–2047).
Tuned for normal indoor room lighting. If the room is moved or the
lighting changes substantially:
- Image too dark → raise to 400–600
- Image too bright → lower to 100–150
- After significant change, re-run `tune_detector.py` to re-tune the
  HSV range against the new exposure.

Values live in `config.py`.
