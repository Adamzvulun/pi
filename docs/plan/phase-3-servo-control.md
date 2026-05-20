# Phase 3 — Servo Control ✅ COMPLETE

## Goal

Drive both DS3225 servos accurately and safely from Python over I2C → PCA9685, with software-enforced angle limits matching the bracket's physical range. Build a reusable owner module (`servo.py`) that the rest of the project will import for all servo access.

## What we built

Three Python files:

| File | Role |
|------|------|
| `test_servo.py` | Sanity check — verify Pi → I2C → PCA9685 → DS3225 chain with a small ±10° pan sweep |
| `calibrate_servo.py` | Interactive REPL — find safe bracket limits, drive servos to specific angles for assembly work |
| `servo.py` | Owner module — the only file in the project that imports `adafruit_servokit` |

Plus calibration record + operating documentation:
- `docs/calibration.md` — recorded servo angle limits
- `docs/operating-guide.md` — practical commands and procedures
- `problems/001-servo-power.md` — the MB102 power story

## Decisions made and why

**No auto-center on startup or on Ctrl+C in the test/calibrate scripts.** "Center" might be past a hard stop if the bracket limits aren't known yet. Snapping into an unknown position can damage gears. The user pre-positions the bracket manually and provides an eyeball-estimated starting angle. `servo.py`'s `init()` does auto-center because by that point the limits are calibrated and safe.

**User-provided estimates as the starting reference.** The PCA9685 has no position readback — there's no way to ask "where is the servo right now?" So we accept the user's eyeball estimate. First-command motion is then small if the estimate is accurate, large if not (caller has Ctrl+C ready).

**Relative `+5` / `-5` commands rather than absolute angle entry** in `calibrate_servo.py`. Safer by default — a typo in a relative move stays small. An absolute-angle typo could swing the bracket far.

**All moves ramp in 2° steps with 50ms sleeps.** Smooth motion, lower peak current draw, easier on the gearbox. A ~60° move takes ~1.5 seconds — fine for calibration, fine later for tracking too (PID corrections are small per-frame).

**`=N` absolute-jump command** added to `calibrate_servo.py` for the bracket reassembly procedure. When we discovered electrical center didn't match physical center on pan, we needed to hold servos at a known angle while remounting horns. The `=135` command does that with smooth ramping.

**`PAN_CENTER` and `TILT_CENTER` computed from limits, not hardcoded to 135°.** After bracket reassembly, tilt ended up asymmetric (115–205, midpoint 160°) because of spline mesh granularity. The midpoint-of-range approach handles this automatically — all code uses `PAN_CENTER = (PAN_MIN + PAN_MAX) / 2`.

**Module-level state in `servo.py` for last-commanded angles.** Needed for ramping (`_ramp` requires a starting angle). Set on every `move_pan` / `move_tilt` call, returned by `current_pan()` / `current_tilt()`.

## Issues encountered

### Problem 001 — MB102 underpowered

Mid-phase, the MB102 power supply was identified as the bottleneck. Resolution: LM2596 buck converter for servo V+, Pi GPIO 5V for PCA9685 VCC, MB102 dropped entirely. See [`problems/001-servo-power.md`](../../problems/001-servo-power.md).

### Bracket reassembly — electrical center ≠ physical center

The pan servo's electrical 135° (the "logical" center) was about 170° away from the bracket's visual center. Cause: pre-assembly manual gear rotation had decoupled the servo's potentiometer from the bracket position. Software re-centering couldn't compensate because the mismatch exceeded the servo's 270° electrical range.

Resolution: drove both servos to electrical 135° via `calibrate_servo.py` (`=135` + `s` + `s` + `done`), then physically unscrewed both horns, manually rotated the bracket arms to visual center, and remounted the horns at the new orientation. Spline mesh forced ~5° of asymmetry on tilt; that's why `TILT_CENTER = 160°` rather than 135°. Procedure documented in [`docs/operating-guide.md`](../operating-guide.md).

## Files created / changed

| Path | Status |
|------|--------|
| `test_servo.py` | New |
| `calibrate_servo.py` | New |
| `servo.py` | New |
| `docs/calibration.md` | New |
| `docs/operating-guide.md` | New |
| `docs/circuit-diagram.md` | New (Mermaid system diagrams) |
| `docs/wiring.md` | Rewritten — current rig (no MB102, no breadboard) |
| `problems/001-servo-power.md` | New |
| `CLAUDE.md` | Updated — hardware constraints reflect LM2596 |
| `CHANGELOG.md` | New entry for Phase 3 |

## Final state / outputs

**Calibrated angle limits** (in `servo.py` and [`docs/calibration.md`](../calibration.md)):
- `PAN_MIN = 50.0`, `PAN_MAX = 220.0` → 170° of usable travel, centered at 135°
- `TILT_MIN = 115.0`, `TILT_MAX = 205.0` → 90° of usable travel, centered at 160°

**`servo.py` public API:**
- `init() → ServoKit`
- `move_pan(kit, angle) → float` (clamped, returns actual angle)
- `move_tilt(kit, angle) → float` (clamped)
- `center(kit)`
- `cleanup(kit)`
- `current_pan() → Optional[float]`
- `current_tilt() → Optional[float]`

All `move_*` calls clamp to the calibrated limits. This is the single safety enforcement preventing hard-stop damage. No other file in the project may import `adafruit_servokit` directly.

## Operating procedures

For commands and how-to-run, see [`docs/operating-guide.md`](../operating-guide.md). It covers:
- Daily workflow (laptop edit → push → Pi pull → run)
- `i2cdetect` sanity check
- Running `test_servo.py` and `calibrate_servo.py` with the actual command reference
- Edge calibration procedure (the steps that produce the four numbers)
- Bracket reassembly procedure (when electrical center is misaligned)
- Servo behavior gotchas (no readback, spline granularity, snap-on-init)
- LM2596 voltage setup
- Troubleshooting
