# Changelog

## [Phase 5 — Closed-loop PID tracking complete] - 2026-05-23

### Achievement
The full vision-to-motion loop runs end-to-end. Camera (on 3D-printed tilt mount) → detector → PID → servos. The bracket smoothly tracks a slow-moving blue plastic bag, holds still on a stationary target (deadband locks the loop), recovers gracefully from sudden target moves, and shows no oscillation or runaway behavior.

### Final tuned values
- `KP_PAN` = `KP_TILT` = **0.017** (P-only response).
- `KI_PAN` = `KI_TILT` = 0.
- `KD_PAN` = `KD_TILT` = 0. (Kd kept amplifying detector centroid jitter; removed entirely.)
- `PID_OUTPUT_LIMIT` = **10.0°** per axis per update.
- `TRACKING_DEADBAND_PX` = **15** (matches `FIRE_PIXEL_THRESHOLD` so Phase 8 fire-when-centered will trigger inside the deadband).

### Key learnings
- **`servo.py`'s 50 ms/2° ramp was a loop bottleneck.** Added a `ramp=False` parameter so `tracker.update()` can issue immediate PWM commands without the per-correction sleep stalling camera capture. `init()` and `cleanup()` still ramp.
- **The "right" Kp depends entirely on whether ramping is on.** With ramping, the ramp itself acts as a rate-limiter, masking that 0.05 is too hot. Without ramping, 0.05 oscillates wildly between calibrated limits. 5× cut to 0.01 stabilized it; bumped back up to 0.017 for responsiveness after empirical testing.
- **Detector centroid jitter is ~10 px** with this camera/target/lighting. The deadband had to be 15 px to catch it solidly.
- **The "forgot to plug in 12V" failure mode bit us once.** Added a pre-flight checklist to the runbook so it doesn't happen again.

### Docs
- `docs/calibration.md` gets a full PID gains section with tuning history.
- `docs/plan/phase-5-pid-tracking.md` rewritten from runbook to completion record. The tuning steps are preserved as a re-tuning runbook for future use.
- `docs/plan/README.md`, `CLAUDE.md`, `README.md` updated.
- `config.py`'s PID comments explain the ramp-vs-Kp relationship so future sessions don't relearn it.

---

## [Phase 5 unblocked — camera mounted] - 2026-05-23

### Hardware
- **3D-printed camera mount installed.** The LifeCam HD-3000 is now rigidly attached to the tilt plate. This unblocks the Phase 5 closed-loop test — the camera view shifts with the bracket so PID has real feedback to work with.

### Docs
- `docs/plan/README.md` — Phase 5 flipped back to in-progress, Phase 6 to paused. The "Currently working on" section rewritten accordingly.
- `docs/plan/phase-5-pid-tracking.md` — Step 1 (camera mount) marked done; runbook Step 2 rewritten as a pre-flight checklist (12V PSU on, latest code on Pi, VNC ready) so the "forgot to plug in 12V" failure mode doesn't bite a second time. Duplicate Step 3 from the prior edit cleaned up.
- `docs/plan/phase-6-laser.md` — status changed to ⏸ PAUSED with a note that the runbook remains valid for whenever it resumes.
- `CLAUDE.md` — current-state bullets flipped.

### No code changes this entry
Tracker code and the Phase 6 laser scaffolding were already pushed in earlier commits. This is purely a status/docs update to reflect that Phase 5 is now actionable.

---

## [Phase 6 — Laser scaffolding] - 2026-05-22

### Code added
- `laser.py` — owner module for the laser on GPIO18. Public API `init/fire/off/cleanup`. The only file that imports `gpiozero` for the laser pin. Variable holding the device must be named `laser_dev` (using `laser` shadows the module and breaks subsequent `laser.cleanup` calls — CLAUDE.md flags this).
- `test_laser.py` — Phase 6 standalone test: init → 3-2-1 countdown → fire 1.0s → off → cleanup. Wrapped in try/finally so Ctrl+C or an exception still turns the laser off.

### Docs
- `docs/plan/phase-6-laser.md` rewritten as a step-by-step runbook covering safety, parts inventory, MOSFET driver build, multimeter pre-power check, laser attach, and the test. Reference sections at the bottom describe what's built.
- `docs/plan/README.md`, `CLAUDE.md` updated — Phase 5 paused (blocked on camera mount), Phase 6 actively in progress.

### Context — why the pivot
Phase 5 code shipped, but tuning is blocked: the LifeCam HD-3000 can't be secured to the tilt plate well enough for the closed-loop to make sense (camera wobble breaks the feedback). Switched focus to Phase 6 because it's independent of the camera mount and uses already-defined hardware (resistors picked, polarity confirmed). Phase 5 resumes when a workable mount exists or Phase 7B lands.

### Still to do for Phase 6
- Rebuild MOSFET driver on breadboard (IRLZ44N + 220Ω gate + 100kΩ pulldown + 100Ω laser limiter).
- Wire Pi pins 4 (5V), 12 (GPIO18), 14 (GND) to the breadboard.
- Multimeter pre-check: red rail ~5V, gate to GND ~0V (pulldown working).
- Attach bare diode (red=+, black=−).
- Power-up sanity check: laser must be OFF before any script runs.
- Run `python3 test_laser.py`, confirm 1-second dot on a matte wall.

---

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
