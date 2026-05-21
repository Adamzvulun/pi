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

## PID gains — not yet tuned

Will be filled in during Task 5.4.

## Boresight offset — not yet measured

Will be filled in during Task 7.4 (boresight.py).
