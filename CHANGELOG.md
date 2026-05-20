# Changelog

## [Phase 3 — Servo bring-up] - 2026-05-20

### Hardware
- **Problem 001 resolved.** MB102 confirmed insufficient for DS3225 servo current (700mA regulator ceiling vs 600–900mA tracking load + 2A+ stall spikes).
- Switched servo power to **LM2596 buck converter** fed by the 12V 5A PSU, output set to 5.0V via trimpot.
- **MB102 removed from the circuit.** Pi GPIO 5V (pin 2) now supplies PCA9685 VCC directly.
- Breadboard temporarily taken out for the servo-only test rig; will return for the laser MOSFET circuit later.
- **Pan-tilt bracket reassembled**: prior manual gear rotation had left electrical center misaligned with physical center by ~170° on pan. Both servos were driven to electrical 135° and held while the brackets/horns were remounted at visual center → electrical center now = physical center on both axes.

### Code added
- `test_servo.py` — Phase 3 sanity check. Drives both DS3225 channels (configured for 500–2500 µs pulse, 270° actuation), takes user-estimated starting angles, sends initial pulse, then runs a small ±10° pan sweep. Verified end-to-end on the Pi.
- `calibrate_servo.py` — interactive REPL-style limit finder. User issues `+5` / `-5` / `=N` / `step N` / `s` (mark) / `done` / `q`. Ramps every move in 2° increments with 50ms sleeps to keep current draw smooth and avoid jerk. Output is `PAN_MIN/MAX` and `TILT_MIN/MAX` for `servo.py` (Task 3.4).

### Docs added
- `problems/` folder — convention: one Markdown file per problem encountered, with diagrams and a fix plan.
- `problems/001-servo-power.md` — root cause, LM2596 fix, full wiring procedure, voltage-setting safety steps.
- `docs/circuit-diagram.md` — Mermaid diagrams covering the full system (power distribution, I2C path, servo connections, laser MOSFET, mechanical layout).

### Docs updated
- `docs/wiring.md` — current rig (Pi → PCA direct, LM2596 → V+, no MB102 in the circuit).
- `CLAUDE.md` — hardware constraints table (LM2596, Pi-VCC direct) and current project state.
- `docs/project-plan.md` — "Where we are right now" reflects post-Phase-3.2/3.3 state.

### Edge calibration results
- `PAN_MIN = 50.0`, `PAN_MAX = 220.0` (170° of pan travel, centered at 135°)
- `TILT_MIN = 115.0`, `TILT_MAX = 205.0` (90° of tilt travel, centered at 160° — asymmetric due to spline mesh granularity)
- Full record in `docs/calibration.md`.

### Task 3.4 — servo.py
- `servo.py` written as the single owner module for ServoKit/PCA9685.
- Public API: `init()`, `move_pan(kit, angle)`, `move_tilt(kit, angle)`, `center(kit)`, `cleanup(kit)`, `current_pan()`, `current_tilt()`.
- All `move_*` calls clamped to the calibrated limits — this is the single safety enforcement against hard stops.
- Module-level state tracks last commanded angle for each servo so subsequent moves can ramp smoothly (PCA9685 has no position readback).

### Phase 3 status
✅ Complete. Next session begins Phase 4 (camera + target detection).

## [Setup] - 2026-05-20

- Initialized project skeleton (README, .gitignore, requirements.txt, CLAUDE.md, docs/)
- Set up three-machine workflow: laptop edits → GitHub → Pi auto-pulls
