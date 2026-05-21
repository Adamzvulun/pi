# Changelog

## [Phase 5 — PID tracking scaffolding] - 2026-05-22

### Code added
- `tracker.py` — owner module for PID control. Public API `init() → (pan_pid, tilt_pid)`, `update(pan_pid, tilt_pid, kit, target_pos)` (per-frame call; holds position when target is None), `stop(kit)`. Two independent `simple_pid.PID` instances with `setpoint=0` and `output_limits=(-PID_OUTPUT_LIMIT, +PID_OUTPUT_LIMIT)`. The ONLY module that uses `simple_pid`.
- `test_tracking.py` — Phase 5 end-to-end loop test (camera → detector → tracker → servos, no laser). OpenCV window shows red frame-center crosshair, green target circle, and overlay with per-axis pan/tilt angles + pixel error + correction. `q` quits cleanly; `finally` block guarantees servo center + camera release.

### config.py
- Added `KP_PAN`, `KI_PAN`, `KD_PAN`, `KP_TILT`, `KI_TILT`, `KD_TILT` (placeholders: 0.05 / 0 / 0.01). Documented that Kp sign may need flipping depending on servo mounting orientation.
- Added `PID_OUTPUT_LIMIT = 20.0` — caps degrees per update per axis to prevent large single-frame swings on far-edge targets.

### Docs
- `docs/plan/phase-5-pid-tracking.md` rewritten as a step-by-step runbook (mount camera on tilt plate temporarily, sign-check Kp, tune P → D → I, record gains). Reference sections at bottom describe what's built.
- `docs/plan/README.md`, `CLAUDE.md` reflect Phase 5 in-progress.

### Still to do
- Temporarily attach LifeCam HD-3000 to the tilt plate (tape / zip-tie / rubber band — Phase 7B's permanent mount comes later).
- VNC into Pi, run `python3 test_tracking.py`, sign-check by holding target right/below center.
- Tune Kp, then Kd, then Ki (if needed). Document final values in `docs/calibration.md`.

---

## [Phase 4 — Camera + detection] - 2026-05-22

### Hardware
- **USB webcam path adopted.** Pi 5 CSI camera on hand remains incompatible with the Pi 4's 15-pin CSI slot. Plugged a Microsoft LifeCam HD-3000 (USB ID `045e:0779`) into the Pi instead. Recognized by the in-kernel `uvcvideo` driver — no install needed. `lsusb`, `/dev/video0`, and `cv2.VideoCapture(0).read()` all verified at 640×480 BGR.

### Code added
- `camera.py` — owner module for the camera subsystem. Public API `init/capture_frame/release` against `cv2.VideoCapture`. Same shape as the original picamera2 plan so downstream code doesn't care which backend is used.
- `config.py` — shared tuned constants. Frame geometry, placeholder `HSV_LOWER`/`HSV_UPPER`, `MIN_CONTOUR_AREA=200`, `FIRE_PIXEL_THRESHOLD=15`.
- `detector.py` — owner module for target detection. Public `detect(frame) -> (x,y) | None` and `build_mask(frame)`. Pipeline: blur → BGR→HSV → inRange → erode×2 → dilate×2 → findContours → largest → centroid via moments.
- `tune_detector.py` — interactive HSV slider GUI. Three windows (controls + feed + mask), six trackbars, `s` prints copy-pasteable values, `q` quits. Mirrors `detector.build_mask()`'s pipeline exactly so the preview matches runtime behavior.

### Docs updated
- `docs/plan/README.md` — Phase 4 from BLOCKED to IN PROGRESS.
- `docs/plan/phase-4-camera.md` — rewritten Status section; Tasks 4.1, 4.2, 4.4, 4.5, 4.6 marked done; tuning procedure flagged as the only remaining work in this phase.
- `README.md`, `CLAUDE.md` — camera entry updated (LifeCam HD-3000 USB, `cv2.VideoCapture`, `picamera2` retained as installed-but-unused).

### Phase 4 completed
- Tuned HSV range against a folded 10×20 cm blue plastic bag under overhead ceiling lighting via `tune_detector.py` on the Pi: `HSV_LOWER = np.array([79, 76, 0])`, `HSV_UPPER = np.array([105, 255, 255])`.
- Committed those values to `config.py`.
- Recorded values, target description, lighting, and smoke-test result in `docs/calibration.md`.
- Smoke-tested `detector.detect()` on the Pi: returned `(385, 288)` with target in frame (inside 640×480 bounds).
- Updated `docs/plan/phase-4-camera.md` from runbook → completion record (runbook preserved for future re-tuning).

---

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
