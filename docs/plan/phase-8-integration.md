# Phase 8 — Final Integration ⏸ FUTURE

## Prerequisites

- All previous phases complete (3 ✅, 4, 5, 6, 7)
- `servo.py`, `camera.py`, `detector.py`, `tracker.py`, `laser.py`, `config.py` all working in isolation

## Goal

Replace the placeholder `main.py` with the real tracking + firing loop. Run end-to-end, polish documentation, demo-ready.

---

## Task 8.1 — Write the full main.py

**Pseudocode:**

```
Initialize logging
servo.init() → kit (centers servos)
camera.init() → cam
tracker.init() → (pan_pid, tilt_pid)
laser.init() → laser_dev (OFF)

Print:
  'f' = fire laser at current target
  'q' = quit

Main loop:
  1. frame = camera.capture_frame(cam)
  2. target = detector.detect(frame)
  3. If target found:
       tracker.update(pan_pid, tilt_pid, kit, target)
       (optional) draw target marker on frame
  4. If 'f' pressed AND target is centered (pixel error < 15 in both axes):
       log("Firing")
       laser.fire(laser_dev)
       sleep(0.5)
       laser.off(laser_dev)
  5. If 'q' pressed: break

On exit (finally):
  laser.off(laser_dev)
  servo.cleanup(kit)
  camera.release(cam)
  log("Shutdown complete")
```

**The "centered" check before firing** is critical safety. Only fire when pixel error is below threshold (e.g., 15 pixels in both axes after applying boresight offset). Prevents firing at a fast-moving or partially-out-of-frame target.

---

## Task 8.2 — End-to-end test

```bash
source ~/pi/venv/bin/activate
python3 main.py
```

**Test sequence:**
1. No target visible → servos hold, laser OFF
2. Bring target into frame → servos start tracking
3. Move target slowly → servos follow
4. Hold target still in center → error drops near zero, servos stop
5. Press `f` → laser fires 0.5 s, turns off
6. Press `q` → clean shutdown, servos center, laser confirmed OFF in log

---

## Task 8.3 — Polish documentation

**Update `CHANGELOG.md`** with the integration entry.

**Update `README.md`** so "How to run" describes what `main.py` actually does (not "placeholder").

**Verify `docs/calibration.md`** has all four sections filled in:
- Servo angle limits ✅ (Phase 3)
- HSV range (Phase 4)
- PID gains (Phase 5)
- Boresight offset (Phase 7)

**Verify cross-references** in CLAUDE.md, `docs/operating-guide.md`, `docs/wiring.md` still accurate.

---

## Acceptance criteria

- `python3 main.py` runs without errors
- Tracking + firing produces a laser dot on the target on demand
- Clean shutdown on `q` — servos centered, laser off, camera released, no GPIO warnings
- All documentation reflects final state
- Demo-ready

## Final file map at completion

```
pi/
├── main.py                  ✅ full tracking loop
├── servo.py                 ✅ ServoKit owner module
├── camera.py                ⏸ picamera2 (or cv2.VideoCapture) wrapper
├── detector.py              ⏸ HSV blob detection
├── tracker.py               ⏸ PID loop
├── laser.py                 ⏸ GPIO18 laser control
├── config.py                ⏸ tuned constants (HSV, PID, boresight)
├── test_servo.py            ✅ kept for debugging
├── calibrate_servo.py       ✅ kept for recalibration
├── tune_detector.py         ⏸ HSV tuning GUI
├── test_tracking.py         ⏸ tracking without laser
├── test_laser.py            ⏸ laser test
├── boresight.py             ⏸ camera-laser offset calibration
├── requirements.txt         ✅
├── CLAUDE.md                ✅
├── CHANGELOG.md             ✅
├── HANDOFF.md               ✅
├── README.md                ✅
├── docs/
│   ├── setup-pi.md          ✅
│   ├── wiring.md            ✅
│   ├── operating-guide.md   ✅
│   ├── circuit-diagram.md   ✅
│   ├── calibration.md       ✅
│   ├── parts.docx           ✅
│   └── plan/
│       ├── README.md        ✅
│       ├── phase-1-foundation.md      ✅
│       ├── phase-2-hardware.md        ✅
│       ├── phase-3-servo-control.md   ✅
│       ├── phase-4-camera.md          ✅
│       ├── phase-5-pid-tracking.md    ✅
│       ├── phase-6-laser.md           ✅
│       ├── phase-7-mounting.md        ✅
│       └── phase-8-integration.md     ✅ (this file)
└── problems/
    └── 001-servo-power.md   ✅
```

✅ = exists at end of Phase 3 (current state). ⏸ = remains to be built.
