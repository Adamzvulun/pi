# CLAUDE.md — Laser Tracker Project Context

This file is read by Claude Code at the start of every session to understand the project. Read it before writing any code.

## What this project is

Autonomous laser tracking system on a Raspberry Pi 4B. Camera detects a target, two servos (pan + tilt) keep it centered via PID control, then a 5mW laser fires on user confirmation.

## Target environment

- Hardware: Raspberry Pi 4B (8GB), hostname `LaserPi`, user `adam`
- OS: Raspberry Pi OS 64-bit (Bookworm)
- Python: 3.11
- Working directory on Pi: `~/pi`

## Three-machine workflow

1. Edit code on the laptop (`C:\Projects\pi`) using Claude Code
2. `git push` to GitHub (private repo `pi`)
3. Pi auto-pulls from GitHub every minute via cron
4. SSH to Pi → `source venv/bin/activate` → `python3 main.py`

Code is NEVER edited directly on the Pi.

## Libraries

**In requirements.txt (pip-installed into venv):**
- `adafruit-circuitpython-pca9685` — low-level PCA9685 driver
- `adafruit-circuitpython-servokit` — high-level servo control
- `adafruit-blinka` — CircuitPython compatibility layer for Pi

**apt-installed (system packages, NOT in requirements.txt):**
- `picamera2` — camera capture
- `python3-opencv` / `cv2` — image processing
- `python3-numpy` / `numpy` — array math

**GPIO:**
- Prefer `gpiozero` for simple digital I/O
- Use `RPi.GPIO` only if low-level timing is needed

## Hardware constraints

| Item | Detail |
|---|---|
| I2C bus | Bus 1 (GPIO2=SDA, GPIO3=SCL) |
| PCA9685 address | 0x40 (default) |
| Servo frequency | 50 Hz |
| DS3225 pulse range | 500–2500 µs |
| DS3225 neutral | 1500 µs (≈ center of 270° range) |
| Channel 0 | Pan servo (left-right, bottom of bracket) |
| Channel 1 | Tilt servo (up-down, top of bracket) |
| Laser GPIO | GPIO18, active HIGH |
| Laser gate resistor | 220Ω between GPIO18 and MOSFET gate |
| Laser pulldown | 100kΩ gate-to-GND |
| Servo supply voltage | 5V from MB102 rail (spec is 4.8–6.8V; running at lower end — may brown out under load) |

## Safety rules (always follow these)

- Software-enforced angle limits on both servos — never command past mechanical stops
- Laser is OFF by default when any script starts
- Laser must be turned OFF on script exit — use `try/finally` or a signal handler
- Every script must handle `KeyboardInterrupt` cleanly (don't let it leave the laser on)

## Coding style

- **Comments:** Comment generously. Adam is learning. Explain WHY, not just what.
- **Type hints:** Use them where they aid clarity (function signatures, return types)
- **Function size:** Prefer small, focused functions over large ones
- **Logging:** Use the `logging` module, not `print()`, for runtime output
- **Python version:** Python 3 only — no Python 2 compatibility shims
- **Error handling:** Handle hardware errors gracefully (I2C failures, servo brownout)
