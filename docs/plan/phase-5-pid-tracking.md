# Phase 5 — PID Closed-Loop Tracking ⏸ FUTURE

## Prerequisites

- Phase 4 complete: `camera.py` and `detector.py` working, target detection reliable
- Phase 3 complete: `servo.py` with calibrated limits ✅

## Goal

Close the loop. Given pixel coordinates of a target from the detector, drive the pan and tilt servos to keep the target centered in the frame. Build `tracker.py` as the PID controller and a `test_tracking.py` standalone test that runs the full loop minus the laser.

---

## Task 5.1 — Understand the tracking math

Camera frame is 640×480 pixels. Center = (320, 240). When target is centered, servos hold position.

**Error** = distance from target to frame center:
- `pan_error = target_x - 320` (positive = target to the right)
- `tilt_error = target_y - 240` (positive = target below center)

A PID controller takes the error and outputs a correction (in degrees). For pan: target 50 pixels to the right → PID outputs +N degrees → new pan angle = current + N → moves bracket right → next frame, error is smaller. Loop converges.

**Proportional gain (Kp)** is the main knob. Higher Kp = bigger correction per pixel of error = faster but riskier (overshoot, oscillation). Lower Kp = slower but stable.

**Wide-angle lens caveat:** the Pi 5 camera in the original parts list was a 220° fisheye. Edge distortion meant pixel-error → angle-correction mapping was nonlinear near the edges. Any replacement camera may be narrower; if so, gains may need rescaling. Keep targets near center anyway — the PID will do this naturally.

---

## Task 5.2 — Write tracker.py

**Public API:**
- `init() → (pan_pid, tilt_pid)` — creates two `simple_pid.PID` instances with initial gains, setpoint 0 (zero error), output limits (-20°, +20°) per update
- `update(pan_pid, tilt_pid, kit, target_pos)` — main per-frame call:
  - If `target_pos is None`, hold position (don't update)
  - Else compute pan_error and tilt_error
  - Run `pan_pid(pan_error)` → correction
  - New pan angle = `servo.current_pan() + correction`, pass to `servo.move_pan(kit, new_angle)` (which clamps)
  - Same for tilt
- `stop(kit)` — calls `servo.cleanup(kit)`

**Initial gains:**
```python
Kp = 0.05   # gentle start
Ki = 0.0    # disable integral initially
Kd = 0.01   # small damping
```

**Output limits:** `(-20, 20)` degrees per update. Prevents huge jumps if the target suddenly appears at frame edge.

---

## Task 5.3 — Write test_tracking.py

Standalone tracking test — full loop minus laser. Used for PID tuning.

**Behavior:**
1. Init camera, servos (calls `servo.init()` which centers), PIDs
2. Loop:
   - Capture frame
   - `detector.detect(frame)` → target position
   - `tracker.update(...)`
   - Optionally save annotated frame for debugging (target marker overlay)
   - Check for `q` keypress → break
3. On exit: `servo.cleanup(kit)`, `camera.release(cam)`

**Run:**
```bash
python3 test_tracking.py
```

Move target slowly in front of camera → bracket follows.

---

## Task 5.4 — Tune the PID gains

Iterate. No shortcut. Run, observe, adjust, repeat.

**P-only first** (Ki=0, Kd=0):
- Too slow → double Kp
- Oscillates → halve Kp
- Goal: responsive but not oscillating

**Then add D** (~Kp × 0.1):
- Reduces overshoot, stabilizes
- Too much → sluggish, ignores fast movements

**Then I if needed** (start at 0.001):
- Use only if there's a persistent offset (target settles slightly off-center forever)
- Too much → slow oscillation that grows over time (integral windup)

Record final gains in `config.py` and `docs/calibration.md`.

---

## Open questions / known unknowns

- **Gains depend on camera frame rate.** Initial values assume ~30 fps at 640×480. If the replacement camera runs at a different rate, gains may need rescaling.
- **Servo movement latency** (the time from `move_pan` call to bracket actually being at the new angle) interacts with the PID. The 2°-step ramping inside `servo.py` adds latency that the PID will adapt to.
- **Frame-to-frame target detection jitter** can confuse the D term. May need a low-pass filter on detector output if jitter is bad.

## Acceptance criteria

- `test_tracking.py` runs without errors
- Slowly moving target → bracket follows smoothly
- Target held stationary in center → error converges to near zero, servos stop
- Final PID gains recorded in `config.py` and `docs/calibration.md`
- No oscillation, no runaway tracking, no servo clamp warnings during normal use
