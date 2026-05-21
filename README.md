# Laser Tracker

An autonomous laser tracking system running on a Raspberry Pi 4B. A camera detects a target, computes its pixel coordinates, and drives two servos (pan and tilt) via PID control to keep the target centered. On user confirmation, a 5mW laser fires at the target.

This is Adam's school final project.

## Where to start

**For Claude Code sessions:** read [`CLAUDE.md`](CLAUDE.md) first, then [`docs/plan/README.md`](docs/plan/README.md) for the current phase status.

**For humans:** [`docs/plan/README.md`](docs/plan/README.md) shows phase status at a glance. [`docs/operating-guide.md`](docs/operating-guide.md) has every command and procedure we use.

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi 4B (8GB) | Hostname: `LaserPi`, user: `adam` |
| Camera | Microsoft LifeCam HD-3000 USB webcam (640×480 BGR via `cv2.VideoCapture`). Pi 5 CSI camera on hand is incompatible with Pi 4's 15-pin CSI slot and stays shelved. |
| Servos | 2× DS3225 digital servo, 270° range |
| PWM driver | PCA9685 16-channel, I2C address 0x40 |
| Servo power | LM2596 buck converter (5.0V regulated) fed by 12V 5A PSU |
| Pi power | USB-C 5V 3A adapter (separate rail from servos) |
| Laser driver | IRLZ44N MOSFET + 220Ω gate + 100kΩ pulldown + 100Ω current limiter |
| Laser | 5mW 650nm red bare diode (no PCB), cross-pattern lens |

See [`docs/wiring.md`](docs/wiring.md) for the current physical wiring, [`docs/circuit-diagram.md`](docs/circuit-diagram.md) for visual diagrams, and [`problems/001-servo-power.md`](problems/001-servo-power.md) for why the MB102 was dropped in favor of the LM2596.

## Current state

Phase 3 (servo control) and Phase 4 (camera + detection) are complete — `detector.detect()` returns `(x, y)` pixel coordinates of a blue target captured from the LifeCam HD-3000. Phase 5 (PID tracking) is next. Phase 6 (laser integration) is parallel-actionable — MOSFET driver circuit to be rebuilt on the breadboard.

Calibrated values are in [`docs/calibration.md`](docs/calibration.md). Working servo angle limits: `PAN_MIN=50, PAN_MAX=220, TILT_MIN=115, TILT_MAX=205`.

## How to run

SSH to the Pi, then:

```bash
cd ~/pi
source venv/bin/activate
python3 <script>.py
```

`main.py` is still a placeholder — final tracking loop is built in [Phase 8](docs/plan/phase-8-integration.md). For Phase-by-phase testing scripts (`test_servo.py`, `calibrate_servo.py`, etc.), see [`docs/operating-guide.md`](docs/operating-guide.md).

The auto-pull cron job on the Pi keeps the code in sync with GitHub — just push from the laptop and wait up to 60 seconds.
