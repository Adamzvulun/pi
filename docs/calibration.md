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

## HSV target range — not yet measured

Will be filled in during Task 4.4 (tune_detector.py).

## PID gains — not yet tuned

Will be filled in during Task 5.4.

## Boresight offset — not yet measured

Will be filled in during Task 7.4 (boresight.py).
