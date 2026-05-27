# Laser Tracker

An autonomous laser tracking system running on a Raspberry Pi 4B. A camera detects a target, computes its pixel coordinates, and drives two servos (pan and tilt) via PID control to keep the target centered. On user confirmation, a 3 V red laser fires at the target.

This is Adam's school final project.

## Status — demo-ready

All eight phases (foundation → hardware → servos → camera → PID tracking → laser → mounting → integration) are complete. The full vision-to-action loop runs end-to-end from a single button in the operator GUI. Tested on the actual hardware 2026-05-27.

## Where to start

**For Claude Code sessions:** read [`CLAUDE.md`](CLAUDE.md) first, then [`latest-changesV1.md`](latest-changesV1.md) for the previous session's deltas and non-obvious decisions.

**For humans:** [`docs/operating-guide.md`](docs/operating-guide.md) has every command and procedure used to run the system day-to-day.

## Hardware

| Component | Details |
|---|---|
| Raspberry Pi 4B (8GB) | Hostname: `LaserPi`, user: `adam` |
| Camera | Microsoft LifeCam HD-3000 USB webcam (640×480 BGR via `cv2.VideoCapture`). Auto-exposure disabled, fixed exposure value 250. |
| Servos | 2× DS3225 digital servo, 270° range |
| PWM driver | PCA9685 16-channel, I2C address 0x40 |
| Servo power | LM2596 buck converter (5.0 V regulated) fed by 12 V 5 A PSU |
| Pi power | USB-C 5 V 3 A adapter (separate rail from servos) |
| Laser | 3 V self-contained laser module (small brass cylinder with internal driver) — direct-driven from GPIO18. No MOSFET, no external resistors. See [`problems/002-laser-dead.md`](problems/002-laser-dead.md) for why the original MOSFET-driven bare diode plan was abandoned. |

See [`CLAUDE.md`](CLAUDE.md) for the full wiring snapshot.

## How to run

The intended path: launch the operator GUI from the Pi's desktop shortcut over VNC.

```bash
# One-time setup (creates the desktop icon):
bash ~/pi/scripts/install_desktop_shortcut.sh
```

Then double-click the "Laser Tracker" icon on the Pi's desktop. Inside the GUI:

1. **Initialize hardware** — centers servos, claims GPIO18 for the laser
2. **Enable laser controls** — ticks the safety checkbox so fire-related buttons go live
3. **▶ RUN FULL DEMO** — launches `main.py`, the full tracking + firing demo

Inside the demo window: `A` to arm the laser, target acquires a green "LOCKED" banner when centered, `F` to fire (2.5 s burst), `Q` to quit.

Other useful buttons in the GUI: tracking-only test (`test_tracking.py`), HSV detector tuner (`tune_detector.py`), servo recalibration (`calibrate_servo.py`), boresight calibration (`calibrate_boresight.py`), single-pulse laser test, manual servo sliders, emergency stop.

### Running scripts directly (rarely needed)

```bash
ssh adam@LaserPi.local
cd ~/pi && source venv/bin/activate
python3 main.py             # full demo
python3 test_laser.py       # 1-second laser pulse
python3 test_tracking.py    # tracking without firing
```

### Workflow

Code is edited on the laptop, pushed to GitHub. The Pi pulls every minute via cron — push from the laptop and wait up to 60 seconds. Code is never edited directly on the Pi.
